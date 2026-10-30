"""web_search: live search over official US legal sources, for looking up and re-checking law.

Three sources, so a result is always a real, citable government text:
    us_code           GovInfo. GOVINFO_API_KEY (free); without it the shared DEMO_KEY, ~10 calls an hour
    cfr               eCFR, current regulations only (no key)
    federal_register  new and proposed federal rules (no key)
California statutes and case law are not covered: neither has a free keyless search API.
`fetch_source` reads one known page from the official sources the law pack cites. A site that
refuses automated readers is reported as refused; we do not disguise the request.

Results are leads for a person, not law: nothing here changes the law pack, which stays small,
cited, dated and checked by two people. Queries leave the machine, so this tool stays away from
NDA text: the reviewer's agents do not get it, and MAX_QUERY is too short to paste a clause into.
Live results also change over time, so a benchmark run must never depend on them.
"""

from __future__ import annotations

import html
import re
from typing import Any, Callable
from urllib.parse import urljoin, urlsplit

import httpx

from ..env import env_value

MAX_QUERY = 200
SNIPPET_CHARS = 200
MAX_PAGE_CHARS = 50_000
ALLOWED_HOSTS = ("law.cornell.edu", "leginfo.legislature.ca.gov", "govinfo.gov", "ecfr.gov", "federalregister.gov")
_TAG = re.compile(r"<[^>]+>")
_SCRIPT = re.compile(r"(?is)<(script|style)\b.*?</\1>")
_GRANULE = re.compile(r"title(\w+?)-.*-sec(\w+)$")
USER_AGENT = "CounselCopilot/0.1 (student research project)"


def _clean(html: str | None) -> str:
    return " ".join(_TAG.sub("", html or "").split())[:SNIPPET_CHARS]


def _hit(source: str, title: str, url: str, date: str | None, snippet: str | None = "") -> dict:
    return {"source": source, "title": _clean(title), "url": url, "date": date or "", "snippet": _clean(snippet)}


def _us_code(http: httpx.Client, query: str, limit: int) -> list[dict]:
    words = query.replace('"', " ")  # GovInfo returns nothing for quoted phrases
    r = http.post("https://api.govinfo.gov/search",
                  headers={"X-Api-Key": env_value("GOVINFO_API_KEY") or "DEMO_KEY"},
                  json={"query": f"collection:USCODE {words}", "pageSize": limit, "offsetMark": "*",
                        "sorts": [{"field": "score", "sortOrder": "DESC"}]})
    r.raise_for_status()
    out = []
    for x in r.json().get("results", []):
        granule = x.get("granuleId", "")
        m = _GRANULE.search(granule)
        cite = f"{m.group(1)} U.S.C. § {m.group(2)}: " if m else ""
        out.append(_hit("us_code", cite + x.get("title", ""),
                        f"https://www.govinfo.gov/app/details/{x['packageId']}/{granule}", x.get("dateIssued")))
    return out


def _cfr(http: httpx.Client, query: str, limit: int) -> list[dict]:
    # the search also returns superseded text, so ask for extra and keep what is still in force
    r = http.get("https://www.ecfr.gov/api/search/v1/results", params={"query": query, "per_page": limit * 4})
    r.raise_for_status()
    out = []
    for x in r.json().get("results", []):
        if x.get("ends_on") is not None:
            continue
        h, names = x.get("hierarchy", {}), x.get("headings", {})
        where = f"section-{h['section']}" if h.get("section") else f"part-{h.get('part')}"
        title = f"{h.get('title')} CFR {h.get('section') or 'part ' + str(h.get('part'))}: {names.get('section') or names.get('part')}"
        out.append(_hit("cfr", title, f"https://www.ecfr.gov/current/title-{h.get('title')}/{where}",
                        x.get("starts_on"), x.get("full_text_excerpt")))
    return out[:limit]


def _federal_register(http: httpx.Client, query: str, limit: int) -> list[dict]:
    r = http.get("https://www.federalregister.gov/api/v1/documents.json",
                 params={"conditions[term]": query, "per_page": limit, "order": "relevance",
                         "fields[]": ["title", "html_url", "publication_date", "abstract"]})
    r.raise_for_status()
    return [_hit("federal_register", x.get("title", ""), x.get("html_url", ""), x.get("publication_date"),
                 x.get("abstract")) for x in r.json().get("results", [])]


SOURCES: dict[str, Callable[[httpx.Client, str, int], list[dict]]] = {
    "us_code": _us_code, "cfr": _cfr, "federal_register": _federal_register,
}


def web_search(query: str, sources: list[str] | None = None, limit: int = 3,
               client: httpx.Client | None = None) -> dict[str, Any]:
    """{"results": [...], "errors": {source: why}}. One source failing never loses the others."""
    query = " ".join(query.split())
    if not query:
        raise ValueError("empty query")
    if len(query) > MAX_QUERY:
        raise ValueError(f"query over {MAX_QUERY} characters: search for the legal topic, never for NDA text")
    http = client or httpx.Client(timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT})
    results: list[dict] = []
    errors: dict[str, str] = {}
    for name in sources or SOURCES:
        try:
            results += SOURCES[name](http, query, limit)
        except httpx.HTTPStatusError as e:  # status only: the exception text carries the full URL
            code = e.response.status_code
            errors[name] = "rate limited; set GOVINFO_API_KEY" if code == 429 and name == "us_code" else f"HTTP {code}"
        except (httpx.HTTPError, ValueError, KeyError) as e:  # network failure or a reply we can't read
            errors[name] = type(e).__name__
    return {"results": results, "errors": errors}


def _allowed(url: str) -> bool:
    parts = urlsplit(url)
    host = parts.hostname or ""
    return parts.scheme == "https" and any(host == d or host.endswith("." + d) for d in ALLOWED_HOSTS)


def fetch_source(url: str, client: httpx.Client | None = None) -> dict[str, str]:
    """{"status": "ok" | "refused" | "error", "text": ..., "why": ...} for an official page.
    Only https pages on ALLOWED_HOSTS are read, and redirects are held to the same list."""
    http = client or httpx.Client(timeout=25, headers={"User-Agent": USER_AGENT})
    try:
        for _ in range(4):
            if not _allowed(url):
                return {"status": "error", "text": "", "why": f"not an allowed source: {urlsplit(url).hostname}"}
            r = http.get(url, follow_redirects=False)
            if not r.is_redirect:
                break
            url = urljoin(url, r.headers.get("location", ""))
        else:
            return {"status": "error", "text": "", "why": "too many redirects"}
    except httpx.HTTPError as e:
        return {"status": "error", "text": "", "why": type(e).__name__}
    if r.status_code in (401, 403, 429):
        return {"status": "refused", "text": "", "why": f"HTTP {r.status_code}: the site refuses automated readers"}
    if r.status_code != 200:
        return {"status": "error", "text": "", "why": f"HTTP {r.status_code}"}
    text = html.unescape(_TAG.sub(" ", _SCRIPT.sub(" ", r.text)))
    return {"status": "ok", "text": " ".join(text.split())[:MAX_PAGE_CHARS], "why": ""}
