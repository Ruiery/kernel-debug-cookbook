#!/usr/bin/env bash
# 一个命令搜遍知识库：kb 案例 + syzbot 报告 + lkml patch
# 用法：bash scripts/search-kb.sh <关键词>
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TERM="${1:?用法: bash scripts/search-kb.sh <关键词>}"

echo "== 含「$TERM」的文件（kb/ + sync/，大小写不敏感）=="
grep -rli --include='*.md' "$TERM" "$ROOT/kb" "$ROOT/sync" 2>/dev/null \
  | grep -vE '_(template|summary-template)' \
  | while IFS= read -r f; do
      rel="${f#"$ROOT"/}"
      t=$(grep -m1 '^title:' "$f" 2>/dev/null | sed 's/^title: *//')
      printf '%s\n    ↳ %s\n' "$rel" "${t:-<无标题>}"
    done
