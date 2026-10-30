"""Findings and the shared findings ledger (design §3.1)."""

from __future__ import annotations

import threading
from enum import Enum

from pydantic import BaseModel, Field


class FindingType(str, Enum):
    VIOLATION = "violation"
    OMISSION = "omission"
    APPROVAL_NEEDED = "approval_needed"
    STATUTORY_RISK = "statutory_risk"
    INCONSISTENCY = "inconsistency"


class Finding(BaseModel):
    draft_id: str
    rule_id: str  # policy rule or law provision; "" for pure consistency findings
    type: FindingType
    evidence: list[int] = Field(default_factory=list)  # draft segment indices (empty for omissions)
    explanation: str = ""
    confidence: float = 0.5
    reviewer: str = ""  # which agent produced it
    direction: str = ""  # "forward" | "reverse" | "exhaustive" | "long_context" | "agentic"
    verified: bool | None = None  # set by the verifier
    severity: str = "medium"

    @property
    def key(self) -> tuple[str, str]:
        return (self.rule_id, self.type.value)


class Ledger:
    """Thread-safe store of findings; one finding per (rule, type), keeping the most confident."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str], Finding] = {}
        self._lock = threading.Lock()

    def add(self, f: Finding) -> None:
        with self._lock:
            old = self._items.get(f.key)
            if old is None or f.confidence > old.confidence:
                if old is not None:  # keep the union of cited evidence
                    f = f.model_copy(update={"evidence": sorted(set(f.evidence) | set(old.evidence))})
                self._items[f.key] = f

    def extend(self, fs: list[Finding]) -> None:
        for f in fs:
            self.add(f)

    def all(self) -> list[Finding]:
        with self._lock:
            return sorted(self._items.values(), key=lambda f: (f.rule_id, f.type.value))

    def __len__(self) -> int:
        return len(self._items)
