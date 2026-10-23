"""Per-NDA hand labels (design §7.1 field rules, plus review problems 1 and 2).

One YAML file, one entry per NDA id, filled by two annotators on a 20% overlap:

    1234:
      verified: false            # set true once a person has checked the entry
      is_template: true          # has blanks such as "____" or "[date]"
      mutual: true               # both parties disclose
      company_party: "Party A"   # which named party our company is (needed for loopholes)
      governing_law: delaware    # lower-case US state, "united states", a country, "none" (the NDA
                                 # names no governing law) or "unknown" (can't tell)
      personal_data: null        # true / false / null if the annotator can't tell
      fields:                    # values for field rules; "blank" = left blank in a template
        confidentiality_term_months: 36
        return_deadline_days: blank

`cc labels init` writes this file pre-filled by regex so annotators only correct it. Only
entries with `verified: true` are used for scoring unless --allow-unverified is passed.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from ..data.contractnli import NDADocument
from ..policy.jurisdictions import is_jurisdiction, normalise_jurisdiction

_BLANK = re.compile(r"_{4,}|…{2,}|\.{6,}|\[\s*(?:date|name|number|insert|●)?[^\]]{0,20}\]", re.I)
_LAW = re.compile(r"govern\w*\s+(?:by|in accordance with)[^.]{0,80}?laws?\s+of\s+(?:the\s+)?([A-Z][A-Za-z ]{2,40})")


def normalise_country(raw: str) -> str:
    """Kept for callers; US states are kept as states (see policy/jurisdictions.py)."""
    return normalise_jurisdiction(raw) or "unknown"


def prefill(doc: NDADocument) -> dict:
    m = _LAW.search(doc.text)
    law = normalise_country(m.group(1)) if m else "unknown"
    return {
        "verified": False,
        "is_template": bool(_BLANK.search(doc.text)),
        "mutual": bool(re.search(r"\bmutual\b", doc.text, re.I)),
        "company_party": None,
        "governing_law": law if is_jurisdiction(law) else "unknown",
        "personal_data": None,
        "fields": {},
    }


def write_prefilled(docs: list[NDADocument], path: str | Path) -> int:
    path = Path(path)
    existing = load_labels(path, allow_unverified=True) if path.exists() else {}
    out = {d.id: existing.get(d.id) or prefill(d) for d in docs}  # never overwrite human work
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(out, sort_keys=True, allow_unicode=True))
    return len(out)


def usable(entry: dict, allow_auto: bool = False) -> bool:
    """Verified by a person, or (with allow_auto) an auto-labelled entry (benchmark/autolabel.py).
    Keys the two labellers disagreed on hold "disputed", which gold.py leaves unscored, so an
    entry with a few disputed keys is still usable for its agreed keys (23 Oct 2026: with 33 keys
    per NDA, requiring every key to agree discarded 77% of entries at 95% key agreement)."""
    if entry.get("verified"):
        return True
    return allow_auto and bool(entry.get("auto"))


def load_labels(path: str | Path | None, allow_unverified: bool = False,
                allow_auto: bool = False) -> dict[int, dict]:
    if path is None or not Path(path).exists():
        return {}
    raw = yaml.safe_load(Path(path).read_text()) or {}
    return {int(k): v for k, v in raw.items() if allow_unverified or usable(v, allow_auto)}
