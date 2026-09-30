#!/usr/bin/env bash
# On remote Linux: run kernel selftests
set -euo pipefail
KERNEL_TREE="${KERNEL_TREE:?请先 export KERNEL_TREE=/path/to/linux}"
OUT="${OUT:-$KERNEL_TREE/build-kasan}"
cd "$KERNEL_TREE"
make O="$OUT" -C tools/testing/selftests run_tests
