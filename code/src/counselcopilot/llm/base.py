"""Backend-neutral LLM client with a response cache and token/cost accounting.

Every agent in the system talks to an `LLMClient`. Swapping Llama (stage 1) for Gemini
(stage 2) is a config change; the rest of the code never sees which backend it is using.

Each response is cached by a hash of the full request (model, messages, sampling settings,
schema, seed), so a re-run after a crash or a scoring fix costs nothing (api_cost_plan.md,
option 2).
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from .cache import ResponseCache


@dataclass(frozen=True)
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


def system(text: str) -> Message:
    return Message("system", text)


def user(text: str) -> Message:
    return Message("user", text)


@dataclass(frozen=True)
class LLMRequest:
    model: str
    messages: tuple[Message, ...]
    temperature: float = 0.0
    max_tokens: int = 512
    json_schema: dict | None = None
    seed: int = 0
    # Backend settings that change answers under the same model name (provider, endpoint,
    # thinking budget, adapter): part of the cache key so changing them never reuses old answers.
    variant: str = ""

    def cache_key(self) -> str:
        payload = {
            "variant": self.variant,
            "model": self.model,
            "messages": [asdict(m) for m in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "json_schema": self.json_schema,
            "seed": self.seed,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cached: bool = False
    latency_s: float = 0.0
    raw: dict = field(default_factory=dict)

    def json(self) -> Any:
        return parse_json_loose(self.text)

    def to_cache(self) -> dict:
        return {"text": self.text, "model": self.model, "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens}


_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def parse_json_loose(text: str) -> Any:
    """Parse JSON from a model reply, tolerating code fences and leading/trailing chatter."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _FENCE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    for open_c, close_c in (("{", "}"), ("[", "]")):
        s, e = text.find(open_c), text.rfind(close_c)
        if s != -1 and e > s:
            try:
                return json.loads(text[s : e + 1])
            except json.JSONDecodeError:
                continue
    raise ValueError(f"no JSON found in model output: {text[:200]!r}")


@dataclass
class Usage:
    calls: int = 0
    cached_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0  # tokens of answers read from the cache (incl. Batch API results)
    cached_output_tokens: int = 0

    def cost(self, price_in: float, price_out: float) -> float:
        """Dollar cost of the *uncached* tokens, prices per million tokens."""
        return self.input_tokens / 1e6 * price_in + self.output_tokens / 1e6 * price_out

    def full_cost(self, price_in: float, price_out: float) -> float:
        """What the run would cost with an empty cache, at list price. Use this to compare
        presets: the cached share depends on which preset ran first."""
        return ((self.input_tokens + self.cached_input_tokens) / 1e6 * price_in
                + (self.output_tokens + self.cached_output_tokens) / 1e6 * price_out)


class PendingBatch(RuntimeError):
    """Raised in batch mode when a request is not cached yet; it has been queued instead."""


class LLMClient(ABC):
    """Base class. Subclasses implement `_call` only.

    Batch mode (review problem 8): with `batch_queue` set, a cache miss is written to the
    queue file and raises PendingBatch instead of calling the API. Runners skip NDAs that
    raise it. Submit the queue as one Batch API job (half price), load the results into the
    cache, and run again: everything cached is free and the next stage of the pipeline is
    queued. A pipeline with N dependent stages takes N batch rounds ("stage-synchronous").
    """

    provider = "base"

    def __init__(
        self,
        model: str,
        *,
        cache: ResponseCache | None = None,
        price_in: float = 0.0,
        price_out: float = 0.0,
        max_retries: int = 4,
        name: str | None = None,
        batch_queue: "BatchQueue | None" = None,
        variant: str = "",
    ):
        self.variant = variant
        self.model = model
        self.name = name or model
        self.cache = cache
        self.price_in = price_in
        self.price_out = price_out
        self.max_retries = max_retries
        self._usage: dict[str, Usage] = defaultdict(Usage)  # by tag (agent name)
        self._lock = threading.Lock()
        self.batch_queue = batch_queue

    @abstractmethod
    def _call(self, req: LLMRequest) -> LLMResponse: ...

    def complete(
        self,
        messages: list[Message],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
        json_schema: dict | None = None,
        seed: int = 0,
        tag: str = "default",
    ) -> LLMResponse:
        req = LLMRequest(self.model, tuple(messages), temperature, max_tokens, json_schema, seed, self.variant)
        key = req.cache_key()
        if self.cache is not None:
            hit = self.cache.get(key)
            if hit is not None:
                resp = LLMResponse(**hit, cached=True)
                self._record(tag, resp)
                return resp
        if self.batch_queue is not None:
            self.batch_queue.add(key, req)
            raise PendingBatch(key)
        resp = self._with_retries(req)
        if self.cache is not None:
            self.cache.put(key, self.model, resp.to_cache())
        self._record(tag, resp)
        return resp

    def complete_json(self, messages: list[Message], schema: dict | None = None, **kw) -> Any:
        """Complete and parse JSON. Retries once with a reminder if the output is not JSON."""
        resp = self.complete(messages, json_schema=schema, **kw)
        try:
            return resp.json()
        except ValueError:
            retry = list(messages) + [Message("assistant", resp.text),
                                      user("That was not valid JSON. Reply with the JSON object only.")]
            return self.complete(retry, json_schema=schema, **kw).json()

    def map(self, fn: Callable[[Any], Any], items: list[Any], max_workers: int = 8) -> list[Any]:
        """Run `fn` over items concurrently. vLLM batches concurrent requests, so this is
        much faster than a loop; keep max_workers low for rate-limited APIs."""
        pending: list[PendingBatch] = []

        def safe(x):
            try:
                return fn(x)
            except PendingBatch as e:  # keep queueing the other items, re-raise at the end
                pending.append(e)
                return None

        if max_workers <= 1:
            out = [safe(x) for x in items]
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as ex:
                out = list(ex.map(safe, items))
        if pending:
            raise PendingBatch(f"{len(pending)} requests queued")
        return out

    def _with_retries(self, req: LLMRequest) -> LLMResponse:
        delay = 2.0
        for attempt in range(self.max_retries + 1):
            try:
                t0 = time.perf_counter()
                resp = self._call(req)
                resp.latency_s = time.perf_counter() - t0
                return resp
            except RetryableError:
                if attempt == self.max_retries:
                    raise
                time.sleep(delay)
                delay *= 2
        raise AssertionError("unreachable")

    def _record(self, tag: str, resp: LLMResponse) -> None:
        with self._lock:
            u = self._usage[tag]
            u.calls += 1
            if resp.cached:
                u.cached_calls += 1
                u.cached_input_tokens += resp.input_tokens
                u.cached_output_tokens += resp.output_tokens
            else:
                u.input_tokens += resp.input_tokens
                u.output_tokens += resp.output_tokens

    def usage(self) -> dict[str, Usage]:
        with self._lock:
            return dict(self._usage)

    def total_usage(self) -> Usage:
        t = Usage()
        for u in self.usage().values():
            t.calls += u.calls
            t.cached_calls += u.cached_calls
            t.input_tokens += u.input_tokens
            t.output_tokens += u.output_tokens
            t.cached_input_tokens += u.cached_input_tokens
            t.cached_output_tokens += u.cached_output_tokens
        return t

    def cost(self) -> float:
        return self.total_usage().cost(self.price_in, self.price_out)


class BatchQueue:
    """Append-only JSONL of uncached requests: {"key", "request"} per line, deduplicated."""

    def __init__(self, path):
        from pathlib import Path

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._keys: set[str] = set()
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    self._keys.add(json.loads(line)["key"])

    def add(self, key: str, req: LLMRequest) -> None:
        with self._lock:
            if key in self._keys:
                return
            self._keys.add(key)
            with self.path.open("a") as f:
                f.write(json.dumps({"key": key, "request": {
                    "model": req.model, "messages": [asdict(m) for m in req.messages],
                    "temperature": req.temperature, "max_tokens": req.max_tokens,
                    "json_schema": req.json_schema, "seed": req.seed}}) + "\n")

    def __len__(self) -> int:
        return len(self._keys)


class RetryableError(RuntimeError):
    """Rate limits, timeouts and 5xx errors."""
