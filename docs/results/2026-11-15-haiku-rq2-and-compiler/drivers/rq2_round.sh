#!/usr/bin/env bash
# One batch round of the RQ2 loop ablations: Haiku agents repair, Sonnet agents judge.
cd /home/user/repo; PY=/tmp/claude-0/venv/bin/python
P="--pack packs/policynda/saas/gold_rules.yaml --pack packs/policynda/hospital/gold_rules.yaml --pack packs/policynda/manufacturer/gold_rules.yaml"
rm -f runs/rq2a/q.claude-haiku-agent.jsonl runs/rq2a/j.claude-sonnet-agent.jsonl
$PY -m counselcopilot.cli rq2 --backend claude-haiku-agent --batch-queue runs/rq2a/q.jsonl --workers 4 $P \
  --law-pack packs/law/us_law_pack.yaml --planted data/planted/test_seed0.json --labels data/labels/ndas_auto.yaml --allow-auto \
  --limit ${LIMIT:-5} --evaluator-backend claude-sonnet-agent --evaluator-batch-queue runs/rq2a/j.jsonl --noise-floor 30 \
  --systems loop r1 r1_attacker r2 loop_no_attacker loop_no_regression loop_1_round > runs/rq2a/rq2.json 2>runs/rq2a/rq2.err
python3 -c "import json;m=json.load(open('runs/rq2a/rq2.json'));print('pending',m['pending_batch_items'],m['out_dir'])"
echo "haiku $(wc -l < runs/rq2a/q.claude-haiku-agent.jsonl 2>/dev/null || echo 0) sonnet $(wc -l < runs/rq2a/j.claude-sonnet-agent.jsonl 2>/dev/null || echo 0)"
