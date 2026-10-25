"""The backend-neutral LLM layer (proposal §7 two-stage backbone, §10 compute and cost).

Swapping Llama for Gemini is a config change; every answer is cached by the full request so a
re-run costs nothing; batch mode queues uncached requests for the half-price Batch API; cost is
reported per run; benchmark data must come from a model family no tested system uses (§6, §11)."""

import json

import pytest

from counselcopilot.llm import BatchQueue, FakeClient, PendingBatch, ResponseCache, parse_json_loose, system, user
from counselcopilot.llm.backends import AgentClient
from counselcopilot.llm.base import LLMRequest, Message, RetryableError, Usage
from counselcopilot.llm.factory import (backend_config, check_data_maker, family, load_backend, roles,
                                        schema_example)

MSGS = [system("s"), user("u")]


# ------------------------------------------------------------------ JSON parsing

@pytest.mark.parametrize("text, value", [
    ('{"a": 1}', {"a": 1}),
    ('```json\n{"a": 1}\n```', {"a": 1}),
    ('Sure! Here it is: {"a": [1, 2]} Hope that helps.', {"a": [1, 2]}),
    ("[1, 2]", [1, 2]),
])
def test_parse_json_loose(text, value):
    assert parse_json_loose(text) == value


def test_parse_json_loose_fails_loudly():
    with pytest.raises(ValueError):
        parse_json_loose("no json here")


# ------------------------------------------------------------------ cache

def test_cache_key_covers_the_whole_request():
    base = LLMRequest("m", tuple(MSGS))
    variants = [LLMRequest("m2", tuple(MSGS)), LLMRequest("m", (user("other"),)),
                LLMRequest("m", tuple(MSGS), temperature=0.7), LLMRequest("m", tuple(MSGS), max_tokens=9),
                LLMRequest("m", tuple(MSGS), json_schema={"type": "object"}), LLMRequest("m", tuple(MSGS), seed=1),
                LLMRequest("m", tuple(MSGS), variant="thinking=512")]
    keys = {base.cache_key()} | {v.cache_key() for v in variants}
    assert len(keys) == len(variants) + 1
    assert base.cache_key() == LLMRequest("m", tuple(MSGS)).cache_key()


def test_cached_reruns_cost_nothing(tmp_path):
    cache = ResponseCache(tmp_path / "c.sqlite")
    llm = FakeClient(lambda r: '{"a": 1}', cache=cache, price_in=1.0, price_out=1.0)
    first = llm.complete(MSGS)
    again = llm.complete(MSGS)
    assert not first.cached and again.cached and len(llm.requests) == 1
    u = llm.total_usage()
    assert u.calls == 2 and u.cached_calls == 1
    assert u.cached_input_tokens == first.input_tokens


def test_cache_persists_across_clients(tmp_path):
    path = tmp_path / "c.sqlite"
    FakeClient(lambda r: "x", cache=ResponseCache(path)).complete(MSGS)
    fresh = FakeClient(lambda r: "y", cache=ResponseCache(path))
    assert fresh.complete(MSGS).text == "x" and fresh.requests == []
    assert len(ResponseCache(path)) == 1


def test_changing_backend_settings_never_reuses_old_answers():
    cache = ResponseCache(":memory:")
    FakeClient(lambda r: "old", cache=cache, variant="a").complete(MSGS)
    assert FakeClient(lambda r: "new", cache=cache, variant="b").complete(MSGS).text == "new"


# ------------------------------------------------------------------ cost

def test_cost_counts_uncached_tokens_and_full_cost_counts_all():
    u = Usage(input_tokens=1_000_000, output_tokens=500_000, cached_input_tokens=1_000_000)
    assert u.cost(0.75, 3.75) == pytest.approx(0.75 + 1.875)
    assert u.full_cost(0.75, 3.75) == pytest.approx(1.5 + 1.875)


def test_usage_is_tracked_per_agent():
    llm = FakeClient(lambda r: "{}")
    llm.complete(MSGS, tag="planner")
    llm.complete([user("x")], tag="verifier")
    llm.complete([user("y")], tag="verifier")
    assert llm.usage()["planner"].calls == 1 and llm.usage()["verifier"].calls == 2


# ------------------------------------------------------------------ JSON completion, retries, map

def test_complete_json_retries_once_with_a_reminder():
    replies = iter(["not json", '{"ok": true}'])
    llm = FakeClient(lambda r: next(replies))
    assert llm.complete_json(MSGS) == {"ok": True}
    assert "not valid JSON" in llm.requests[1].messages[-1].content


def test_complete_json_gives_up_after_one_retry():
    with pytest.raises(ValueError):
        FakeClient(lambda r: "never json").complete_json(MSGS)


def test_retryable_errors_are_retried_with_backoff(monkeypatch):
    import counselcopilot.llm.base as base

    sleeps = []
    monkeypatch.setattr(base.time, "sleep", sleeps.append)
    calls = iter([RetryableError("429"), RetryableError("503"), "ok"])

    def flaky(req):
        x = next(calls)
        if isinstance(x, Exception):
            raise x
        return x

    assert FakeClient(flaky).complete(MSGS).text == "ok"
    assert sleeps == [2.0, 4.0]


def test_retries_run_out(monkeypatch):
    import counselcopilot.llm.base as base

    monkeypatch.setattr(base.time, "sleep", lambda s: None)

    def down(req):
        raise RetryableError("503")

    with pytest.raises(RetryableError):
        FakeClient(down, max_retries=2).complete(MSGS)


def test_map_keeps_order_and_works_serially():
    llm = FakeClient()
    assert llm.map(lambda x: x * 2, [3, 1, 2], max_workers=4) == [6, 2, 4]
    assert llm.map(lambda x: x * 2, [3, 1, 2], max_workers=1) == [6, 2, 4]


# ------------------------------------------------------------------ batch mode

def test_batch_mode_queues_misses_and_answers_hits(tmp_path):
    cache = ResponseCache(":memory:")
    q = BatchQueue(tmp_path / "q.jsonl")
    llm = FakeClient(lambda r: "live", cache=cache, batch_queue=q)
    with pytest.raises(PendingBatch):
        llm.complete(MSGS)
    with pytest.raises(PendingBatch):
        llm.complete(MSGS)  # deduplicated
    assert len(q) == 1 and llm.requests == []
    key = LLMRequest("fake", tuple(MSGS)).cache_key()
    cache.put(key, "fake", {"text": "from batch", "model": "fake", "input_tokens": 3, "output_tokens": 1})
    assert llm.complete(MSGS).text == "from batch"


def test_queue_survives_a_restart(tmp_path):
    path = tmp_path / "q.jsonl"
    BatchQueue(path).add("k1", LLMRequest("m", tuple(MSGS)))
    q = BatchQueue(path)
    q.add("k1", LLMRequest("m", tuple(MSGS)))
    assert len(q) == 1 and len(path.read_text().splitlines()) == 1
    row = json.loads(path.read_text())
    assert row["request"]["messages"][0] == {"role": "system", "content": "s"}


def test_map_queues_everything_before_raising(tmp_path):
    q = BatchQueue(tmp_path / "q.jsonl")
    llm = FakeClient(cache=ResponseCache(":memory:"), batch_queue=q)
    with pytest.raises(PendingBatch, match="3 requests queued"):
        llm.map(lambda x: llm.complete([user(str(x))]), [1, 2, 3], max_workers=2)
    assert len(q) == 3


def test_agent_backend_only_answers_from_the_cache():
    with pytest.raises(RuntimeError, match="batch"):
        AgentClient("claude", cache=None).complete(MSGS)


# ------------------------------------------------------------------ backends from config

CONFIG = """
[roles]
backbones = ["llama", "gem-flash"]
compiler = "gem-pro"
evaluator = "gem-pro"

[cache]
path = "{cache}"

[backends.llama]
provider = "openai_compat"
base_url = "http://localhost:8000/v1"
model = "llama-8b"
family = "llama"

[backends.gem-flash]
provider = "fake"
model = "flash"
family = "gemini"

[backends.gem-pro]
provider = "fake"
model = "pro"
family = "gemini"

[backends.qwen]
provider = "fake"
model = "qwen"
family = "qwen"

[backends.agent]
provider = "agent"
model = "claude (agent)"
family = "claude"

[backends.fake]
provider = "fake"
model = "fake"
family = "fake"
"""


@pytest.fixture
def config(tmp_path):
    p = tmp_path / "backends.toml"
    p.write_text(CONFIG.replace("{cache}", str(tmp_path / "cache.sqlite")))
    return p


def test_backends_load_from_config(config):
    llm = load_backend("llama", config)
    assert llm.provider == "openai_compat" and llm.model == "llama-8b" and llm.name == "llama"
    assert load_backend("agent", config).provider == "agent"
    with pytest.raises(KeyError, match="unknown backend"):
        load_backend("gpt", config)


def test_fake_backend_answers_any_schema(config):
    llm = load_backend("fake", config)
    out = llm.complete_json(MSGS, {"type": "object", "properties": {
        "label": {"type": "string", "enum": ["Entailment", "NotMentioned"]}, "ev": {"type": "array"},
        "n": {"type": "number"}, "b": {"type": "boolean"}}})
    assert out == {"label": "Entailment", "ev": [], "n": 0, "b": False}
    assert schema_example({"type": ["string", "null"]}) == ""


def test_batch_queue_is_per_backend(config, tmp_path):
    llm = load_backend("qwen", config, batch_queue=tmp_path / "q.jsonl")
    assert llm.batch_queue.path.name == "q.qwen.jsonl"


def test_backend_settings_are_part_of_the_cache_key(config):
    assert "base_url" in load_backend("llama", config).variant


def test_roles_and_families(config):
    assert roles(config)["backbones"] == ["llama", "gem-flash"]
    assert family("gem-pro", config) == "gemini" and backend_config("llama", config)["model"] == "llama-8b"


def test_data_makers_must_come_from_an_untested_family(config):
    """Proposal §6/§11: packs and labels come from a family no tested system, compiler or judge uses."""
    assert check_data_maker(["qwen", "agent"], config) == []
    problems = check_data_maker(["gem-pro"], config)
    assert len(problems) == 1 and "gemini" in problems[0]
    assert check_data_maker(["fake"], config) == []


# ------------------------------------------------------------------ the project's real config

def test_project_config_backbones_are_llama_then_gemini():
    """Proposal §7: stage 1 on Llama-3.1-8B, stage 2 on Gemini Flash."""
    r = roles()
    assert r["backbones"] == ["llama-vllm", "gemini-flash"]
    assert family("llama-vllm") == "llama" and family("gemini-flash") == "gemini"


def test_project_config_claude_data_makers_are_not_tested_families():
    """Proposal §6: Claude (Sonnet) writes the packs and Claude Haiku cross-checks them."""
    assert check_data_maker(["claude-sonnet-agent", "claude-haiku-agent"]) == []


@pytest.mark.xfail(strict=True, reason="CONFIG MISMATCH: the API fallback labellers in configs/backends.toml include "
                                        "gemini-pro, the compiler/judge and the same family as the gemini-flash "
                                        "backbone, which the proposal's independence rule forbids")
def test_project_config_fallback_data_makers_are_independent():
    r = roles()
    assert check_data_maker([r["pack_generator"], *r["labellers"]]) == []
