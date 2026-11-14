# Running the ablation studies with Ollama

Step by step for `scripts/run_ablations.sh` on your own machine. What each ablation means is
in [the design](../design/ablation-studies.md).

## 1. One-time setup

```bash
git clone https://github.com/pavanreddy2480/NDA-Reviewer-Agent.git && cd NDA-Reviewer-Agent
git checkout claude/ablation-studies
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev,gemini]'          # drop ",gemini" for the Ollama-only setup
pytest -q                               # 522 passed, 4 xfailed

ollama pull llama3.1:8b                 # the system under test (about 5 GB)
ollama pull qwen3:14b                   # other attacker, and the judge in the Ollama-only setup (about 9 GB)
```

Start Ollama with a 16k context, in its own terminal. **This is required:** Ollama's default
context (2k–4k) cuts long prompts without an error, and the results would be wrong.

```bash
OLLAMA_CONTEXT_LENGTH=16384 OLLAMA_NUM_PARALLEL=2 ollama serve
```

If Ollama already runs as a background app, quit it first, or set the variable for the app
(macOS: `launchctl setenv OLLAMA_CONTEXT_LENGTH 16384`, then restart Ollama).

Check that it answers: `curl localhost:11434/api/tags`.

## 2. Pick a setup

**A. Ollama + Gemini (the proposal's plan).** Llama runs every ablation; Gemini Pro compiles the
policies and judges RQ2; Gemini Flash confirms the key ablations.

```bash
export GEMINI_API_KEY=...               # never commit it
```

**B. Ollama only (no API cost).** Qwen3-14B compiles the policies and judges RQ2 (a different
model family from Llama, so the judge stays independent). There is no Gemini stage.

```bash
export COMPILER=qwen-ollama JUDGE=qwen-ollama OTHER=qwen-ollama STAGES="compile rq1 rq2 report"
```

## 3. Run, in passes

Start small to check that everything works, then grow. Every answer is cached in
`data/cache/llm.sqlite`, so the bigger passes reuse the smaller ones, and a stopped run picks
up where it stopped. Just run the same command again.

```bash
# pass 1: 5 NDAs, RQ1 only, roughly an hour. Check runs/ablations/ABLATIONS.md looks sane
STAGES="compile rq1 report" LIMIT=5 scripts/run_ablations.sh

# pass 2: 40 NDAs, RQ1 and RQ2, roughly 6-10 h (overnight)
STAGES="compile rq1 rq2 report" LIMIT=40 RQ2_LIMIT=20 scripts/run_ablations.sh

# pass 3 (setup A): Gemini confirmation and the cascade
STAGES="remote cascade report" LIMIT=40 WORKERS=8 scripts/run_ablations.sh

# full: all 123 NDAs and 3 seeds, as in the proposal
SEEDS="0 1 2" scripts/run_ablations.sh
```

Useful settings: `WORKERS` (parallel requests; match `OLLAMA_NUM_PARALLEL`, 2 on a 16 GB GPU or
Mac), `ORACLE=1` (skip the compiler and use the gold rule lists, an upper bound only),
`TUNED=llama-tuned` (adds the fine-tuned checker ablation, see
[qlora-kaggle.md](qlora-kaggle.md)). All settings are listed at the top of the script.

## 4. What you get

| File | What |
|---|---|
| `runs/ablations/ABLATIONS.md` | The main table: every ablation vs the full system on Llama (ΔF1 with 95% CI, Holm-corrected p, omission recall, false alarms, tokens), and the RQ2 loop ablations |
| `runs/ablations/ABLATIONS_remote.md` | The same on Gemini Flash (setup A) |
| `runs/ablations/cascade*.json` | Cascade curve and the chosen threshold |
| `runs/ablations/compile_*.json` | Policy compiler precision and recall per company |
| `runs/<time>-rq1-…/`, `runs/<time>-rq2-…/` | Each run's metrics.json and per-NDA rows |

Send back `ABLATIONS.md` (and `ABLATIONS_remote.md`, `cascade.json`) for the write-up. The
`runs/` folders are git-ignored; zip them if someone needs the per-NDA rows.

## 5. If something goes wrong

| Symptom | Fix |
|---|---|
| `Ollama is not answering on localhost:11434` | Start `ollama serve` (step 1) |
| `GEMINI_API_KEY is not set` | Export it, or use setup B |
| Many `check_errors` in a run's metrics.json, or JSON parse errors | The model's answer was cut: check `OLLAMA_CONTEXT_LENGTH=16384`; lower `WORKERS` if the machine runs out of memory |
| Requests time out | Lower `WORKERS`; the client waits 300 s per request |
| Qwen3 answers fail to parse (setup B) | `ollama pull qwen2.5:14b` and use `COMPILER=qwen25-ollama JUDGE=qwen25-ollama OTHER=qwen25-ollama` |
| `skip rq2 other_attacker` | Expected in setup B: the other attacker would be the judge's model, so that one run is skipped |
| A run crashed half-way | Run the same command again; cached answers are reused |
| `ΔF1` is exactly 0 with p = 1 for an ablation | That component made no difference on these NDAs. Report it as "no measurable effect"; it is a result, not a bug |
