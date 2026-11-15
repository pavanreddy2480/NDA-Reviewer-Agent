#!/usr/bin/env bash
# load round N answers, run every config again, export round N+1 shards
cd /home/user/repo; N=$1; M=$((N+1)); PY=/tmp/claude-0/venv/bin/python; B=claude-haiku-agent
cp runs/abl/q.$B.jsonl runs/abl/r$N/q.$B.jsonl 2>/dev/null
$PY -m counselcopilot.cli batch load --backend $B --queue runs/abl/r$N/q.$B.jsonl --answers runs/abl/r$N/answers
runs/abl/round.sh | tr '\n' ';'; echo
[ -s runs/abl/q.$B.jsonl ] && $PY -m counselcopilot.cli batch export --backend $B --queue runs/abl/q.$B.jsonl --out runs/abl/r$M --per-shard ${PER:-40} | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['requests'],[(s['n'],s['chars']) for s in d['shards']])"
