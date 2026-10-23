"""An NDA draft as a list of numbered segments that findings can cite and redlines can edit.

Segments are ContractNLI's spans (sentences or list items) when the draft comes from the
dataset, so predicted evidence can be scored against gold evidence directly. Plain-text
drafts are split the same way: by line, then by sentence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from .contractnli import NDADocument

_SENT = re.compile(r"(?<=[.;:])\s+(?=[A-Z(\"“])")


@dataclass(frozen=True)
class Edit:
    """A clause-level redline (design §5.2): insert after, replace, or delete a segment."""

    op: Literal["insert_after", "replace", "delete"]
    segment: int  # index in the current draft; -1 with insert_after inserts at the start
    text: str = ""
    reason: str = ""  # rule id or scenario id this edit fixes


@dataclass
class Draft:
    id: str
    segments: list[str]
    source_ids: list[int | None] = field(default_factory=list)  # original span index, None if new

    def __post_init__(self) -> None:
        if not self.source_ids:
            self.source_ids = list(range(len(self.segments)))

    @classmethod
    def from_nda(cls, doc: NDADocument) -> "Draft":
        return cls(id=str(doc.id), segments=[t.strip() for t in doc.span_texts])

    @classmethod
    def from_text(cls, text: str, draft_id: str = "draft") -> "Draft":
        segs: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                segs.extend(s.strip() for s in _SENT.split(line) if s.strip())
        return cls(id=draft_id, segments=segs)

    def numbered(self, ids: list[int] | None = None) -> str:
        ids = range(len(self.segments)) if ids is None else ids
        return "\n".join(f"[{i}] {self.segments[i]}" for i in ids)

    @property
    def text(self) -> str:
        return "\n".join(self.segments)

    def apply(self, edits: list[Edit]) -> "Draft":
        """Return a new draft with edits applied. Indices refer to *this* draft."""
        segs = list(self.segments)
        src = list(self.source_ids)
        # apply from the end so earlier indices stay valid
        for e in sorted(edits, key=lambda e: e.segment, reverse=True):
            if e.op == "replace":
                segs[e.segment] = e.text
                src[e.segment] = None
            elif e.op == "delete":
                del segs[e.segment], src[e.segment]
            elif e.op == "insert_after":
                segs.insert(e.segment + 1, e.text)
                src.insert(e.segment + 1, None)
        return Draft(self.id, segs, src)
