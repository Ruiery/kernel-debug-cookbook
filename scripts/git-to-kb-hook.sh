#!/usr/bin/env bash
# post-commit hook: commit -> kb candidate entry (one growth trigger source, spec §6)
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
DATE="$(date +%F)"
SUBJECT="$(git log -1 --pretty=%s)"
BODY="$(git log -1 --pretty=%b)"
SLUG="$(printf '%s' "$SUBJECT" | tr ' /' '__' | cut -c1-60)"
OUT="$REPO_ROOT/kb/$DATE-$SLUG.md"
cat > "$OUT" <<EOF
---
title: $SUBJECT
subsystem: <待定>
kind: <待定>
symptom: <从 commit 推断>
root_cause: <从 commit 推断>
fix: $SUBJECT
verified_by: <待定>
provenance: <待定>
sources: $(git rev-parse --short HEAD)
lesson: <必填：这次修 bug 的教训>
date: $DATE
---

$BODY

## 详细过程（补充）
EOF
echo "已生成 kb 候选条目：$OUT（请补 <待定> 字段，尤其 lesson）"
