from pathlib import Path
import json

import httpx
import pytest

from counselcopilot.data.draft import Draft
from counselcopilot.policy.schema import PolicyPack
from counselcopilot.retrieval.index import HybridIndex, Passage
from counselcopilot.review.agentic import _registry
from counselcopilot.tools.legal_tools import build_registry
from counselcopilot.tools.web_search import MAX_QUERY, web_search

TOY_PACK = Path(__file__).resolve().parents[1] / "packs" / "toy" / "toy_pack.yaml"

CFR = {"results": [
    {"ends_on": "2017-07-30", "starts_on": "2017-05-30", "hierarchy": {"title": "17", "part": "165", "section": "165.1"},
     "headings": {"section": "Superseded"}, "full_text_excerpt": "old"},
    {"ends_on": None, "starts_on": "2017-07-31", "hierarchy": {"title": "17", "part": "165", "section": "165.19"},
     "headings": {"section": "Nonenforceability"}, "full_text_excerpt": "may not be <strong>waived</strong>"},
    {"ends_on": None, "starts_on": "2020-01-01", "hierarchy": {"title": "17", "part": "165", "section": None},
     "headings": {"section": None, "part": "Whistleblower Rules"}, "full_text_excerpt": ""},
]}
GOV = {"results": [{"title": "Immunity from liability", "packageId": "USCODE-2024-title18", "dateIssued": "2024-12-31",
                    "granuleId": "USCODE-2024-title18-partI-chap90-sec1833"}]}
FR = {"results": [{"title": "Rule", "html_url": "https://fr.example/1", "publication_date": "2026-01-02", "abstract": None}]}


def client(seen=None, broken=()):
    def handle(req: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(req)
        for name, payload in (("govinfo", GOV), ("ecfr", CFR), ("federalregister", FR)):
            if name in req.url.host:
                return httpx.Response(429 if name in broken else 200, json=payload)
        raise AssertionError(req.url)

    return httpx.Client(transport=httpx.MockTransport(handle))


def test_all_sources_are_merged_into_citable_hits():
    out = web_search("trade secret immunity", client=client())
    assert out["errors"] == {} and {r["source"] for r in out["results"]} == {"us_code", "cfr", "federal_register"}
    code = out["results"][0]
    assert code["title"] == "18 U.S.C. § 1833: Immunity from liability"
    assert code["url"].endswith("/USCODE-2024-title18/USCODE-2024-title18-partI-chap90-sec1833")


def test_superseded_regulations_are_dropped():
    hits = web_search("waiver", ["cfr"], client=client())["results"]
    assert [h["url"] for h in hits] == ["https://www.ecfr.gov/current/title-17/section-165.19",
                                        "https://www.ecfr.gov/current/title-17/part-165"]
    assert hits[0]["snippet"] == "may not be waived"  # no markup reaches a prompt


def test_one_source_failing_keeps_the_others():
    out = web_search("q", client=client(broken=("govinfo",)))
    assert out["errors"] == {"us_code": "rate limited; set GOVINFO_API_KEY"}
    assert {r["source"] for r in out["results"]} == {"cfr", "federal_register"}


def test_network_failure_is_reported_not_raised():
    def down(req):
        raise httpx.ConnectError("down")

    out = web_search("q", client=httpx.Client(transport=httpx.MockTransport(down)))
    assert out["results"] == [] and set(out["errors"]) == {"us_code", "cfr", "federal_register"}


def test_api_key_stays_out_of_the_url_and_errors(monkeypatch):
    monkeypatch.setenv("GOVINFO_API_KEY", "secret-key")
    seen = []
    out = web_search("q", ["us_code"], client=client(seen, broken=("govinfo",)))
    assert seen[0].headers["x-api-key"] == "secret-key" and "secret-key" not in str(seen[0].url)
    assert "secret-key" not in json.dumps(out)


@pytest.mark.parametrize("query", ["", "   ", "x" * (MAX_QUERY + 1)])
def test_bad_query_is_refused_before_any_request(query):
    seen = []
    with pytest.raises(ValueError):
        web_search(query, client=client(seen))
    assert seen == []


def test_tool_is_registered_and_too_long_a_query_is_an_agent_error():
    calls = []
    reg = build_registry(PolicyPack.load(TOY_PACK), search=lambda q, limit: calls.append((q, limit)) or {"results": []})
    assert reg.call("web_search", {"query": "non-compete"}).status == "ok" and calls == [("non-compete", 2)]
    real = build_registry(PolicyPack.load(TOY_PACK))
    assert real.call("web_search", {"query": "x" * (MAX_QUERY + 1)}).status == "error"


def test_the_nda_agent_has_no_way_to_reach_the_web():
    draft = Draft("d", ["Some confidential clause."])
    index = HybridIndex([Passage("0", draft.segments[0])])
    assert set(_registry(draft, index, set(), {}).tools) == {"search_nda", "read_segments"}
