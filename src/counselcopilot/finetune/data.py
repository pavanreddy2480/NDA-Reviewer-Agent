"""Training data for the one multi-task QLoRA model (proposal §5 fine-tuning row; design §6).

Three tasks share one Llama-3.1-8B-Instruct adapter, each with its own instruction, in chat
format (system / user / assistant), so the tuned model drops into the same prompts the pipeline
already sends:

1. ContractNLI checks on the 12 training hypotheses (the 5 held-out ones never appear). Input =
   the checker's exact prompt (review/checker.py) with the top-k retrieved spans; target = the
   checker's JSON with the gold label and the gold evidence spans that were shown.
2. CUAD clause-type tagging: a clause -> the CUAD categories it belongs to (41 types), for planner
   routing and dispute-risk patterns.
3. Obligation frames: the frame prompt (review/frames.py) -> silver frames written by Gemini Flash
   on train clauses (`cc frames silver`); 300 hand-checked frames are the gold test set.

`build_all` writes train.jsonl / val.jsonl plus a manifest with counts per task, so the data mix
is recorded with the adapter.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

from ..data.contractnli import HELD_OUT_HYPOTHESES, ContractNLI
from ..data.draft import Draft
from ..retrieval.index import HybridIndex, Passage
from ..review.checker import CHECK_SYSTEM
from ..review.frames import FRAME_SYSTEM

CUAD_SYSTEM = ("You tag contract clauses with CUAD clause types. Reply with JSON "
               '{"types": [list of CUAD category names, or empty if none applies]}.')


def chat(system_text: str, user_text: str, answer: dict | str, task: str) -> dict:
    return {"task": task, "messages": [
        {"role": "system", "content": system_text}, {"role": "user", "content": user_text},
        {"role": "assistant", "content": answer if isinstance(answer, str) else json.dumps(answer)}]}


def nli_examples(data: ContractNLI, split: str = "train", k: int = 12, limit: int | None = None,
                 seed: int = 0) -> list[dict]:
    hyps = [h for h in data.hypothesis_keys if h not in HELD_OUT_HYPOTHESES]
    out = []
    docs = data[split][:limit] if limit else data[split]
    for doc in docs:
        draft = Draft.from_nda(doc)
        index = HybridIndex([Passage(str(i), s) for i, s in enumerate(draft.segments)])
        for h in hyps:
            text = data.hypotheses[h].text
            a = doc.annotations[h]
            ids = set(int(x.passage.id) for x in index.search(text, k=k))
            ids |= set(a.spans)  # gold evidence is always shown in training, so the target is learnable
            ids = sorted(ids)
            ev = [i for i in a.spans if i in ids] if a.label.value != "NotMentioned" else []
            ans = {"rationale": f"The segments {'state' if a.label.value == 'Entailment' else 'contradict' if a.label.value == 'Contradiction' else 'do not address'} the term.",
                   "label": a.label.value, "evidence": ev, "confidence": 0.9}
            out.append(chat(CHECK_SYSTEM, f"STATEMENT: {text}\n\nSEGMENTS:\n{draft.numbered(ids)}", ans, "nli"))
    return out


# ------------------------------------------------------------------ CUAD

_CAT = re.compile(r'related to "([^"]+)"')


def load_cuad(path: str | Path) -> list[dict]:
    """CUAD_v1.json (SQuAD format) -> [{"title", "context", "labels": {category: [answer texts]}}]."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for d in raw["data"]:
        for p in d["paragraphs"]:
            labels: dict[str, list[str]] = {}
            for qa in p["qas"]:
                m = _CAT.search(qa["question"])
                cat = m.group(1) if m else qa["id"].split("__")[-1]
                texts = [a["text"] for a in qa.get("answers", []) if a.get("text")]
                if texts:
                    labels.setdefault(cat, []).extend(texts)
            out.append({"title": d.get("title", ""), "context": p["context"], "labels": labels})
    return out


def cuad_examples(contracts: list[dict], negatives_per_contract: int = 5, max_chars: int = 1200,
                  seed: int = 0) -> list[dict]:
    """One example per labelled clause span (all its categories), plus a few unlabelled sentences
    per contract as "no type" negatives."""
    rng = random.Random(f"cuad-{seed}")
    out = []
    for c in contracts:
        by_text: dict[str, set[str]] = {}
        for cat, texts in c["labels"].items():
            for t in texts:
                by_text.setdefault(t.strip()[:max_chars], set()).add(cat)
        for t, cats in by_text.items():
            out.append(chat(CUAD_SYSTEM, f"CLAUSE:\n{t}", {"types": sorted(cats)}, "cuad"))
        labelled = " ".join(by_text)
        sents = [s.strip() for s in re.split(r"(?<=[.;])\s+", c["context"]) if 60 < len(s.strip()) < max_chars]
        sents = [s for s in sents if s not in labelled]
        for s in rng.sample(sents, min(negatives_per_contract, len(sents))):
            out.append(chat(CUAD_SYSTEM, f"CLAUSE:\n{s}", {"types": []}, "cuad"))
    return out


def cuad_tag_f1(gold: list[list[str]], pred: list[list[str]]) -> dict:
    """Micro and macro F1 of multi-label CUAD tags (proposal §5: CUAD tag F1)."""
    from collections import Counter

    tp, fp, fn = Counter(), Counter(), Counter()
    for g, p in zip(gold, pred):
        g, p = set(g), set(p)
        for c in g & p:
            tp[c] += 1
        for c in p - g:
            fp[c] += 1
        for c in g - p:
            fn[c] += 1
    cats = set(tp) | set(fp) | set(fn)
    f1 = lambda a, b, c: 2 * a / (2 * a + b + c) if a else 0.0
    micro = f1(sum(tp.values()), sum(fp.values()), sum(fn.values()))
    macro = sum(f1(tp[c], fp[c], fn[c]) for c in cats) / len(cats) if cats else 0.0
    return {"micro_f1": round(micro, 4), "macro_f1": round(macro, 4), "n": len(gold), "n_types": len(cats)}


# ------------------------------------------------------------------ frames

def frame_examples(silver_jsonl: str | Path, batch: int = 12) -> list[dict]:
    """Silver frames file (one JSON per line: {"doc_id", "segments": [...], "ids": [...], "frames": [...]})
    -> frame-extraction examples with the exact prompt the pipeline sends."""
    out = []
    for line in Path(silver_jsonl).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        draft = Draft(str(r["doc_id"]), r["segments"])
        ids = r.get("ids") or list(range(len(r["segments"])))
        for i in range(0, len(ids), batch):
            chunk = ids[i:i + batch]
            frames = [{k: v for k, v in f.items() if k != "source"} for f in r["frames"] if f["segment"] in chunk]
            out.append(chat(FRAME_SYSTEM, f"SEGMENTS:\n{draft.numbered(chunk)}", {"frames": frames}, "frames"))
    return out


def build_all(out_dir: str | Path, nli: list[dict], cuad: list[dict] = (), frames: list[dict] = (),
              val_share: float = 0.05, seed: int = 0, max_per_task: int | None = None) -> dict:
    rng = random.Random(f"mix-{seed}")
    tasks = {"nli": list(nli), "cuad": list(cuad), "frames": list(frames)}
    for k, v in tasks.items():
        rng.shuffle(v)
        if max_per_task:
            tasks[k] = v[:max_per_task]
    allx = [x for v in tasks.values() for x in v]
    rng.shuffle(allx)
    n_val = int(len(allx) * val_share)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in (("val", allx[:n_val]), ("train", allx[n_val:])):
        with (out / f"{name}.jsonl").open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    manifest = {"counts": {k: len(v) for k, v in tasks.items()}, "train": len(allx) - n_val, "val": n_val,
                "held_out_hypotheses": list(HELD_OUT_HYPOTHESES), "seed": seed}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def silver_frames(llm, data: ContractNLI, out_path: str | Path, split: str = "train", limit: int | None = None,
                  max_segments: int = 60) -> int:
    """Silver frames for training (Gemini Flash in the proposal): the prompted frame extractor over
    the first `max_segments` segments of each NDA. Returns the number of NDAs written."""
    from ..review.frames import extract_frames

    docs = data[split][:limit] if limit else data[split]
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w") as f:
        for doc in docs:
            draft = Draft.from_nda(doc)
            ids = list(range(min(len(draft.segments), max_segments)))
            frames = extract_frames(llm, draft, ids, fallback=False)
            f.write(json.dumps({"doc_id": doc.id, "segments": draft.segments, "ids": ids,
                                "frames": [fr.as_dict() for fr in frames]}) + "\n")
            n += 1
    return n
