#!/usr/bin/env bash
# RQ1 pilot with Claude (agents) as the system under test: 20 planted test NDAs, three presets,
# deal facts hidden. Step 1 compiles each company's prose policies into requirement cards
# (cc compile); step 2 reviews with those cards and scores them against the gold rule lists
# (--gold-pack), which the system never sees. Run it, answer the exported shards with agents,
# `cc batch load`, run it again, until it reports nothing pending. Then the runs/ folders hold
# the metrics, and runs/pilot/compile_*.json the compiler's precision and recall.
# ORACLE=1 skips the compiler and hands the reviewer the gold rules (an upper bound only).
set -e
B=${BACKEND:-claude-sonnet-agent}
N=${LIMIT:-20}
Q=runs/pilot/queue.jsonl
mkdir -p runs/pilot packs/compiled
declare -A COMPANY=([saas]="Northwind Cloud, Inc." [hospital]="Bayview Health Partners"
                    [manufacturer]="Keystone Precision Manufacturing, Inc.")
PACKS=() GOLD=()
for c in saas hospital manufacturer; do
  GOLD+=(--gold-pack "packs/policynda/$c/gold_rules.yaml")
  if [ -n "$ORACLE" ]; then
    PACKS+=(--pack "packs/policynda/$c/gold_rules.yaml")
    continue
  fi
  if [ ! -f "packs/compiled/$c.yaml" ]; then
    cc compile --backend "$B" --batch-queue "$Q" --workers 4 --policies "packs/policynda/$c/policies" \
      --company "${COMPANY[$c]}" --gold "packs/policynda/$c/gold_rules.yaml" --out "packs/compiled/$c.yaml" \
      > "runs/pilot/compile_$c.json"
  fi
  PACKS+=(--pack "packs/compiled/$c.yaml")
done
if [ -z "$ORACLE" ] && [ ! -f packs/compiled/saas.yaml -o ! -f packs/compiled/hospital.yaml -o ! -f packs/compiled/manufacturer.yaml ]; then
  echo "compiler requests queued in $Q: answer them, cc batch load, and run this again"; exit 0
fi
[ -n "$ORACLE" ] && GOLD=()
for p in full no_reverse exhaustive_filtered; do
  cc rq1 --backend "$B" --batch-queue "$Q" --workers 4 --limit "$N" --preset "$p" --split test \
    "${PACKS[@]}" "${GOLD[@]}" --law-pack packs/law/us_law_pack.yaml \
    --planted data/planted/test_seed0.json --labels data/labels/ndas_auto.yaml --allow-auto --hide-facts \
    > "runs/pilot/last_$p.json"
  python -c "import json;m=json.load(open('runs/pilot/last_$p.json'));print('$p', m['rules'], 'pending NDAs:', m['pending_batch_ndas'], 'strict:', m['strict']['overall'])"
done
