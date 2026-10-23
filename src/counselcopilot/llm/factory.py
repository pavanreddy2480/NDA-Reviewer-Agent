"""Build an LLM client from configs/backends.toml."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from .backends import AgentClient, FakeClient, GeminiClient, OpenAICompatClient
from .base import BatchQueue, LLMClient, LLMRequest
from .cache import ResponseCache

DEFAULT_CONFIG = Path(__file__).resolve().parents[3] / "configs" / "backends.toml"


def schema_example(schema: dict) -> Any:
    """Smallest value that matches a JSON schema (first enum value, empty arrays, etc.)."""
    if "enum" in schema:
        return schema["enum"][0]
    t = schema.get("type")
    if isinstance(t, list):
        t = t[0]
    if t == "object":
        return {k: schema_example(v) for k, v in schema.get("properties", {}).items()}
    if t == "array":
        return []
    if t == "string":
        return ""
    if t in ("integer", "number"):
        return 0
    if t == "boolean":
        return False
    return None


def _fake_responder(req: LLMRequest) -> str:
    if req.json_schema is not None:
        return json.dumps(schema_example(req.json_schema))
    return "{}"


def backend_config(name: str, config_path: str | Path | None = None) -> dict:
    cfg = tomllib.loads(Path(config_path or DEFAULT_CONFIG).read_text())
    return {**cfg["backends"][name], "cache_path": cfg.get("cache", {}).get("path", "data/cache/llm.sqlite")}


def roles(config_path: str | Path | None = None) -> dict:
    return tomllib.loads(Path(config_path or DEFAULT_CONFIG).read_text()).get("roles", {})


def family(name: str, config_path: str | Path | None = None) -> str:
    cfg = tomllib.loads(Path(config_path or DEFAULT_CONFIG).read_text())
    b = cfg["backends"].get(name, {})
    return b.get("family", b.get("model", name))


def check_data_maker(names: list[str], config_path: str | Path | None = None) -> list[str]:
    """Problems if a backend that writes benchmark data shares a family with a backbone, the compiler
    or the evaluator ([roles] in backends.toml). Fake backends are exempt (tests)."""
    r = roles(config_path)
    graded = list(r.get("backbones", [])) + [x for x in (r.get("compiler"), r.get("evaluator")) if x]
    used = {family(g, config_path): g for g in graded}
    out = []
    for n in names:
        f = family(n, config_path)
        if f != "fake" and f in used:
            out.append(f"{n} is in the {f} family, like {used[f]}; benchmark data would favour that system")
    return out


def load_backend(name: str, config_path: str | Path | None = None, use_cache: bool = True,
                 batch_queue: str | Path | None = None) -> LLMClient:
    cfg = tomllib.loads(Path(config_path or DEFAULT_CONFIG).read_text())
    if name not in cfg["backends"]:
        raise KeyError(f"unknown backend {name!r}; choose from {sorted(cfg['backends'])}")
    b = dict(cfg["backends"][name])
    provider = b.pop("provider")
    cache = ResponseCache(cfg.get("cache", {}).get("path", "data/cache/llm.sqlite")) if use_cache else None
    if batch_queue:  # one queue per backend: a Batch job is sent to one model (batch submit --backend)
        q = Path(batch_queue)
        batch_queue = q.with_name(f"{q.stem}.{name}{q.suffix or '.jsonl'}")
    price_in, price_out = b.pop("price_in", 0.0), b.pop("price_out", 0.0)
    b.pop("family", None)
    variant = json.dumps({"provider": provider, **{k: v for k, v in b.items() if k != "model"}}, sort_keys=True)
    common = dict(cache=cache, price_in=price_in, price_out=price_out, name=name, variant=variant,
                  batch_queue=BatchQueue(batch_queue) if batch_queue else None)
    model = b.pop("model")
    if provider == "openai_compat":
        return OpenAICompatClient(model, **b, **common)
    if provider == "gemini":
        return GeminiClient(model, **b, **common)
    if provider == "agent":
        return AgentClient(model, **common)
    if provider == "fake":
        common["cache"] = None
        return FakeClient(_fake_responder, model=model, **{k: v for k, v in common.items() if k != "cache"})
    raise ValueError(f"unknown provider {provider!r}")
