#!/usr/bin/env bash
# Validate kb required fields + methodology citation sources (the "monitoring/evidence gate")
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fail=0
for f in "$REPO_ROOT"/kb/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *_template.md) continue;; esac
  for field in title root_cause fix lesson; do
    grep -q "^$field:" "$f" || { echo "缺少字段 $field: $f"; fail=1; }
  done
done
for f in "$REPO_ROOT"/methodology/*.md; do
  [ -e "$f" ] || continue
  grep -qiE "出处|引源|source|参考" "$f" || { echo "缺引源: $f"; fail=1; }
done
[ "$fail" -eq 0 ] && echo "校验通过" || { echo "校验失败"; exit 1; }
