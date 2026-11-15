#!/usr/bin/env bash
# mkp.sh N : write per-shard Haiku prompts and the judge prompt for round N
cd /home/user/repo/runs/all; N=$1
for s in r$N/haiku/shard_*.jsonl; do b=$(basename $s .jsonl)
  sed -e "s#SHARD#/home/user/repo/runs/all/$s#g" -e "s#OUT#/home/user/repo/runs/all/r$N/haiku/answers/$b.jsonl#g" -e "s#under /tmp named after your shard#/tmp/r${N}_$b#" -e "s#<shard name>#$b#" /home/user/repo/runs/abl/agent_prompt.txt > r$N/haiku/$b.prompt.txt; done
sed "s#JUDGEDIR#/home/user/repo/runs/all/r$N/judge#g" judge_prompt.txt > r$N/judge.prompt.txt
ls r$N/haiku/*.prompt.txt r$N/judge.prompt.txt
