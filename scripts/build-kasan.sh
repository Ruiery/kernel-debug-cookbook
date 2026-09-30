#!/usr/bin/env bash
# On remote Linux: rebuild the modified kernel with KASAN/KCSAN/lockdep
set -euo pipefail
KERNEL_TREE="${KERNEL_TREE:?请先 export KERNEL_TREE=/path/to/linux}"
OUT="${OUT:-$KERNEL_TREE/build-kasan}"
JOBS="${JOBS:-$(nproc)}"
cd "$KERNEL_TREE"
make O="$OUT" "${DEFCONFIG:-defconfig}"
./scripts/config --file "$OUT/.config" \
  -e KASAN -e KCSAN -e PROVE_LOCKING \
  -e DEBUG_KERNEL -e DEBUG_INFO -e FRAME_POINTER -e KALLSYMS
make O="$OUT" olddefconfig
make O="$OUT" -j"$JOBS"
echo "构建完成：$OUT/vmlinux"
