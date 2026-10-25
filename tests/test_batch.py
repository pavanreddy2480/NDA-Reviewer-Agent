"""Batch rounds (proposal §10: Gemini Batch API at half price; packs, labels and pilot runs answered
by Claude agents with no API). Requests go out as files and answers come back into the cache."""

import json

from counselcopilot.llm import BatchQueue, FakeClient, ResponseCache, system, user
from counselcopilot.llm.base import LLMRequest
from counselcopilot.llm.batch import export_shards, load_answers, load_results, to_gemini_jsonl


def queue(tmp_path, n=3, schema=None):
    q = BatchQueue(tmp_path / "q.jsonl")
    reqs = []
    for i in range(n):
        r = LLMRequest("m", (system("SYS"), user(f"question {i}")), temperature=0.0, max_tokens=300,
                       json_schema=schema, seed=i)
        q.add(r.cache_key(), r)
        reqs.append(r)
    return q, reqs


def test_gemini_jsonl_maps_roles_schema_and_thinking_budget(tmp_path):
    q, reqs = queue(tmp_path, 1, schema={"type": "object"})
    out = tmp_path / "g.jsonl"
    assert to_gemini_jsonl(q.path, out, thinking_budget=512) == 1
    row = json.loads(out.read_text())
    cfg = row["request"]["generationConfig"]
    assert row["key"] == reqs[0].cache_key()
    assert row["request"]["systemInstruction"] == {"parts": [{"text": "SYS"}]}
    assert row["request"]["contents"] == [{"role": "user", "parts": [{"text": "question 0"}]}]
    assert cfg["maxOutputTokens"] == 300 + 512  # thinking tokens share the output limit
    assert cfg["responseMimeType"] == "application/json" and cfg["thinkingConfig"] == {"thinkingBudget": 512}


def test_gemini_results_load_into_the_cache_without_thoughts(tmp_path):
    cache = ResponseCache(":memory:")
    line = json.dumps({"key": "k1", "response": {
        "candidates": [{"content": {"parts": [{"text": "thinking...", "thought": True}, {"text": '{"a": 1}'}]}}],
        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 4, "thoughtsTokenCount": 6}}})
    assert load_results([line, "", json.dumps({"key": "k2"})], "flash", cache) == 1
    hit = cache.get("k1")
    assert hit["text"] == '{"a": 1}' and hit["output_tokens"] == 10  # thinking is billed as output


def test_agent_shards_skip_cached_requests_and_answers_fill_the_cache(tmp_path):
    q, reqs = queue(tmp_path, 5)
    cache = ResponseCache(":memory:")
    cache.put(reqs[0].cache_key(), "m", {"text": "done", "model": "m", "input_tokens": 0, "output_tokens": 0})
    out = export_shards(q.path, tmp_path / "round1", cache, per_shard=2)
    assert out["requests"] == 4 and [s["n"] for s in out["shards"]] == [2, 2]
    first = json.loads((tmp_path / "round1" / "shard_000.jsonl").read_text().splitlines()[0])
    assert set(first) == {"key", "system", "messages", "schema"} and first["system"] == "SYS"

    answers = tmp_path / "round1" / "answers"
    lines = [json.dumps({"key": r.cache_key(), "text": {"label": "Entailment"}}) for r in reqs[1:4]]
    (answers / "a.jsonl").write_text("\n".join(lines + ["{broken", json.dumps({"key": "nope", "text": "x"})]))
    rep = load_answers(answers, q.path, "claude (agent)", cache)
    assert rep == {"loaded": 3, "unknown_keys": 1, "bad_lines": 1, "still_missing": 1}

    llm = FakeClient(lambda r: "live call", model="m", cache=cache)
    assert json.loads(llm.complete(list(reqs[1].messages), seed=1, max_tokens=300).text) == {"label": "Entailment"}
    assert llm.requests == []
