#!/usr/bin/env bash
# Every ablation study in docs/design/ablation-studies.md, in one command.
#
#   ollama pull llama3.1:8b && ollama pull qwen3:14b      # local models
#   OLLAMA_CONTEXT_LENGTH=16384 ollama serve              # 16k context: Ollama's default silently cuts prompts
#   export GEMINI_API_KEY=...                             # compiler, RQ2 judge, stage 2
#   scripts/run_ablations.sh                              # everything
#   STAGES="rq1" LIMIT=20 scripts/run_ablations.sh        # a quick first pass
#
# Re-running is cheap: every model answer is cached in data/cache/llm.sqlite, so a crashed or
# interrupted run picks up where it stopped. Results: runs/ablations/ABLATIONS.md.
#
# Settings (environment variables):
#   LOCAL=llama-ollama     stage-1 backbone (every ablation)
#   OTHER=qwen-ollama      "attacker on a different model" (RQ2)
#   REMOTE=gemini-flash    stage-2 backbone (headline systems + two ablations)
#   COMPILER=gemini-pro    policy prose -> requirement cards, once per company
#   JUDGE=gemini-pro       RQ2 independent evaluator (never a repair system's model)
#   TUNED=                 e.g. llama-tuned: adds the "tuned checker" ablation
#   LIMIT=                 NDAs per local RQ1 run (empty = all 123 test NDAs)
#   REMOTE_LIMIT=$LIMIT    NDAs per Gemini Flash RQ1 run (cost: about $0.25 per NDA for the stage-2 set)
#   RQ2_LIMIT=40           NDAs for RQ2 (proposal: 40)
#   SEEDS="0"              planted-defect / deal draws, e.g. "0 1 2" for the proposal's 3 draws
#   WORKERS=2              parallel requests (Ollama: 1-4; Gemini: 16)
#   ORACLE=                1 = give the reviewer the gold rule lists instead of compiled cards
#   STAGES="compile rq1 remote rq2 cascade report"
set -euo pipefail
cd "$(dirname "$0")/.."

LOCAL=${LOCAL:-llama-ollama}; OTHER=${OTHER:-qwen-ollama}; REMOTE=${REMOTE:-gemini-flash}
COMPILER=${COMPILER:-gemini-pro}; JUDGE=${JUDGE:-gemini-pro}; TUNED=${TUNED:-}
LIMIT=${LIMIT:-}; REMOTE_LIMIT=${REMOTE_LIMIT:-$LIMIT}; RQ2_LIMIT=${RQ2_LIMIT:-40}; SEEDS=${SEEDS:-0}; WORKERS=${WORKERS:-2}
STAGES=${STAGES:-compile rq1 remote rq2 cascade report}
CC=${CC:-python -m counselcopilot.cli}
OUT=runs/ablations
mkdir -p "$OUT" packs/compiled
has() { [[ " $STAGES " == *" $1 "* ]]; }
lim() { [ -n "$1" ] && echo "--limit $1" || true; }

declare -A COMPANY=([saas]="Northwind Cloud, Inc." [hospital]="Bayview Health Partners"
                    [manufacturer]="Keystone Precision Manufacturing, Inc.")
LAW=packs/law/us_law_pack.yaml
LABELS=data/labels/ndas_auto.yaml

# ---------------------------------------------------------------- preflight
need=()
has compile && [ -z "${ORACLE:-}" ] && need+=("$COMPILER")
has remote && need+=("$REMOTE")
has rq2 && need+=("$JUDGE")
for b in "${need[@]}"; do
  if [[ $b == gemini* ]] && [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "GEMINI_API_KEY is not set (needed for $b); export it, or see docs/guides/run-ablations-ollama.md for the Ollama-only setup"; exit 1
  fi
done
if [[ "$LOCAL $OTHER" == *ollama* ]] && { has rq1 || has rq2; }; then
  curl -sf localhost:11434/api/tags > /dev/null || { echo "Ollama is not answering on localhost:11434: run 'OLLAMA_CONTEXT_LENGTH=16384 ollama serve'"; exit 1; }
fi
$CC data download >/dev/null

# ---------------------------------------------------------------- 0. policy compiler (once)
PACKS=() GOLD=() GOLDS=()
for c in saas hospital manufacturer; do
  GOLDS+=(--pack "packs/policynda/$c/gold_rules.yaml")
  if [ -n "${ORACLE:-}" ]; then PACKS+=(--pack "packs/policynda/$c/gold_rules.yaml"); continue; fi
  if has compile && [ ! -f "packs/compiled/$c.yaml" ]; then
    echo "== compile $c ($COMPILER)"
    $CC compile --backend "$COMPILER" --workers "$WORKERS" --policies "packs/policynda/$c/policies" \
      --company "${COMPANY[$c]}" --gold "packs/policynda/$c/gold_rules.yaml" \
      --out "packs/compiled/$c.yaml" > "$OUT/compile_$c.json"
  fi
  PACKS+=(--pack "packs/compiled/$c.yaml"); GOLD+=(--gold-pack "packs/policynda/$c/gold_rules.yaml")
done

# planted defects and deals per seed (seed 0 ships in data/planted/)
for s in $SEEDS; do
  if [ ! -f "data/planted/test_seed$s.json" ]; then
    echo "== plant seed $s"
    $CC plant "${GOLDS[@]}" --law-pack "$LAW" --split test --labels "$LABELS" --allow-auto --seed "$s" \
      --out "data/planted/test_seed$s.json"
  fi
done

# run one RQ1 system; prints the run folder
rq1() {  # rq1 NAME BACKEND SEED extra-args...
  local name=$1 backend=$2 seed=$3; shift 3
  local n=$LIMIT; [ "$backend" = "$REMOTE" ] && [ "$REMOTE" != "$LOCAL" ] && n=$REMOTE_LIMIT
  echo "== rq1 $name ($backend, seed $seed)" >&2
  $CC rq1 --backend "$backend" --workers "$WORKERS" $(lim "$n") --split test "${PACKS[@]}" "${GOLD[@]}" \
    --law-pack "$LAW" --planted "data/planted/test_seed$seed.json" --labels "$LABELS" --allow-auto \
    --hide-facts --scripted-precedents 30 "$@" > "$OUT/rq1_${name}_${backend}_s$seed.json"
  python -c "import json,sys;print(json.load(open(sys.argv[1]))['out_dir'])" "$OUT/rq1_${name}_${backend}_s$seed.json"
}

ABLATIONS="full no_reverse no_filter no_frames no_verifier fixed_pipeline no_xref no_memory no_tool_agent structured_applicability tool_errors"

# ---------------------------------------------------------------- 1. RQ1 ablations on the local model
if has rq1; then
  for s in $SEEDS; do
    : > "$OUT/runs_local_s$s.txt"
    for a in $ABLATIONS; do
      echo "$a=$(rq1 "$a" "$LOCAL" "$s" --system pipeline --ablation "$a")" >> "$OUT/runs_local_s$s.txt"
    done
    for p in full exhaustive_filtered; do  # reviewer alone and B4+filter (H1 equivalence)
      echo "reviewer:$p=$(rq1 "reviewer_$p" "$LOCAL" "$s" --system reviewer --preset "$p")" >> "$OUT/runs_local_s$s.txt"
    done
    for b in b2 b2_checklist b3; do  # baselines that fit an 8B context
      echo "$b=$(rq1 "$b" "$LOCAL" "$s" --system "$b")" >> "$OUT/runs_local_s$s.txt"
    done
    if [ -n "$TUNED" ]; then
      echo "tuned_checker=$(rq1 tuned_checker "$LOCAL" "$s" --system pipeline --ablation full --checker-backend "$TUNED")" \
        >> "$OUT/runs_local_s$s.txt"
    fi
  done
fi

# ---------------------------------------------------------------- 2. stage 2: confirm on Gemini Flash
if has remote; then
  s=${SEEDS%% *}
  : > "$OUT/runs_remote.txt"
  for a in full no_reverse no_filter; do
    echo "$a=$(rq1 "$a" "$REMOTE" "$s" --system pipeline --ablation "$a")" >> "$OUT/runs_remote.txt"
  done
  echo "reviewer:full=$(rq1 reviewer_full "$REMOTE" "$s" --system reviewer --preset full)" >> "$OUT/runs_remote.txt"
  echo "reviewer:exhaustive_filtered=$(rq1 reviewer_exhaustive_filtered "$REMOTE" "$s" --system reviewer --preset exhaustive_filtered)" >> "$OUT/runs_remote.txt"
  for b in b1 b2 b2_checklist; do  # B1 long context needs Gemini's window
    echo "$b=$(rq1 "$b" "$REMOTE" "$s" --system "$b")" >> "$OUT/runs_remote.txt"
  done
fi

# ---------------------------------------------------------------- 3. RQ2 loop ablations
if has rq2; then
  s=${SEEDS%% *}
  : > "$OUT/runs_rq2.txt"
  rq2() {  # rq2 NAME extra-args...
    local name=$1; shift
    echo "== rq2 $name" >&2
    $CC rq2 --backend "$LOCAL" --workers "$WORKERS" "${PACKS[@]}" "${GOLD[@]}" --law-pack "$LAW" \
      --planted "data/planted/test_seed$s.json" --labels "$LABELS" --allow-auto --limit "$RQ2_LIMIT" \
      --evaluator-backend "$JUDGE" --noise-floor 30 "$@" > "$OUT/rq2_$name.json"
    python -c "import json,sys;print(json.load(open(sys.argv[1]))['out_dir'])" "$OUT/rq2_$name.json"
  }
  rq2 main --systems loop r1 r1_attacker r2 loop_no_attacker loop_no_regression loop_1_round >> "$OUT/runs_rq2.txt"
  if [ "$OTHER" = "$JUDGE" ]; then  # the judge must stay independent of every repair system
    echo "== skip rq2 other_attacker: OTHER=$OTHER is also the judge" >&2
  else
    rq2 other_attacker --systems loop --attacker-backend "$OTHER" >> "$OUT/runs_rq2.txt"
  fi
fi

# ---------------------------------------------------------------- 4. local-first cascade (offline, from runs)
if has cascade && [ -f "$OUT/runs_remote.txt" ] && [ -f "$OUT/runs_local_s${SEEDS%% *}.txt" ]; then
  get() { grep "^$1=" "$2" | head -1 | cut -d= -f2; }
  L=$(get reviewer:full "$OUT/runs_local_s${SEEDS%% *}.txt"); R=$(get reviewer:full "$OUT/runs_remote.txt")
  echo "== cascade"
  $CC cascade "$L" "$R" "${PACKS[@]}" "${GOLD[@]}" --law-pack "$LAW" > "$OUT/cascade.json"
  $CC cascade "$L" "$R" "${PACKS[@]}" "${GOLD[@]}" --law-pack "$LAW" --high-severity > "$OUT/cascade_high_severity.json"
fi

# ---------------------------------------------------------------- 5. report
if has report; then
  s0="$OUT/runs_local_s${SEEDS%% *}.txt"
  ARGS=(); [ -f "$s0" ] && mapfile -t ARGS < "$s0"
  RQ2=(); [ -f "$OUT/runs_rq2.txt" ] && mapfile -t RQ2 < "$OUT/runs_rq2.txt"
  $CC ablations "${ARGS[@]}" --rq2 "${RQ2[@]}" --out "$OUT/ABLATIONS.md" > /dev/null
  if [ -f "$OUT/runs_remote.txt" ]; then
    mapfile -t REM < "$OUT/runs_remote.txt"
    $CC ablations "${REM[@]}" --out "$OUT/ABLATIONS_remote.md" > /dev/null
  fi
  echo "== done: $OUT/ABLATIONS.md"
fi
