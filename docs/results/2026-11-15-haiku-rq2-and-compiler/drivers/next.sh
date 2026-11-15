#!/usr/bin/env bash
# load round N (Haiku shards + Sonnet judge tasks), rerun RQ2 loop ablations and the compiled-pack runs, export round N+1
cd /home/user/repo; N=$1; M=$((N+1)); PY=/tmp/claude-0/venv/bin/python; R=runs/all
if [ "$N" -gt 0 ]; then
  [ -f $R/r$N/q.claude-haiku-agent.jsonl ] && $PY -m counselcopilot.cli batch load --backend claude-haiku-agent --queue $R/r$N/q.claude-haiku-agent.jsonl --answers $R/r$N/haiku/answers
  if [ -f $R/r$N/j.claude-sonnet-agent.jsonl ]; then
    PYTHONPATH=src $PY scripts/agent_judge.py collect --out $R/r$N/judge > /dev/null
    $PY -m counselcopilot.cli batch load --backend claude-sonnet-agent --queue $R/r$N/j.claude-sonnet-agent.jsonl --answers $R/r$N/judge/answers_jsonl
  fi
fi
echo "rq2: $(runs/rq2a/round.sh | tr '\n' ' ')"
echo "cmp: $(runs/cmp/round.sh | tr '\n' ' ')"
mkdir -p $R/r$M
cat runs/rq2a/q.claude-haiku-agent.jsonl runs/cmp/q.claude-haiku-agent.jsonl 2>/dev/null | python3 -c "
import sys,json
seen=set()
for l in sys.stdin:
  if l.strip():
    k=json.loads(l)['key']
    if k not in seen: seen.add(k); sys.stdout.write(l)" > $R/r$M/q.claude-haiku-agent.jsonl
[ -s $R/r$M/q.claude-haiku-agent.jsonl ] || rm $R/r$M/q.claude-haiku-agent.jsonl
if [ -f $R/r$M/q.claude-haiku-agent.jsonl ]; then
  $PY -m counselcopilot.cli batch export --backend claude-haiku-agent --queue $R/r$M/q.claude-haiku-agent.jsonl --out $R/r$M/haiku --per-shard ${PER:-40} | python3 -c "import json,sys;d=json.load(sys.stdin);print('haiku',d['requests'],[(s['n'],s['chars']) for s in d['shards']])"
fi
if [ -s runs/rq2a/j.claude-sonnet-agent.jsonl ]; then
  cp runs/rq2a/j.claude-sonnet-agent.jsonl $R/r$M/
  OUT=$(python3 -c "import json;print(json.load(open('runs/rq2a/rq2.json'))['out_dir'])")
  PYTHONPATH=src $PY scripts/agent_judge.py export --queue $R/r$M/j.claude-sonnet-agent.jsonl --repaired $OUT/repaired_drafts.jsonl --out $R/r$M/judge | python3 -c "
import json,sys; d=json.load(sys.stdin); print('judge', {g:(len(v),sum(x['questions'] for x in v)) for g,v in d.items()})"
fi
