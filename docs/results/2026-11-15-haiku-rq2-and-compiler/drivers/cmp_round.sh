#!/usr/bin/env bash
# compile the three companies' prose policies with Haiku agents, then full vs structured_applicability on compiled cards
cd /home/user/repo; PY=/tmp/claude-0/venv/bin/python; Q=runs/cmp/q.jsonl
rm -f runs/cmp/q.claude-haiku-agent.jsonl
declare -A CO=([saas]="Northwind Cloud, Inc." [hospital]="Bayview Health Partners" [manufacturer]="Keystone Precision Manufacturing, Inc.")
ok=1
for c in saas hospital manufacturer; do
  [ -f packs/compiled/haiku_$c.yaml ] && continue
  $PY -m counselcopilot.cli compile --backend claude-haiku-agent --batch-queue $Q --workers 4 --policies packs/policynda/$c/policies \
    --company "${CO[$c]}" --gold packs/policynda/$c/gold_rules.yaml --out packs/compiled/haiku_$c.yaml > runs/cmp/compile_$c.json 2>runs/cmp/compile_$c.err
  [ -f packs/compiled/haiku_$c.yaml ] || ok=0
done
if [ $ok = 1 ]; then
  P="" G=""
  for c in saas hospital manufacturer; do P="$P --pack packs/compiled/haiku_$c.yaml"; G="$G --gold-pack packs/policynda/$c/gold_rules.yaml"; done
  for a in full structured_applicability; do
    $PY -m counselcopilot.cli rq1 --backend claude-haiku-agent --batch-queue $Q --workers 4 --limit 5 --split test $P $G \
      --law-pack packs/law/us_law_pack.yaml --planted data/planted/test_seed0.json --labels data/labels/ndas_auto.yaml --allow-auto \
      --hide-facts --scripted-precedents 30 --system pipeline --ablation $a > runs/cmp/$a.json 2>runs/cmp/$a.err
    echo "$a $(grep -o '[0-9]* NDAs waiting' runs/cmp/$a.err || echo done)"
  done
else echo "compile pending"; fi
echo "haiku $(wc -l < runs/cmp/q.claude-haiku-agent.jsonl 2>/dev/null || echo 0)"
