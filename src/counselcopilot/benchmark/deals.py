"""Deal contexts for benchmark NDAs (design §7: one per test NDA, spread over the three
companies and four counterparty types).

ContractNLI has no deal metadata, so each NDA gets the short form a consultant would fill in.
Since 25 Oct 2026 the facts the NDA itself shows are read from its labels (benchmark/autolabel.py):
counterparty type from `counterparty_role` / `counterparty_kind`, counterparty country from
`counterparty_country`, personal data and the mutual side as before. Only what lives on the form
alone is drawn: which of our companies is the party, the value band, and a counterparty type where
the NDA doesn't show one. `deal_sources` says which facts were read and which were assigned, so
results can be reported on read facts only.

Every draw is seeded by (seed, NDA id), so an NDA's deal never depends on which other NDAs are in
the run, and seeds give real deal draws (proposal §7: 3 per NDA). Keep `seed` fixed across model
seeds (audit 22 Oct). Governing law is never on the form; the reviewer reads it from the NDA.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from ..policy.schema import CounterpartyType, DealContext

TYPES = [t.value for t in CounterpartyType]
# Counterparty type for an NDA whose role is unknown. An individual can only be an employee-type
# counterparty (employee, contractor, consultant); a company can be any of the other three.
COMPANY_TYPES = ("vendor", "customer", "partner")


def _known(v) -> bool:
    return v is not None and v not in ("unknown", "disputed", "")


def deal_sources(label: dict | None) -> dict[str, str]:
    """For each form fact: "label" if the NDA's label gave it, "assigned" if it was drawn."""
    lab = label or {}
    role, kind = lab.get("counterparty_role"), lab.get("counterparty_kind")
    return {
        "counterparty_type": "label" if role in TYPES or kind == "individual" else "assigned",
        "counterparty_country": "label" if _known(lab.get("counterparty_country")) else "assigned",
        "personal_data": "label" if isinstance(lab.get("personal_data"), bool) else "unknown",
        "company": "assigned",
        "value_band": "assigned",
    }


def _country(raw) -> str:
    """Form value for the counterparty country. Not stated in the NDA: assume a US counterparty
    (the companies are US companies; we never invent a foreign one)."""
    if not _known(raw) or str(raw).strip().lower() in ("united states", "us", "usa"):
        return "US"
    return str(raw).strip().lower()


def deal_for(doc_id: int, companies: list[str], label: dict | None = None, seed: int = 0) -> DealContext:
    lab = label or {}
    rng = random.Random(f"deal-{seed}-{doc_id}")
    company = sorted(companies)[rng.randrange(len(companies))]
    role, kind = lab.get("counterparty_role"), lab.get("counterparty_kind")
    if role in TYPES:
        ctype = role
    elif kind == "individual":
        ctype = "employee"
    elif kind == "company":
        ctype = rng.choice(COMPANY_TYPES)
    else:
        ctype = rng.choice(TYPES)
    pd = lab.get("personal_data")
    return DealContext(
        company=company,
        counterparty_type=ctype,
        # unknown personal data stays blank on the form (the reviewer reads it from the NDA), so
        # hidden-fact and form runs score the same rules (gold-deals audit, point 8)
        personal_data=pd if isinstance(pd, bool) else None,
        counterparty_country=_country(lab.get("counterparty_country")),
        value_band=rng.choice(["low", "medium", "high"]),
        company_side="mutual" if lab.get("mutual") is True else "disclosing",
    )


def generate_deals(doc_ids: list[int], companies: list[str], seed: int = 0,
                   labels: dict[int, dict] | None = None) -> dict[int, DealContext]:
    labels = labels or {}
    return {i: deal_for(i, companies, labels.get(i), seed) for i in doc_ids}


def save_deals(deals: dict[int, DealContext], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({str(k): v.model_dump(mode="json") for k, v in deals.items()}, indent=1))


def load_deals(path: str | Path) -> dict[int, DealContext]:
    raw = json.loads(Path(path).read_text())
    return {int(k): DealContext.model_validate(v) for k, v in raw.items()}
