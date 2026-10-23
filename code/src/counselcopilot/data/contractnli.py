"""ContractNLI loader (Koreeda & Manning, 2021; CC BY 4.0).

The dataset has 607 NDAs split 423 / 61 / 123 (train / dev / test). Every NDA is labelled
against the same 17 hypotheses ("nda-1" ... "nda-20", with gaps) as Entailment,
Contradiction or NotMentioned, with evidence given as indices into the document's spans.

Run `cc data download` once to fetch the zip into data/raw/.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from pathlib import Path

SPLITS = ("train", "dev", "test")


class NLILabel(str, Enum):
    ENTAILMENT = "Entailment"
    CONTRADICTION = "Contradiction"
    NOT_MENTIONED = "NotMentioned"


# Five hypotheses kept out of fine-tuning (design §6, D18), so detection on rules anchored
# to them shows the gain comes from the pipeline rather than memorised labels.
# Default choice: a mix of an omission-heavy check (nda-16), a loophole check used by RQ2
# (nda-20), the standard independent-development carve-out (nda-12), and two ordinary clause
# checks (nda-3, nda-8). Change it here before any fine-tuning run, never after.
HELD_OUT_HYPOTHESES: tuple[str, ...] = ("nda-3", "nda-8", "nda-12", "nda-16", "nda-20")

# ContractNLI checks that describe loopholes from the disclosing party's side (design §5.3), with
# the label that means "the loophole is there". nda-3 is the other way round: an NDA that
# contradicts "may include verbally conveyed information" leaves oral disclosures unprotected.
# nda-12 (independent development) and nda-13 (third-party acquisition) are market-standard
# carve-outs, not loopholes: a repair that deletes them would be unreasonable, so they are not
# counted (audit 22 Oct 2026).
LOOPHOLE_LABELS: dict[str, str] = {"nda-2": "Entailment", "nda-3": "Contradiction", "nda-20": "Entailment"}
LOOPHOLE_HYPOTHESES: tuple[str, ...] = tuple(LOOPHOLE_LABELS)
STANDARD_CARVE_OUTS: tuple[str, ...] = ("nda-12", "nda-13")


@dataclass(frozen=True)
class Hypothesis:
    key: str
    short_description: str
    text: str

    @property
    def held_out(self) -> bool:
        return self.key in HELD_OUT_HYPOTHESES


@dataclass(frozen=True)
class Annotation:
    label: NLILabel
    spans: tuple[int, ...]


@dataclass
class NDADocument:
    id: int
    file_name: str
    text: str
    spans: list[tuple[int, int]]
    annotations: dict[str, Annotation]
    document_type: str
    url: str
    split: str = ""

    def span_text(self, i: int) -> str:
        s, e = self.spans[i]
        return self.text[s:e]

    @cached_property
    def span_texts(self) -> list[str]:
        return [self.span_text(i) for i in range(len(self.spans))]

    def evidence_text(self, hypothesis: str) -> list[str]:
        return [self.span_text(i) for i in self.annotations[hypothesis].spans]


@dataclass
class ContractNLI:
    hypotheses: dict[str, Hypothesis]
    splits: dict[str, list[NDADocument]] = field(default_factory=dict)

    def __getitem__(self, split: str) -> list[NDADocument]:
        return self.splits[split]

    def by_id(self, doc_id: int) -> NDADocument:
        for docs in self.splits.values():
            for d in docs:
                if d.id == doc_id:
                    return d
        raise KeyError(doc_id)

    @property
    def hypothesis_keys(self) -> list[str]:
        return sorted(self.hypotheses, key=lambda k: int(k.split("-")[1]))

    def train_hypotheses(self) -> list[str]:
        return [h for h in self.hypothesis_keys if h not in HELD_OUT_HYPOTHESES]

    def label_counts(self, split: str) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {h: {l.value: 0 for l in NLILabel} for h in self.hypothesis_keys}
        for d in self.splits[split]:
            for h, a in d.annotations.items():
                out[h][a.label.value] += 1
        return out


def _parse_doc(raw: dict, split: str) -> NDADocument:
    anns = raw["annotation_sets"][0]["annotations"]
    return NDADocument(
        id=raw["id"],
        file_name=raw["file_name"],
        text=raw["text"],
        spans=[tuple(s) for s in raw["spans"]],
        annotations={h: Annotation(NLILabel(a["choice"]), tuple(a["spans"])) for h, a in anns.items()},
        document_type=raw.get("document_type", ""),
        url=raw.get("url", ""),
        split=split,
    )


def load_contractnli(root: str | Path, splits: tuple[str, ...] = SPLITS) -> ContractNLI:
    """Load ContractNLI from a folder containing train.json, dev.json and test.json."""
    root = Path(root)
    if (root / "contract-nli").is_dir():
        root = root / "contract-nli"
    hyps: dict[str, Hypothesis] = {}
    out: dict[str, list[NDADocument]] = {}
    for split in splits:
        path = root / f"{split}.json"
        if not path.exists():
            raise FileNotFoundError(f"{path} not found; run `cc data download` first")
        raw = json.loads(path.read_text(encoding="utf-8"))
        for k, v in raw["labels"].items():
            hyps[k] = Hypothesis(k, v["short_description"], v["hypothesis"])
        out[split] = [_parse_doc(d, split) for d in raw["documents"]]
    return ContractNLI(hyps, out)
