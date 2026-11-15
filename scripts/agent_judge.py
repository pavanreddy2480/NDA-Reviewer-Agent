"""Claude agents as the RQ2 judge: compact task files, one per repaired NDA, grouped by repair system.

`cc batch export` writes every queued request whole, so a judge agent would read the same 100-segment
NDA once per rule. This script groups a judge queue by the NDA each question is about: a task file shows
the NDA once and then lists the questions (rule terms and field questions). The agent writes one
JSON answer file per task. `collect` turns those into the {"key", "text"} lines `cc batch load` reads.

    python scripts/agent_judge.py export --queue data/rq2_judge/q.claude-haiku-agent.jsonl \
        --repaired run_logs/rq2/repaired_drafts.jsonl --out data/rq2_judge/round1
    (one agent per group folder answers every tasks/*.md into answers/<task>.json)
    python scripts/agent_judge.py collect --out data/rq2_judge/round1
    cc batch load --backend claude-haiku-agent --queue data/rq2_judge/q.claude-haiku-agent.jsonl \
        --answers data/rq2_judge/round1/answers_jsonl

Groups: `original` (the unrepaired planted NDAs, shared by every system) and one per repair system.
A question about a draft that is neither a saved original nor a saved repaired NDA (a redline applied
alone, for regression attribution, or an earlier round's draft) goes to the system whose saved draft it
is closest to, and is shown as a change list against that draft.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

from counselcopilot.data.draft import Draft, Edit

SEG = re.compile(r"^\[(\d+)\] (.*)$")

INSTRUCTIONS = """You are the independent judge for a contract-repair experiment. Answer every question below on your
own reading of the NDA text in this file. Do not use tools other than reading this file and writing the answer file.

Two kinds of question:

TERM questions. You are auditing a revised contract for a senior lawyer. Read the whole NDA and decide whether it
contains the CONTRACT TERM. Answer "Entailment" if the NDA contains the term (in any wording), "Contradiction" if it
says something incompatible with it, and "NotMentioned" if it does not deal with it. Exceptions and carve-outs count.
Cite segment numbers as evidence. Give your probability of being right as confidence, and a one-sentence rationale.
Answer: {"rationale": "...", "label": "Entailment|Contradiction|NotMentioned", "evidence": [ints], "confidence": 0-1}

FIELD questions. You extract facts from NDAs. Use only the numbered segments given with that question.
Answer: {"value": <as the question asks: a number, null, "blank" or "unspecified">, "evidence": [ints]}

Write ONE JSON object to the answer file: {"Q1": {...}, "Q2": {...}, ...} with every question id. Valid JSON only."""


def split_term(user: str) -> tuple[str, list[str]] | None:
    if not user.startswith("CONTRACT TERM: ") or "\n\nNDA:\n" not in user:
        return None
    term, nda = user[len("CONTRACT TERM: "):].split("\n\nNDA:\n", 1)
    segs = []
    for line in nda.split("\n"):
        m = SEG.match(line)
        if m and int(m.group(1)) == len(segs):
            segs.append(m.group(2))
        elif segs:  # a segment with a line break inside
            segs[-1] += "\n" + line
    return term, segs


def numbered(segs: list[str]) -> str:
    return "\n".join(f"[{i}] {s}" for i, s in enumerate(segs))


def changes(base: list[str], other: list[str]) -> str:
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=base, b=other, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        if op == "delete":
            out.append(f"- segments [{i1}]..[{i2 - 1}] of the base are deleted")
        elif op == "insert":
            out.append(f"- after base segment [{i1 - 1}] insert:\n" + "\n".join(f"    {t}" for t in other[j1:j2]))
        else:
            out.append(f"- base segments [{i1}]..[{i2 - 1}] are replaced by:\n" + "\n".join(f"    {t}" for t in other[j1:j2]))
    return "\n".join(out) or "- (no change)"


def cached_keys(cache_path: str) -> set[str]:
    if not Path(cache_path).exists():
        return set()
    with sqlite3.connect(cache_path) as c:
        try:
            return {r[0] for r in c.execute("SELECT key FROM responses")}
        except sqlite3.OperationalError:
            return set()


def export(args) -> None:
    known: dict[tuple, tuple[str, str]] = {}  # segments -> (group, task)
    attrib: dict[tuple, tuple[str, str, tuple]] = {}  # single-redline draft -> (group, task, its base)
    for line in Path(args.repaired).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        known.setdefault(tuple(r["original"]), ("original", f"original_doc{r['doc_id']}"))
        known.setdefault(tuple(r["repaired"]), (r["system"], f"{r['system']}_doc{r['doc_id']}"))
        # each round's draft and each single redline on it (the judge's regression attribution checks)
        base = Draft(str(r["doc_id"]), list(r["original"]))
        for k in range(1, r["rounds"] + 1):
            edits = [Edit(e["op"], e["segment"], e.get("text", ""), e.get("fixes", "")) for e in r["edits"]
                     if e["round"] == k]
            for e in edits:
                attrib.setdefault(tuple(base.apply([e]).segments),
                                  (r["system"], f"{r['system']}_doc{r['doc_id']}_round{k}", tuple(base.segments)))
            base = base.apply(edits)
    done = cached_keys(args.cache)
    tasks: dict[str, dict] = defaultdict(lambda: {"group": None, "base": None, "variants": {}, "q": []})
    for line in Path(args.queue).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item["key"] in done:
            continue
        msgs = item["request"]["messages"]
        user = next(m["content"] for m in msgs if m["role"] == "user")
        st = split_term(user)
        if st is None:  # field question: self-contained, filed under the task of the NDA it quotes
            segs_q = [(int(m.group(1)), m.group(2)) for m in map(SEG.match, user.split("\n")) if m]
            hits = [v for k, v in known.items() if segs_q and all(i < len(k) and k[i] == t for i, t in segs_q)]
            hits += [v[:2] for k, v in attrib.items() if segs_q and all(i < len(k) and k[i] == t for i, t in segs_q)]
            hit = hits[0] if hits else ("fields", "fields")
            tasks[hit[1]]["group"] = hit[0]
            tasks[hit[1]]["q"].append(("field", user, None, item["key"]))
            continue
        term, segs = st
        hit = known.get(tuple(segs))
        if hit is None and tuple(segs) in attrib:
            g, name, b = attrib[tuple(segs)]
            hit, base = (g, name), list(b)
        elif hit is None:  # some other draft: nearest saved draft, or its own task if none is close
            best = max(known, key=lambda k: difflib.SequenceMatcher(a=k, b=segs, autojunk=False).ratio())
            if difflib.SequenceMatcher(a=best, b=segs, autojunk=False).ratio() >= 0.8:
                hit, base = known[best], list(best)
            else:  # an unrelated NDA (e.g. ContractNLI validation)
                tag = hashlib.sha256("\n".join(segs).encode()).hexdigest()[:8]
                known[tuple(segs)] = hit = ("validation", f"nda_{tag}")
                base = segs
        else:
            base = segs
        t = tasks[hit[1]]
        t["group"], t["base"] = hit[0], base
        vid = None
        if segs != base:
            key = tuple(segs)
            if key not in t["variants"]:
                t["variants"][key] = f"V{len(t['variants']) + 1}"
            vid = t["variants"][key]
        t["q"].append(("term", term, vid, item["key"]))
    out = Path(args.out)
    summary = defaultdict(list)
    for name, t in sorted(tasks.items()):
        if not t["q"]:
            continue
        name = name.lstrip("_")
        d = out / t["group"]
        (d / "tasks").mkdir(parents=True, exist_ok=True)
        (d / "answers").mkdir(parents=True, exist_ok=True)
        parts = [f"# Judge task {name}\n", INSTRUCTIONS, ""]
        if t["base"] is not None:
            parts += ["## NDA (base text)", "", numbered(t["base"]), ""]
        for segs, vid in t["variants"].items():
            parts += [f"## NDA {vid}: the base NDA with these changes (renumber nothing: cite base numbers, "
                      "or describe inserted text as 'new')", "", changes(t["base"], list(segs)), ""]
        parts += ["## Questions", ""]
        keymap = {}
        for k, (kind, text, vid, key) in enumerate(t["q"], 1):
            qid = f"Q{k}"
            keymap[qid] = key
            if kind == "term":
                on = f"NDA {vid}" if vid else "the base NDA"
                parts.append(f"{qid} [TERM, about {on}] CONTRACT TERM: {text}\n")
            else:
                parts.append(f"{qid} [FIELD]\n{text}\n")
        (d / "tasks" / f"{name}.md").write_text("\n".join(parts), encoding="utf-8")
        (d / "tasks" / f"{name}.keys.json").write_text(json.dumps(keymap, indent=0))
        summary[t["group"]].append({"task": name, "questions": len(t["q"]), "variants": len(t["variants"])})
    print(json.dumps(summary, indent=1))


def collect(args) -> None:
    out = Path(args.out)
    dest = out / "answers_jsonl"
    dest.mkdir(exist_ok=True)
    report = {}
    for keys in sorted(out.glob("*/tasks/*.keys.json")):
        name = keys.name[:-len(".keys.json")]
        group = keys.parent.parent
        keymap = json.loads(keys.read_text())
        ans_file = group / "answers" / f"{name}.json"
        if not ans_file.exists():
            report[name] = "no answer file"
            continue
        try:
            ans = json.loads(ans_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            report[name] = f"bad JSON: {e}"
            continue
        lines = [json.dumps({"key": keymap[q], "text": json.dumps(a)}) for q, a in ans.items() if q in keymap]
        (dest / f"{name}.jsonl").write_text("\n".join(lines) + "\n")
        report[name] = f"{len(lines)}/{len(keymap)}"
    print(json.dumps(report, indent=1))


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--queue", required=True)
    e.add_argument("--repaired", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--cache", default="data/cache/llm.sqlite", help="skip requests already answered")
    e.set_defaults(fn=export)
    c = sub.add_parser("collect")
    c.add_argument("--out", required=True)
    c.set_defaults(fn=collect)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
