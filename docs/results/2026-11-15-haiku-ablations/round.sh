#!/usr/bin/env bash
# One batch round of the Haiku-agent RQ1 ablations: run every config (queues uncached requests).
cd /home/user/repo
PY=/tmp/claude-0/venv/bin/python; B=claude-haiku-agent; Q=runs/abl/q.jsonl
P="--pack packs/policynda/saas/gold_rules.yaml --pack packs/policynda/hospital/gold_rules.yaml --pack packs/policynda/manufacturer/gold_rules.yaml"
COMMON="--backend $B --batch-queue $Q --workers 4 --limit ${LIMIT:-5} --split test $P --law-pack packs/law/us_law_pack.yaml --planted data/planted/test_seed0.json --labels data/labels/ndas_auto.yaml --allow-auto --hide-facts --scripted-precedents 30"
rm -f runs/abl/q.$B.jsonl
run() { n=$1; shift; $PY -m counselcopilot.cli rq1 $COMMON "$@" > runs/abl/$n.json 2>runs/abl/$n.err; echo "$n $(grep -o '[0-9]* NDAs waiting' runs/abl/$n.err || echo done)"; }
for a in full no_reverse no_filter no_frames no_verifier fixed_pipeline no_xref no_memory no_tool_agent tool_errors; do run $a --system pipeline --ablation $a; done
for p in full exhaustive_filtered; do run reviewer_$p --system reviewer --preset $p; done
for b in b2 b2_checklist b3; do run $b --system $b; done
wc -l < runs/abl/q.$B.jsonl 2>/dev/null || echo 0
