#!/usr/bin/env bash
# RQ1 pilot with Claude (agents) as the system under test: 20 planted test NDAs, three presets,
# deal facts hidden. Run it, answer the exported shards with agents, `cc batch load`, run it again,
# until it reports nothing pending. Then the three runs/ folders hold the metrics.
set -e
B=${BACKEND:-claude-sonnet-agent}
N=${LIMIT:-20}
Q=runs/pilot/queue.jsonl
mkdir -p runs/pilot
for p in full no_reverse exhaustive_filtered; do
  cc rq1 --backend "$B" --batch-queue "$Q" --workers 4 --limit "$N" --preset "$p" --split test \
    --pack packs/policynda/saas/gold_rules.yaml --pack packs/policynda/hospital/gold_rules.yaml \
    --pack packs/policynda/manufacturer/gold_rules.yaml --law-pack packs/law/us_law_pack.yaml \
    --planted data/planted/test_seed0.json --labels data/labels/ndas_auto.yaml --allow-auto --hide-facts \
    > "runs/pilot/last_$p.json"
  python -c "import json;m=json.load(open('runs/pilot/last_$p.json'));print('$p', 'pending NDAs:', m['pending_batch_ndas'], 'strict:', m['strict']['overall'])"
done
