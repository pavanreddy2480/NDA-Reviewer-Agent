"""Gemini Batch API helpers for batch mode (see LLMClient docstring).

    cc rq1 ... --backend gemini-flash --batch-queue runs/queue.jsonl   # round 1: queues stage 1
    cc batch submit --backend gemini-flash --queue runs/queue.jsonl     # prints a job name
    cc batch collect --backend gemini-flash --job <name>                # loads results into the cache
    (repeat the first command for the next stage, until nothing is queued)

Claude agents instead of an API (`provider = "agent"` backends):
    cc rq1 ... --backend claude-sonnet-agent --batch-queue runs/queue.jsonl
    cc batch export --backend claude-sonnet-agent --queue runs/queue.claude-sonnet-agent.jsonl --out runs/agent_round1
    (agents write answers/<shard>.jsonl, one {"key", "text"} per request)
    cc batch load --backend claude-sonnet-agent --answers runs/agent_round1/answers

Gemini Batch API: not yet run against the live API (no key in the build container): check field names against
the google-genai docs on the first real job, with a 5-NDA smoke test.
"""

from __future__ import annotations

import json
from pathlib import Path

from .cache import ResponseCache


def to_gemini_jsonl(queue_path: str | Path, out_path: str | Path, thinking_budget: int | None = None) -> int:
    n = 0
    with Path(out_path).open("w") as out:
        for line in Path(queue_path).read_text().splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            r = item["request"]
            sys_text = "\n\n".join(m["content"] for m in r["messages"] if m["role"] == "system")
            contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                        for m in r["messages"] if m["role"] != "system"]
            cfg = {"temperature": r["temperature"], "maxOutputTokens": r["max_tokens"] + (thinking_budget or 0),
                   "seed": r["seed"]}
            if r["json_schema"] is not None:
                cfg.update(responseMimeType="application/json", responseJsonSchema=r["json_schema"])
            if thinking_budget is not None:
                cfg["thinkingConfig"] = {"thinkingBudget": thinking_budget}
            req = {"contents": contents, "generationConfig": cfg}
            if sys_text:
                req["systemInstruction"] = {"parts": [{"text": sys_text}]}
            out.write(json.dumps({"key": item["key"], "request": req}) + "\n")
            n += 1
    return n


def submit(queue_path: str | Path, model: str, thinking_budget: int | None = None) -> str:  # pragma: no cover
    from google import genai

    client = genai.Client()
    jsonl = Path(queue_path).with_suffix(".gemini.jsonl")
    to_gemini_jsonl(queue_path, jsonl, thinking_budget)
    uploaded = client.files.upload(file=str(jsonl), config={"mime_type": "jsonl"})
    job = client.batches.create(model=model, src=uploaded.name)
    return job.name


def collect(job_name: str, model: str, cache: ResponseCache) -> dict:  # pragma: no cover
    from google import genai

    client = genai.Client()
    job = client.batches.get(name=job_name)
    state = str(job.state)
    if "SUCCEEDED" not in state:
        return {"state": state, "loaded": 0}
    raw = client.files.download(file=job.dest.file_name).decode()
    return {"state": state, "loaded": load_results(raw.splitlines(), model, cache)}


def load_results(lines: list[str], model: str, cache: ResponseCache) -> int:
    """Load Gemini batch output lines ({"key", "response"}) into the response cache."""
    n = 0
    for line in lines:
        if not line.strip():
            continue
        item = json.loads(line)
        resp = item.get("response")
        if not resp:
            continue
        parts = resp["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
        um = resp.get("usageMetadata", {})
        cache.put(item["key"], model, {
            "text": text, "model": model, "input_tokens": um.get("promptTokenCount", 0),
            "output_tokens": um.get("candidatesTokenCount", 0) + um.get("thoughtsTokenCount", 0)})
        n += 1
    return n


def export_shards(queue_path: str | Path, out_dir: str | Path, cache: ResponseCache, per_shard: int = 60,
                  seed: int = 0) -> dict:
    """Write uncached queued requests as shards for agents: one JSON object per line with key, system,
    user and schema. Requests are shuffled so neighbouring lines come from different NDAs."""
    import random

    items = []
    for line in Path(queue_path).read_text().splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if cache.get(item["key"]) is not None:
            continue
        r = item["request"]
        items.append({"key": item["key"],
                      "system": "\n\n".join(m["content"] for m in r["messages"] if m["role"] == "system"),
                      "messages": [m for m in r["messages"] if m["role"] != "system"],
                      "schema": r["json_schema"]})
    random.Random(seed).shuffle(items)
    out = Path(out_dir)
    (out / "answers").mkdir(parents=True, exist_ok=True)
    shards = []
    for i in range(0, len(items), per_shard):
        f = out / f"shard_{i // per_shard:03d}.jsonl"
        f.write_text("".join(json.dumps(x) + "\n" for x in items[i:i + per_shard]))
        shards.append({"file": str(f), "n": len(items[i:i + per_shard]),
                       "chars": sum(len(json.dumps(x)) for x in items[i:i + per_shard])})
    return {"requests": len(items), "shards": shards}


def load_answers(answers_dir: str | Path, queue_path: str | Path, model: str, cache: ResponseCache) -> dict:
    """Load agents' answers ({"key", "text"} per line) into the cache. Token counts are estimated
    as characters / 4, since agents report none."""
    reqs = {}
    for line in Path(queue_path).read_text().splitlines():
        if line.strip():
            item = json.loads(line)
            reqs[item["key"]] = item["request"]
    loaded, unknown, bad = 0, 0, 0
    for f in sorted(Path(answers_dir).glob("*.jsonl")):
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            try:
                a = json.loads(line)
            except json.JSONDecodeError:
                bad += 1
                continue
            r = reqs.get(a.get("key"))
            if r is None:
                unknown += 1
                continue
            text = a["text"] if isinstance(a["text"], str) else json.dumps(a["text"])
            n_in = sum(len(m["content"]) for m in r["messages"]) // 4
            cache.put(a["key"], model, {"text": text, "model": model, "input_tokens": n_in,
                                        "output_tokens": len(text) // 4})
            loaded += 1
    missing = sum(1 for k in reqs if cache.get(k) is None)
    return {"loaded": loaded, "unknown_keys": unknown, "bad_lines": bad, "still_missing": missing}
