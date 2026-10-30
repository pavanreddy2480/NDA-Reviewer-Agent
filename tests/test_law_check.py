from pathlib import Path
import json

import httpx

from counselcopilot.experiments.law_check import _query, check_law_pack, check_provision
from counselcopilot.policy.schema import LawPack, LawProvision
from counselcopilot.tools.web_search import MAX_QUERY, fetch_source, web_search

ROOT = Path(__file__).resolve().parents[1]
TOY_PACK = ROOT / "packs" / "toy" / "toy_pack.yaml"

LAW = ROOT / "packs" / "law" / "us_law_pack.yaml"
CORNELL = "https://www.law.cornell.edu/uscode/text/18/1833"


def prov(act="Defend Trade Secrets Act (18 U.S.C.)", url=CORNELL):
    return LawProvision(id="LAW-X", act=act, section="1", title="Notice", summary="An employer must give immunity notice.",
                        risk_pattern="x", source_url=url)


def client(handle):
    return httpx.Client(transport=httpx.MockTransport(handle))


def page(body, status=200, **kw):
    return lambda req: httpx.Response(status, text=body, **kw)


def test_page_text_has_no_markup_or_scripts():
    body = "<html><script>var a=1;</script><style>p{}</style><p>Sec.&nbsp;&sect; 1833 <b>immunity</b></p></html>"
    out = fetch_source(CORNELL, client(page(body)))
    assert out["status"] == "ok" and "§ 1833 immunity" in out["text"].replace("\xa0", " ")
    assert "var a" not in out["text"] and "p{}" not in out["text"]


def test_refusal_is_reported_and_only_one_request_is_made():
    calls = []

    def handle(req):
        calls.append(req)
        return httpx.Response(403, text="Forbidden")

    out = fetch_source("https://leginfo.legislature.ca.gov/faces/x", client(handle))
    assert out["status"] == "refused" and "refuses" in out["why"] and len(calls) == 1


def test_only_https_official_hosts_are_read():
    def fail(req):
        raise AssertionError("no request should be made")

    for url in ("https://example.com/law", "http://www.law.cornell.edu/x", "https://law.cornell.edu.evil.com/x",
                "https://notlaw.cornell.edu.example/x", "file:///etc/passwd"):
        assert fetch_source(url, client(fail))["status"] == "error", url


def test_redirect_to_another_site_is_not_followed():
    seen = []

    def handle(req):
        seen.append(str(req.url))
        return httpx.Response(302, headers={"location": "https://evil.example/x"})

    out = fetch_source(CORNELL, client(handle))
    assert out["status"] == "error" and "evil.example" in out["why"] and seen == [CORNELL]


def test_redirect_inside_an_official_site_is_followed():
    def handle(req):
        if req.url.path == "/a":
            return httpx.Response(301, headers={"location": "/b"})
        return httpx.Response(200, text="<p>moved here</p>")

    assert fetch_source("https://www.law.cornell.edu/a", client(handle))["text"] == "moved here"


def test_redirect_loop_ends():
    out = fetch_source(CORNELL, client(lambda r: httpx.Response(302, headers={"location": CORNELL})))
    assert out == {"status": "error", "text": "", "why": "too many redirects"}


def test_network_failure_is_an_error_not_a_crash():
    def down(req):
        raise httpx.ConnectError("down")

    assert fetch_source(CORNELL, client(down))["why"] == "ConnectError"


def test_quoted_phrases_reach_govinfo_unquoted():
    seen = []

    def handle(req):
        seen.append(json.loads(req.content)["query"])
        return httpx.Response(200, json={"results": []})

    web_search('"trade secret" immunity', ["us_code"], client=client(handle))
    assert '"' not in seen[0] and "trade secret" in seen[0]


def test_govinfo_key_can_come_from_dotenv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GOVINFO_API_KEY", raising=False)
    (tmp_path / ".env").write_text("GOVINFO_API_KEY=from-file\n", encoding="utf-8")
    seen = []

    def handle(req):
        seen.append(req.headers["x-api-key"])
        return httpx.Response(200, json={"results": []})

    web_search("q", ["us_code"], client=client(handle))
    assert seen == ["from-file"]


def test_coverage_names_the_summary_words_the_page_lacks():
    row = check_provision(prov(), lambda q, limit: {"results": [], "errors": {}},
                          lambda url: {"status": "ok", "text": "employers give notice", "why": ""})
    assert row["coverage"] == 0.6 and row["missing"] == ["immunity", "must"]


def test_only_federal_acts_are_searched():
    searched = []

    def search(q, limit):
        searched.append(q)
        return {"results": [], "errors": {}}

    ok = lambda url: {"status": "ok", "text": "", "why": ""}
    check_provision(prov("California Business and Professions Code"), search, ok)
    check_provision(prov("Common law of contracts"), search, ok)
    assert searched == []
    check_provision(prov(), search, ok)
    assert len(searched) == 1 and len(searched[0]) <= MAX_QUERY


def test_search_query_is_cut_on_a_word_and_fits():
    p = prov().model_copy(update={"title": "word " * 100})
    assert len(_query(p)) <= MAX_QUERY and _query(p).endswith("word")
    assert _query(prov().model_copy(update={"id": "LAW-SEC-21F17"})) == "whistleblower confidentiality agreement"


def test_report_lists_refused_sources_and_changes_no_pack(tmp_path):
    before = LAW.read_bytes()
    pack = LawPack.load(LAW)
    leads = {"results": [{"source": "cfr", "title": "T", "date": "2026-01-01", "url": "https://u"}],
             "errors": {"us_code": "rate limited; set GOVINFO_API_KEY"}}

    def fetch(url):
        if "leginfo" in url:
            return {"status": "refused", "text": "", "why": "HTTP 403: the site refuses automated readers"}
        return {"status": "ok", "text": "immunity notice", "why": ""}

    report, path = check_law_pack(pack, str(tmp_path), lambda q, limit: leads, fetch)
    assert "4 of 7 sources read automatically" in report and report.count("Read this one in a browser") == 3
    assert "Search on us_code failed" in report and "Signed off by 0 of 2 people" in report
    assert open(path, encoding="utf-8").read() == report and LAW.read_bytes() == before
    assert LawPack.load(LAW).unchecked() == pack.unchecked()
