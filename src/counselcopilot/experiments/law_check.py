"""Re-check the law pack against its official sources: a report for the two people who sign off
each provision (proposal safety plan). No model and no NDA text is involved.

For each provision it reads the cited source page and says how many of the summary's words appear
there, so the pages that deserve the closest reading stand out. That is a cheap signal, not a
verdict: a high score does not show the summary is right. Federal provisions also get live search
leads, which can show newer rules. Nothing here changes the pack or `checked_by`.
"""

from __future__ import annotations

import re
from typing import Callable

from ..policy.schema import LawPack, LawProvision
from ..retrieval.index import tokenize
from ..tools.web_search import MAX_QUERY, fetch_source, web_search
from .common import run_dir

_FEDERAL = re.compile(r"U\.S\.C\.|C\.F\.R\.")  # the only acts the search sources cover
MAX_MISSING = 8
# Hand-written and tried on the live sources: a provision's title or summary found mostly noise.
SEARCH_TOPICS = {
    "LAW-DTSA-1833B": "immunity trade secret disclosure to government official or attorney reporting suspected violation of law",
    "LAW-SEC-21F17": "whistleblower confidentiality agreement",
    "LAW-SPEAK-OUT": "sexual harassment nondisclosure clause judicially enforceable",
}


def _query(p: LawProvision) -> str:
    return SEARCH_TOPICS.get(p.id) or f"{p.act.split(' (')[0]} {p.title}"[:MAX_QUERY].rsplit(" ", 1)[0]


def _summary_words(summary: str) -> dict[str, str]:
    """Stem -> the word as written, so a report can show real words."""
    words: dict[str, str] = {}
    for word in re.findall(r"[a-z0-9']+", summary.lower()):
        for stem in tokenize(word):
            words.setdefault(stem, word)
    return words


def check_provision(p: LawProvision, search: Callable[..., dict] = web_search,
                    fetch: Callable[[str], dict] = fetch_source) -> dict:
    page = fetch(p.source_url)
    row = {"id": p.id, "act": p.act, "section": p.section, "url": p.source_url, "status": page["status"],
           "why": page["why"], "n_checked": len(p.checked_by), "coverage": None, "missing": [], "leads": [],
           "lead_errors": {}}
    if page["status"] == "ok":
        words = _summary_words(p.summary)
        found = set(tokenize(page["text"]))
        missing = sorted(w for stem, w in words.items() if stem not in found)
        row["coverage"] = round(1 - len(missing) / max(len(words), 1), 2)
        row["missing"] = missing[:MAX_MISSING]
    if _FEDERAL.search(p.act):
        out = search(_query(p), limit=2)
        row["leads"], row["lead_errors"] = out["results"], out["errors"]
    return row


def format_report(pack: LawPack, rows: list[dict]) -> str:
    done = sum(r["status"] == "ok" for r in rows)
    out = [f"# Law pack check: {pack.jurisdiction}, version {pack.version}, checked as of {pack.as_of}", "",
           f"{done} of {len(rows)} sources read automatically. This is a reading aid, not legal advice: "
           "it changes nothing in the pack, and each provision still needs two people to read the source. "
           "Leads are keyword matches from a live search and can be off-topic.", ""]
    for r in rows:
        out += [f"## {r['id']}: {r['act']} {r['section']}", f"- Source: {r['url']}",
                f"- Signed off by {r['n_checked']} of 2 people"]
        if r["status"] == "ok":
            out.append(f"- {r['coverage']:.0%} of the summary's words are on the page"
                       + (f"; not found: {', '.join(r['missing'])}" if r["missing"] else ""))
        else:
            out.append(f"- **Read this one in a browser.** Not read automatically ({r['why']})")
        out += [f"- Lead: [{x['source']}] {x['title']} ({x['date']}) {x['url']}" for x in r["leads"]]
        out += [f"- Search on {s} failed: {why}" for s, why in r["lead_errors"].items()]
        out.append("")
    return "\n".join(out)


def check_law_pack(pack: LawPack, out_root: str = "runs", search: Callable[..., dict] = web_search,
                   fetch: Callable[[str], dict] = fetch_source) -> tuple[str, str]:
    """Returns (report, path it was saved to)."""
    report = format_report(pack, [check_provision(p, search, fetch) for p in pack.provisions])
    path = run_dir("law-check", out_root) / "report.md"
    path.write_text(report, encoding="utf-8")
    return report, str(path)
