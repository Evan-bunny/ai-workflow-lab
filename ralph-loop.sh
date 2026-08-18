#!/bin/bash
# Ralph Loop：每轮全新 context 启动 kimi，靠磁盘文件（fix_plan.md）接力。
set -u
cd "$(dirname "$0")"
mkdir -p .ralph

MAX_LOOPS=${1:-8}
for i in $(seq 1 "$MAX_LOOPS"); do
  echo "===== Loop $i / $MAX_LOOPS 开始 $(date +%H:%M:%S) ====="
  output=$(kimi -p "$(cat PROMPT.md)" 2>&1)
  echo "$output" | tee ".ralph/loop-$i.log" | tail -5

  # 双重完成判定：显式信号 + 计划文件无未完成项
  if echo "$output" | grep -q "EXIT_SIGNAL: true" && ! grep -q '^- \[ \]' fix_plan.md; then
    echo "===== 全部任务完成，循环收敛于第 $i 轮 ====="
    exit 0
  fi
done
echo "===== 达到上限 $MAX_LOOPS 轮，人工介入 ====="
exit 1
