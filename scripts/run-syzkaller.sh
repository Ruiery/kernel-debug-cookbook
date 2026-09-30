#!/usr/bin/env bash
# On remote Linux: run syzkaller fuzzing in QEMU (prereq: syzkaller built, image available)
set -euo pipefail
SZK_BIN="${SZK_BIN:?请先 export SZK_BIN=/path/to/syz-manager}"
CFG="${CFG:?请先 export CFG=/path/to/syzkaller.cfg}"
"$SZK_BIN" -config "$CFG"
