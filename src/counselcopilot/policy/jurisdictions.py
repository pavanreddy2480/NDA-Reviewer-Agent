"""Jurisdiction names. Governing law is stored as a lower-case US state ("delaware",
"new york") when the NDA names one, "united states" when it only names the US, otherwise a
lower-case country ("united kingdom", "singapore"), or "unknown"."""

from __future__ import annotations

import re

US_STATES = frozenset({
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida",
    "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska",
    "nevada", "new hampshire", "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina", "south dakota", "tennessee", "texas",
    "utah", "vermont", "virginia", "washington", "west virginia", "wisconsin", "wyoming", "district of columbia",
})
CA_PROVINCES = frozenset({"ontario", "quebec", "british columbia", "alberta", "manitoba", "saskatchewan",
                          "nova scotia", "new brunswick", "newfoundland", "prince edward island"})
ALIASES = {"england and wales": "united kingdom", "england": "united kingdom", "republic of india": "india",
           "republic of south africa": "south africa", "united states of america": "united states",
           "republic of singapore": "singapore", "new south wales": "australia", "victoria": "australia",
           "usa": "united states", "u.s.": "united states", "us": "united states"}


def normalise_jurisdiction(raw: str | None) -> str | None:
    if raw is None:
        return None
    x = re.sub(r"^(the\s+)?(state|commonwealth|province) of\s+", "", str(raw).strip().lower())
    x = re.split(r"\s+(?:without|and|excluding|applicable|as|in)\b|,", x)[0].strip()
    if x in CA_PROVINCES:
        return "canada"
    return ALIASES.get(x, x)


def is_us(j: str | None) -> bool:
    return j in US_STATES or j == "united states"


# Countries seen in ContractNLI governing-law clauses, plus common ones. Anything else a regex
# pulls out ("state", "republic of singapore for every intent an") is not a jurisdiction.
COUNTRIES = {"united states", "united kingdom", "canada", "singapore", "india", "australia", "germany", "france",
             "netherlands", "switzerland", "ireland", "israel", "japan", "china", "hong kong", "south africa",
             "new zealand", "sweden", "belgium", "luxembourg", "spain", "italy", "korea", "taiwan", "brazil",
             "mexico", "scotland", "united arab emirates", "denmark", "norway", "finland", "austria"}


def is_jurisdiction(j: str | None) -> bool:
    return j is not None and (j in US_STATES or j in COUNTRIES)
