import json

from counselcopilot.llm import FakeClient, ResponseCache, parse_json_loose, user
from counselcopilot.llm.factory import load_backend, schema_example


def test_cache_avoids_second_call(tmp_path):
    llm = FakeClient(lambda r: '{"a": 1}', cache=ResponseCache(tmp_path / "c.sqlite"))
    for _ in range(3):
        assert llm.complete([user("hi")]).json() == {"a": 1}
    assert len(llm.requests) == 1
    u = llm.total_usage()
    assert u.calls == 3 and u.cached_calls == 2
    # different seed -> different cache entry
    llm.complete([user("hi")], seed=1)
    assert len(llm.requests) == 2


def test_parse_json_loose():
    assert parse_json_loose('```json\n{"x": 2}\n```') == {"x": 2}
    assert parse_json_loose('Sure! {"x": 3} hope that helps') == {"x": 3}


def test_complete_json_retries_on_bad_json():
    replies = iter(["not json", '{"ok": true}'])
    llm = FakeClient(lambda r: next(replies))
    assert llm.complete_json([user("x")]) == {"ok": True}


def test_fake_backend_follows_schema():
    llm = load_backend("fake", use_cache=False)
    schema = {"type": "object", "properties": {"label": {"type": "string", "enum": ["A", "B"]},
                                               "ev": {"type": "array"}}}
    assert llm.complete_json([user("x")], schema) == {"label": "A", "ev": []}
    assert schema_example({"type": "number"}) == 0
