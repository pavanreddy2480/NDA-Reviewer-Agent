"""Concrete LLM backends.

- OpenAICompatClient: any server with an OpenAI-style /v1/chat/completions endpoint.
  That covers Ollama (laptop, small tests) and vLLM (Kaggle, full stage-1 runs), and hosted
  Llama endpoints (fallback if GPU quota runs out).
- GeminiClient: Google Gemini via the google-genai SDK (stage 2). Install with
  `pip install -e .[gemini]` and set GEMINI_API_KEY.
- AgentClient: Claude answered by agents in the project thread, not an API. Only usable in batch
  mode: `cc batch export` writes the queue as shards, agents answer them, `cc batch load` fills the cache.
- FakeClient: deterministic stand-in for tests and dry runs; no network.
"""

from __future__ import annotations

import json
import os
from typing import Callable

import httpx

from .base import LLMClient, LLMRequest, LLMResponse, RetryableError


class OpenAICompatClient(LLMClient):
    provider = "openai_compat"

    def __init__(self, model: str, base_url: str, api_key: str | None = None,
                 timeout: float = 300.0, structured: str = "json_schema", **kw):
        super().__init__(model, **kw)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "none")
        # "json_schema" (vLLM >= 0.6, Ollama >= 0.5), "json_object", or "none"
        self.structured = structured
        self._http = httpx.Client(timeout=timeout)

    def _call(self, req: LLMRequest) -> LLMResponse:
        body: dict = {
            "model": req.model,
            "messages": [{"role": m.role, "content": m.content} for m in req.messages],
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
            "seed": req.seed,
        }
        if req.json_schema is not None and self.structured == "json_schema":
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "output", "schema": req.json_schema, "strict": True},
            }
        elif req.json_schema is not None and self.structured == "json_object":
            body["response_format"] = {"type": "json_object"}
        try:
            r = self._http.post(f"{self.base_url}/chat/completions", json=body,
                                headers={"Authorization": f"Bearer {self.api_key}"})
        except (httpx.TimeoutException, httpx.TransportError) as e:
            raise RetryableError(str(e)) from e
        if r.status_code == 429 or r.status_code >= 500:
            raise RetryableError(f"{r.status_code}: {r.text[:200]}")
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage") or {}
        return LLMResponse(
            text=data["choices"][0]["message"]["content"] or "",
            model=req.model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )


class GeminiClient(LLMClient):
    provider = "gemini"

    def __init__(self, model: str, api_key: str | None = None, thinking_budget: int | None = None, **kw):
        super().__init__(model, **kw)
        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise ImportError("pip install -e '.[gemini]' to use the Gemini backend") from e
        self._types = types
        self._client = genai.Client(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        self.thinking_budget = thinking_budget

    def _call(self, req: LLMRequest) -> LLMResponse:  # pragma: no cover - needs network
        t = self._types
        sys_text = "\n\n".join(m.content for m in req.messages if m.role == "system") or None
        contents = [
            t.Content(role="model" if m.role == "assistant" else "user", parts=[t.Part(text=m.content)])
            for m in req.messages if m.role != "system"
        ]
        # Thinking tokens share the output limit, so add the thinking budget to it: otherwise a
        # 300-token check with a 512-token budget can end before the JSON answer (audit 22 Oct).
        cfg = dict(system_instruction=sys_text, temperature=req.temperature,
                   max_output_tokens=req.max_tokens + (self.thinking_budget or 0), seed=req.seed)
        if req.json_schema is not None:
            cfg.update(response_mime_type="application/json", response_json_schema=req.json_schema)
        if self.thinking_budget is not None:
            cfg["thinking_config"] = t.ThinkingConfig(thinking_budget=self.thinking_budget)
        try:
            resp = self._client.models.generate_content(
                model=req.model, contents=contents, config=t.GenerateContentConfig(**cfg))
        except Exception as e:
            msg = str(e)
            if any(code in msg for code in ("429", "500", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE")):
                raise RetryableError(msg) from e
            raise
        um = resp.usage_metadata
        return LLMResponse(
            text=resp.text or "",
            model=req.model,
            input_tokens=getattr(um, "prompt_token_count", 0) or 0,
            output_tokens=(getattr(um, "candidates_token_count", 0) or 0)
            + (getattr(um, "thoughts_token_count", 0) or 0),
        )


class FakeClient(LLMClient):
    """Returns `responder(request)`; the default replies with a fixed JSON object."""

    provider = "fake"

    def __init__(self, responder: Callable[[LLMRequest], str] | None = None, model: str = "fake", **kw):
        super().__init__(model, **kw)
        self.responder = responder or (lambda req: json.dumps({"ok": True}))
        self.requests: list[LLMRequest] = []

    def _call(self, req: LLMRequest) -> LLMResponse:
        self.requests.append(req)
        text = self.responder(req)
        n_in = sum(len(m.content) for m in req.messages) // 4
        return LLMResponse(text=text, model=req.model, input_tokens=n_in, output_tokens=len(text) // 4)


class AgentClient(LLMClient):
    """Answers come only from the cache, filled by `cc batch load` from agents' answer files."""

    provider = "agent"

    def _call(self, req: LLMRequest) -> LLMResponse:
        raise RuntimeError(f"{self.name} is answered by Claude agents: run with --batch-queue, then "
                           "`cc batch export`, have agents answer the shards, and `cc batch load`")
