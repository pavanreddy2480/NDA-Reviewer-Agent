"""A deterministic, offline stand-in for a model: `--backend heuristic`.

It answers every prompt the system sends with keyword and pattern rules, so the whole pipeline
(detection, baselines, repair loop, evaluator) runs end to end with no network, GPU or API key:
- rule checks: word overlap between the statement and each shown segment;
- field questions and frames: the rule-based frame parser (review/frames.py);
- deal facts, applicability, planner, verifier: fixed conservative answers;
- opposing counsel: pattern search for known loophole wordings, quoting the draft;
- repairer: insert the required term for an omission, delete a clause that breaks a rule;
- tool agents: the scripted steps of the approval clerk.

It is a plumbing check and a no-model reference point, not a result: numbers from it say the
code runs, never how well a model does. Every reply is cheap to compute, so it is not cached.
"""

from __future__ import annotations

import json
import re

from .backends import FakeClient
from .base import LLMRequest

_SEG = re.compile(r"^\[(-?\d+)\] (.*)$", re.M)
_PROB = re.compile(r"^- \[([^\]]+)\] (.*?)(?: \(segments \[([\d, ]*)\]\))?$", re.M)


def _segments(text: str) -> dict[int, str]:
    return {int(m.group(1)): m.group(2) for m in _SEG.finditer(text)}


def _overlap(statement: str, seg: str) -> float:
    from ..retrieval.index import tokenize

    s, t = set(tokenize(statement)), set(tokenize(seg))
    return len(s & t) / len(s) if s else 0.0


LOOPHOLE_PATTERNS = [
    ("residuals", re.compile(r"residual|unaided memory", re.I), "use of information retained in memory"),
    ("technical_only", re.compile(r"limited to technical information|shall not include business", re.I),
     "protection of business and financial information"),
    ("independent_development", re.compile(r"develop[^.]{0,80}similar[^.]{0,120}whether or not", re.I),
     "protection against use of ideas in competing products"),
    ("oral_excluded", re.compile(r"oral\w* (?:disclosures? )?(?:are|is|shall) not|only (?:information )?in writing", re.I),
     "protection of orally disclosed information"),
    ("retained_copies", re.compile(r"(?:may|entitled to) retain[^.]{0,80}cop(?:y|ies)", re.I),
     "complete return of information"),
]


class HeuristicClient(FakeClient):
    provider = "heuristic"

    def __init__(self, model: str = "heuristic", **kw):
        kw.pop("cache", None)
        super().__init__(self._respond, model=model, **kw)

    # ------------------------------------------------------------------ dispatch
    def _respond(self, req: LLMRequest) -> str:
        from ..agents.planner import PLAN_SYSTEM
        from ..baselines.systems import B1_SYSTEM, B2_SYSTEM
        from ..repair.attacker import ATTACK_SYSTEM
        from ..repair.repairer import CRITIQUE_SYSTEM, ONE_SHOT_SYSTEM, REPAIR_SYSTEM
        from ..review.applicability import APPLY_SYSTEM
        from ..review.checker import CHECK_SYSTEM
        from ..review.frames import FRAME_SYSTEM
        from ..review.verifier import VERIFY_SYSTEM

        sys_text, prompt = req.messages[0].content, req.messages[-1].content
        if sys_text == CHECK_SYSTEM or prompt.startswith("CONTRACT TERM:"):
            return self._check(prompt)
        if prompt.startswith("QUESTION:"):
            return self._field(prompt)
        if "personal data" in sys_text and "personal_data" in sys_text:
            segs = _segments(prompt)
            pd = any(re.search(r"personal (?:data|information)|personally identifiable|patient|health", s, re.I)
                     for s in segs.values())
            return json.dumps({"rationale": "keyword", "personal_data": pd, "evidence": []})
        if sys_text == APPLY_SYSTEM:
            ids = re.findall(r"^- ([A-Z]+(?:-[A-Za-z0-9]+)+): ", prompt, re.M)
            return json.dumps({"answers": [{"id": i, "applies": "unknown", "rationale": "heuristic"} for i in ids]})
        if sys_text == FRAME_SYSTEM:
            return self._frames(prompt)
        if sys_text == VERIFY_SYSTEM:
            return json.dumps({"rationale": "heuristic", "verdict": "supported", "confidence": 0.7})
        if sys_text == PLAN_SYSTEM:
            return json.dumps({"reviewers": ["policy", "law", "consistency"], "rationale": "run everything"})
        if sys_text == ATTACK_SYSTEM:
            return self._attack(prompt)
        if sys_text in (REPAIR_SYSTEM, ONE_SHOT_SYSTEM):
            return self._repair(prompt)
        if sys_text == CRITIQUE_SYSTEM:
            return json.dumps({"remaining": [], "done": True})
        if sys_text in (B1_SYSTEM, B2_SYSTEM):
            return json.dumps({"findings": []})
        if '"action"' in sys_text and "TOOLS:" in sys_text:
            return self._agent_step(req)
        if req.json_schema is not None:
            from .factory import schema_example

            return json.dumps(schema_example(req.json_schema))
        return "{}"

    # ------------------------------------------------------------------ answers
    def _check(self, prompt: str) -> str:
        term = re.search(r"(?:STATEMENT|CONTRACT TERM): (.*)", prompt).group(1).strip()
        segs = _segments(prompt)
        scored = sorted(((_overlap(term, s), i) for i, s in segs.items()), reverse=True)
        if scored and scored[0][0] >= 0.5:
            top = [i for sc, i in scored if sc >= scored[0][0] - 0.1][:3]
            return json.dumps({"rationale": "word overlap", "label": "Entailment", "evidence": top,
                               "confidence": round(min(0.95, scored[0][0]), 2)})
        conf = round(1 - (scored[0][0] if scored else 0.0), 2)
        return json.dumps({"rationale": "no segment states the term", "label": "NotMentioned", "evidence": [],
                           "confidence": conf})

    def _field(self, prompt: str) -> str:
        from ..data.draft import Draft
        from ..review.fields import FIELD_QUESTIONS
        from ..review.frames import fields_from_frames, regex_frames

        field = next((f for f, q in FIELD_QUESTIONS.items() if q in prompt), None)
        segs = _segments(prompt)
        ids = sorted(segs)
        if not ids or field is None:
            return json.dumps({"value": None, "evidence": []})
        draft = Draft("h", [segs.get(i, "") for i in range(max(ids) + 1)])
        got = fields_from_frames(regex_frames(draft, ids))
        if field in got:
            v, ev = got[field]
            return json.dumps({"value": v, "evidence": ev})
        return json.dumps({"value": None if field != "non_compete" else False, "evidence": []})

    def _frames(self, prompt: str) -> str:
        from ..data.draft import Draft
        from ..review.frames import FRAME_FIELDS, regex_frames

        segs = _segments(prompt)
        if not segs:
            return json.dumps({"frames": []})
        draft = Draft("h", [segs.get(i, "") for i in range(max(segs) + 1)])
        fr = regex_frames(draft, sorted(segs))
        return json.dumps({"frames": [{"segment": f.segment, "clause_type": f.clause_type,
                                       **{k: getattr(f, k) for k in FRAME_FIELDS}} for f in fr]})

    def _attack(self, prompt: str) -> str:
        segs = _segments(prompt.split("NDA:", 1)[-1])
        known = prompt.split("KNOWN SCENARIOS:", 1)[-1].split("NDA:", 1)[0]
        out = []
        for lt, pat, avoided in LOOPHOLE_PATTERNS:
            if f"- {lt}:" in known:
                continue
            for i, s in segs.items():
                m = pat.search(s)
                if m:
                    out.append({"obligation_avoided": avoided, "segments": [i], "quotes": [m.group(0)],
                                "how": "We rely on this wording.", "loophole_type": lt})
                    break
        return json.dumps({"scenarios": out})

    def _repair(self, prompt: str) -> str:
        head, _, nda = prompt.partition("\n\nNDA:\n")
        segs = _segments(nda)
        last = max(segs) if segs else -1
        edits, done = [], set()
        for m in _PROB.finditer(head):
            pid, desc, ev = m.group(1), m.group(2), m.group(3)
            ev_ids = [int(x) for x in ev.split(",") if x.strip()] if ev else []
            if desc.startswith("Missing required term"):
                term = desc.split("Term required/forbidden:", 1)[-1].strip() or desc
                edits.append({"op": "insert_after", "segment": last, "text": term, "fixes": pid})
            elif ev_ids:
                seg = ev_ids[0]
                if seg in done:
                    continue
                done.add(seg)
                edits.append({"op": "delete", "segment": seg, "text": "", "fixes": pid})
        return json.dumps({"edits": edits})

    def _agent_step(self, req: LLMRequest) -> str:
        task = req.messages[1].content
        results = [m.content for m in req.messages if m.role == "user" and m.content.startswith("RESULT of ")]
        rule = re.search(r"Rule: (\S+)", task)
        prov = re.search(r"Provision: (\S+)", task)
        if prov:
            if not results:
                return json.dumps({"thought": "look it up", "action": "statute_lookup",
                                   "args": {"provision_id": prov.group(1)}})
            return json.dumps({"thought": "done", "action": "finish", "args": {"decision": "confirmed", "summary": ""}})
        if not rule:  # B3 single agent: no scripted review, report nothing
            return json.dumps({"thought": "no findings", "action": "finish", "args": {"findings": []}})
        rid = rule.group(1)
        cp = (re.search(r"Counterparty type: (\S+)", task) or re.search(r"(vendor)", "vendor")).group(1)
        steps = [("rule_lookup", {"rule_id": rid}), ("approval_matrix_query", {"rule_id": rid}),
                 ("precedent_search", {"rule_id": rid, "counterparty": cp})]
        if len(results) < len(steps):
            name, args = steps[len(results)]
            return json.dumps({"thought": f"step {len(results) + 1}", "action": name, "args": args})
        prec = results[2] if len(results) > 2 else ""
        if len(results) == 3:
            if re.search(r"\(ok\): \[\s*\]", prec) or "(ok)" not in prec:
                return json.dumps({"thought": "no precedent", "action": "request_approval",
                                   "args": {"rule_id": rid, "reason": "Deviation from company rule needs sign-off."}})
            return json.dumps({"thought": "precedent", "action": "finish", "args": {"decision": "precedent"}})
        aid = re.search(r'"approval_id": "([^"]+)"', results[-1])
        return json.dumps({"thought": "filed", "action": "finish",
                           "args": {"decision": "requested", "approval_id": aid.group(1) if aid else ""}})
