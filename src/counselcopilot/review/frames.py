"""Obligation frames (design §3.1 clause parser, §4 T4, §6).

Each obligation in an NDA clause becomes a frame
``{party, action, object, condition, duration, exception}`` plus the clause type it belongs to.
Numbers and conditions are then compared exactly (``duration=24 months`` against a rule's
``>= 36``), not by text similarity, which sees "2 years" and "3 years" as near-identical.

Frames come from the fine-tuned 8B model once it exists (finetune/), from a prompted backbone
until then (`extract_frames`), or from a small rule-based parser (`regex_frames`) that needs no
model and is the fallback for unreadable replies. `fields_from_frames` turns frames into the
field values field rules check, so the policy reviewer can read fields from frames (the main
system) or from per-field questions (`review/fields.py`, the "no frames" ablation).

The same frames score repairs (§5.3): a repaired clause restores the gold obligation when its
frame matches the original clause's frame field by field (`frame_match`).
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from ..data.draft import Draft
from ..llm import LLMClient, PendingBatch, system, user
from ..policy.jurisdictions import normalise_jurisdiction
from .fields import _duration

CLAUSE_TYPES = (
    "definition", "confidentiality_term", "survival", "return_or_destroy", "non_solicit", "non_compete",
    "governing_law", "dispute_forum", "permitted_disclosure", "use_restriction", "residuals", "remedies",
    "compelled_disclosure", "no_license", "other",
)
FRAME_FIELDS = ("party", "action", "object", "condition", "duration", "exception")

FRAME_SCHEMA = {
    "type": "object",
    "properties": {"frames": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "segment": {"type": "integer"},
            "clause_type": {"type": "string", "enum": list(CLAUSE_TYPES)},
            "party": {"type": "string"}, "action": {"type": "string"}, "object": {"type": "string"},
            "condition": {"type": "string"}, "duration": {"type": "string"}, "exception": {"type": "string"},
        },
        "required": ["segment", "clause_type", "party", "action", "object", "condition", "duration", "exception"],
    }}},
    "required": ["frames"],
}

FRAME_SYSTEM = f"""You turn NDA clauses into obligation frames. For every obligation, permission or prohibition in the numbered SEGMENTS, write one frame:
- segment: the segment number;
- clause_type: one of {", ".join(CLAUSE_TYPES)};
- party: who is bound or allowed ("receiving party", "disclosing party", "each party", "employee");
- action: what they must, may or must not do, as a short verb phrase ("not disclose", "return or destroy", "not solicit");
- object: what the action is about ("confidential information", "employees of the other party");
- condition: when it applies ("upon request", "upon termination"), or "";
- duration: how long, exactly as written ("five (5) years", "perpetual", "30 days"), or "";
- exception: any carve-out ("except as required by law"), or "".
For governing_law and dispute_forum clauses, put the place in object ("delaware", "england").
Segments with no obligation get no frame. Use only the text shown.
Reply with JSON {{"frames": [...]}}."""


@dataclass
class ObligationFrame:
    segment: int
    clause_type: str = "other"
    party: str = ""
    action: str = ""
    object: str = ""
    condition: str = ""
    duration: str = ""
    exception: str = ""
    source: str = "model"  # "model" | "regex"

    @property
    def months(self) -> float | None:
        return _duration(self.duration, "months") if self.duration else None

    @property
    def days(self) -> float | None:
        return _duration(self.duration, "days") if self.duration else None

    def as_dict(self) -> dict:
        return asdict(self)


def _clean(frames_json, shown: set[int]) -> list[ObligationFrame]:
    out = []
    for f in (frames_json or {}).get("frames", []) if isinstance(frames_json, dict) else []:
        if not isinstance(f, dict) or not isinstance(f.get("segment"), (int, float)) or int(f["segment"]) not in shown:
            continue
        ct = f.get("clause_type") if f.get("clause_type") in CLAUSE_TYPES else "other"
        out.append(ObligationFrame(int(f["segment"]), ct, **{k: str(f.get(k) or "").strip() for k in FRAME_FIELDS}))
    return out


def extract_frames(llm: LLMClient, draft: Draft, ids: list[int] | None = None, batch: int = 12,
                   tag: str = "frames", fallback: bool = True) -> list[ObligationFrame]:
    """Frames for the segments `ids` (default: all), `batch` segments per call. A batch whose reply
    is unreadable falls back to the rule-based parser so a review never loses its fields."""
    ids = list(range(len(draft.segments))) if ids is None else list(ids)
    out: list[ObligationFrame] = []
    chunks = [ids[i:i + batch] for i in range(0, len(ids), batch)]

    def one(chunk: list[int]) -> list[ObligationFrame]:
        try:
            got = llm.complete_json([system(FRAME_SYSTEM), user(f"SEGMENTS:\n{draft.numbered(chunk)}")],
                                    FRAME_SCHEMA, max_tokens=90 * len(chunk) + 100, tag=tag)
            frames = _clean(got, set(chunk))
        except PendingBatch:
            raise
        except Exception:
            frames = []
        if not frames and fallback:
            frames = regex_frames(draft, chunk)
        return frames

    for fs in llm.map(one, chunks, max_workers=4):
        out.extend(fs or [])
    return sorted(out, key=lambda f: f.segment)


# ---------------------------------------------------------------- rule-based parser

_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("governing_law", re.compile(r"govern\w*\s+(?:by|in accordance with)|laws?\s+of\s+the\s+state", re.I)),
    ("dispute_forum", re.compile(r"\b(?:courts?|venue|arbitrat\w*|jurisdiction)\b", re.I)),
    ("non_compete", re.compile(r"\bcompet(?:e|ing|ition)\b", re.I)),
    ("non_solicit", re.compile(r"\bsolicit\w*|\bhire\b", re.I)),
    ("residuals", re.compile(r"residual|unaided memory", re.I)),
    ("return_or_destroy", re.compile(r"\breturn\b.*\bdestroy|\bdestroy\b.*\breturn|\breturn\b[^.]*confidential", re.I)),
    ("survival", re.compile(r"\bsurviv\w*", re.I)),
    ("confidentiality_term", re.compile(r"(?:period|term)\s+of\b|\bfor\s+(?:a\s+period\s+of\s+)?[a-z]+\s*\(\d+\)\s*(?:years?|months?)|"
                                        r"(?:years?|months?)\s+(?:from|after|following)", re.I)),
    ("compelled_disclosure", re.compile(r"required by (?:law|court|subpoena)|compelled", re.I)),
    ("no_license", re.compile(r"\blicen[cs]e\b|\bno right\b", re.I)),
    ("remedies", re.compile(r"injunct\w*|equitable relief|specific performance", re.I)),
    ("definition", re.compile(r"\bmeans\b|\bshall include\b|\bincludes?\b.*\binformation\b", re.I)),
]
_DUR = re.compile(r"(?:(?:[a-z]+(?:-[a-z]+)?\s*)?\(\d+\)|\d+|(?:one|two|three|four|five|six|seven|eight|nine|ten|twelve|"
                  r"eighteen|twenty-four|thirty|sixty|ninety))\s*(?:calendar\s+|business\s+)?(?:years?|months?|days?)|"
                  r"perpetu\w*|indefinite\w*", re.I)
_PARTY = re.compile(r"\b(receiving party|recipient|disclosing party|discloser|each party|either party|"
                    r"neither party|employee|consultant|contractor|the parties)\b", re.I)
_EXC = re.compile(r"\b(?:except|unless|provided that|other than|save that)\b[^.;]*", re.I)
_COND = re.compile(r"\b(?:upon|on|after|following|within)\s+(?:the\s+)?(?:written\s+)?"
                   r"(request|termination|expiration|expiry|completion|demand)[^,.;]*", re.I)
_PLACE = re.compile(r"laws?\s+(?:in force\s+)?(?:of|in)\s+(?:the\s+)?(?:(?i:state|commonwealth)\s+of\s+)?"
                    r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)")
_COURT = re.compile(r"courts?\s+(?:located\s+)?(?:of|in)\s+(?:the\s+)?(?:(?i:state)\s+of\s+)?([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?)")


def clause_type(text: str) -> str:
    for name, pat in _PATTERNS:
        if pat.search(text):
            return name
    return "other"


def regex_frames(draft: Draft, ids: list[int] | None = None) -> list[ObligationFrame]:
    """A frame for each segment whose clause type the patterns recognise. Coarse but deterministic;
    it is the no-model fallback and the baseline the tuned frame model is compared with."""
    ids = range(len(draft.segments)) if ids is None else ids
    out = []
    for i in ids:
        t = draft.segments[i]
        ct = clause_type(t)
        if ct == "other":
            continue
        party = (_PARTY.search(t).group(1).lower() if _PARTY.search(t) else "")
        dur = _DUR.search(t)
        obj = ""
        if ct == "governing_law" and _PLACE.search(t):
            obj = _PLACE.search(t).group(1)
        elif ct == "dispute_forum" and _COURT.search(t):
            obj = _COURT.search(t).group(1)
        elif "confidential information" in t.lower():
            obj = "confidential information"
        out.append(ObligationFrame(
            i, ct, party, "", obj, (_COND.search(t).group(0) if _COND.search(t) else ""),
            dur.group(0) if dur and ct not in ("governing_law", "dispute_forum") else "",
            _EXC.search(t).group(0)[:160] if _EXC.search(t) else "", source="regex"))
    return out


# ---------------------------------------------------------------- frames -> field values

def fields_from_frames(frames: list[ObligationFrame]) -> dict[str, tuple]:
    """{field: (value, evidence)} for the field rules (policy/schema.py FieldConstraint). A field no
    frame states is left out (the caller decides whether that means absent or ask again)."""
    out: dict[str, tuple] = {}

    def put(name, value, seg):
        if value is not None and name not in out:
            out[name] = (value, [seg])

    for f in frames:
        if f.clause_type == "confidentiality_term" and f.months is not None:
            put("confidentiality_term_months", f.months, f.segment)
        elif f.clause_type == "survival" and f.months is not None:
            put("survival_months", f.months, f.segment)
        elif f.clause_type == "return_or_destroy" and f.days is not None:
            put("return_deadline_days", f.days, f.segment)
        elif f.clause_type == "non_solicit" and f.months is not None:
            put("non_solicit_months", f.months, f.segment)
        elif f.clause_type == "non_compete":
            put("non_compete", True, f.segment)
        elif f.clause_type == "governing_law" and f.object:
            put("governing_law", normalise_jurisdiction(f.object), f.segment)
        elif f.clause_type == "dispute_forum" and f.object:
            put("dispute_forum", normalise_jurisdiction(f.object), f.segment)
    return out


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower())).strip()


def frame_match(gold: ObligationFrame, pred: ObligationFrame) -> dict[str, bool]:
    """Field-by-field agreement. Durations compare as numbers of months; text fields match when
    one normalised string contains the other (wording varies, the obligation does not)."""
    out = {"clause_type": gold.clause_type == pred.clause_type}
    for k in FRAME_FIELDS:
        g, p = getattr(gold, k), getattr(pred, k)
        if k == "duration":
            out[k] = (gold.months == pred.months) if (g or p) else True
        else:
            gn, pn = _norm(g), _norm(p)
            out[k] = gn == pn or (bool(gn) and bool(pn) and (gn in pn or pn in gn))
    return out


@dataclass
class FrameScores:
    n_gold: int = 0
    n_matched: int = 0  # gold frames with a predicted frame on the same segment
    field_correct: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        acc = {k: round(v / self.n_gold, 4) if self.n_gold else 0.0 for k, v in self.field_correct.items()}
        return {"n_gold": self.n_gold, "segment_recall": round(self.n_matched / self.n_gold, 4) if self.n_gold else 0.0,
                "field_accuracy": acc,
                "mean_field_accuracy": round(sum(acc.values()) / len(acc), 4) if acc else 0.0}


def frame_field_accuracy(gold: list[ObligationFrame], pred: list[ObligationFrame]) -> dict:
    """Proposal §5 fine-tuning metric: frame field accuracy on gold frames. Each gold frame is
    paired with the best predicted frame on the same segment; a missing frame gets every field wrong."""
    s = FrameScores(field_correct={k: 0 for k in ("clause_type", *FRAME_FIELDS)})
    by_seg: dict[int, list[ObligationFrame]] = {}
    for p in pred:
        by_seg.setdefault(p.segment, []).append(p)
    for g in gold:
        s.n_gold += 1
        cands = by_seg.get(g.segment, [])
        if not cands:
            continue
        s.n_matched += 1
        best = max((frame_match(g, p) for p in cands), key=lambda m: sum(m.values()))
        for k, ok in best.items():
            s.field_correct[k] += ok
    return s.as_dict()
