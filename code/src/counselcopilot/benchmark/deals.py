"""Deal contexts for benchmark NDAs (design §7: one per test NDA, spread over the three
companies and four counterparty types). Deterministic for a given seed."""

from __future__ import annotations

import json
import random
from pathlib import Path

from ..policy.schema import CounterpartyType, DealContext

FOREIGN = ("GB", "DE", "SG", "IN", "CA")


def generate_deals(doc_ids: list[int], companies: list[str], seed: int = 0,
                   p_personal_data: float = 0.5, p_foreign: float = 0.3,
                   labels: dict[int, dict] | None = None) -> dict[int, DealContext]:
    """With labels, the form agrees with the NDA: personal data comes from the label (drawn
    only where the label is unknown) and a mutual NDA puts the company on the mutual side.
    Governing law is never on the form; the reviewer reads it from the NDA (design §16, 4).
    Deals depend only on `seed`, so keep it fixed across model seeds (audit 22 Oct)."""
    labels = labels or {}
    rng = random.Random(seed)
    types = list(CounterpartyType)
    out: dict[int, DealContext] = {}
    for n, doc_id in enumerate(sorted(doc_ids)):
        out[doc_id] = DealContext(
            company=companies[n % len(companies)],
            counterparty_type=types[(n // len(companies)) % len(types)],
            personal_data=_label_or(labels.get(doc_id, {}).get("personal_data"), rng.random() < p_personal_data),
            counterparty_country=rng.choice(FOREIGN) if rng.random() < p_foreign else "US",
            value_band=rng.choice(["low", "medium", "high"]),
            company_side="mutual" if labels.get(doc_id, {}).get("mutual") is True else "disclosing",
        )
    return out


def _label_or(label, drawn: bool) -> bool:
    return label if isinstance(label, bool) else drawn


def save_deals(deals: dict[int, DealContext], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({str(k): v.model_dump(mode="json") for k, v in deals.items()}, indent=1))


def load_deals(path: str | Path) -> dict[int, DealContext]:
    raw = json.loads(Path(path).read_text())
    return {int(k): DealContext.model_validate(v) for k, v in raw.items()}
