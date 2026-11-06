---
title: [PATCH v2 00/15] lib/lz4: stop forking upstream LZ4, vendor it instead
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-0-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-0-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 00/15] lib/lz4: stop forking upstream LZ4, vendor it instead

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-0-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-0-ee04c3f0d7dc@samsung.com/)

```
The in-kernel LZ4 is a fork. The decompressor was last synced with
upstream v1.8.3 in 2018 and the compressor with v1.7.3 in 2017, both by
hand. Upstream has made 488 commits against lib/ since, and the gap is
maintained one cherry-pick at a time.

That has left real bugs in place for example the forked
LZ4_decompress_fast() has no bounds checks on its input, so corrupted
input reads past its end and before the output buffer.

This series vendors the upstream sources unmodified and adapts them at
build time, so a re-sync becomes a directory copy:

  upstream/lz4.c, upstream/lz4.h    verbatim upstream sources
  upstream/lz4hc.c, upstream/lz4hc.h
  lz4_deps.h                        the build environment
  lz4_kernel_api.h                  hands the LZ4 names back
  freestanding/                     ISO C headers -nostdinc drops
  lz4_compress.c                    the kernel's entry points
  lz4_decompress.c
  lz4hc_compress.c

Patches 1-3 apply to the fork as it stands: patch 1 moves the pre-boot
decompressor off LZ4_decompress_fast(), patch 2 removes it and its
variants, and patch 3 stops zram's lz4hc backend resetting its stream
for every page. Patch 4 imports the sources. Patches 5-7 backport the
upstream fixes the kernel needs on top of v1.10.0. Patch 8 adds the
build environment. Patch 9 puts the freestanding headers on the pre-boot
decompressor path. Patches 10, 11 and 13 convert the compressor, HC
compressor and decompressor in turn; patch 12 widens the in-place margin
erofs relies on for the new decoder. Patch 14 drops the last duplicated
prototype list. Patch 15 gives lib/lz4 a MAINTAINERS entry, which it has
never had.

This is meant to go through Andrew's tree; patch 9 needs acks from the
boot maintainers.

The exported API changes in four ways.

The three stream types become incomplete. <linux/lz4.h> spelled out their
layout for the fork's benefit, upstream headers define the same types and
lib/decompress_unlz4.c ends up with both in one translation unit. Callers
allocate LZ4_MEM_COMPRESS, LZ4HC_MEM_COMPRESS or LZ4_MEM_DECOMPRESS bytes
instead of sizeof() every caller but zram already did. Each conversion
patch makes its own type incomplete so no step leaves the tree broken.

Sixteen macros go with them: the hash geometry (LZ4_HASHLOG,
LZ4_HASHTABLESIZE, LZ4_HASH_SIZE_U32, LZ4HC_DICTIONARY_LOGSIZE, LZ4HC_MAXD,
LZ4HC_MAXD_MASK, LZ4HC_HASH_LOG, LZ4HC_HASHTABLESIZE, LZ4HC_HASH_MASK) and
the sizes derived from it (LZ4_MEMORY_USAGE, LZ4_STREAMSIZE{,_U64},
LZ4_STREAMHCSIZE{,_SIZET}, LZ4_STREAMDECODESIZE{,_U64}). They existed to
lay out structures the fork defined here none has an in tree user outside
lib/lz4. LZ4_compressBound() goes too a static inline whose only caller
was lib/decompress_unlz4.c, now using the LZ4_COMPRESSBOUND() macro.

LZ4_MEM_DECOMPRESS and LZ4HC_CLAMP_CLEVEL are new.

LZ4_decompress_fast(), LZ4_decompress_fast_continue() and
LZ4_decompress_fast_usingDict() go. Upstream has deprecated them since
v1.9, and their last in-tree user, the pre-boot decompressor, now uses
LZ4_decompress_safe_partial().

There are some behaviour changes. All of them come from upstream rather
than from this series and I have kept them rather than patching them
out: a local fix on top of vendored sources is exactly the divergence
this series exists to remove.

 - LZ4HC levels 10 and up are clamped to 9. Upstream routes them to its
   optimal parser, whose ~64K opt[] does not fit a kernel stack. The
   fork had no optimal parser at all - level only scaled search depth -
   so its levels 10-16 beat its own level 9 by 0.01%. Clamping rather
   than rejecting keeps existing f2fs and zram settings working.

 - LZ4_decompress_safe_partial() with a zero-length target returns 0
   rather than -1, matching upstream since 725cb0aafdf7. No in-tree
   caller depends on it.

 - The compressors require wrkmem aligned to 8 bytes. Upstream checks
   this and LZ4_initStream() returns NULL, which upstream's own callers
   then dereference or ignore. The entry points check the alignment
   themselves, warn once and fail the call. Every in-tree caller uses
   kmalloc() or vmalloc() and is already aligned; <linux/lz4.h> now
   documents the requirement.

The layout follows lib/zstd, which keeps upstream's sources in a
subdirectory and the kernel glue on top. zstd has an upstream import
tool and an upstream zstd_deps.h; LZ4 has neither, so the kernel glue
here lives outside the vendored files.

The import is the v1.10.0 release tag. It does not build under
-Wmissing-prototypes without upstream commit 5ef1f16929b5, which patch 5
backports. Patch 6 backports upstream's arm64 fast decode loop and patch
7 its match length limit fix; those are the only deviations from the
tag. The rest of PR #1753 fixes code added after v1.10.0, so it will
come with the next release.

checkpatch reports some 3500 errors against patch 4: upstream's coding
style, and no SPDX tags, in files kept verbatim.

Measured in the kernel: three kernels differing only in lib/lz4, booted
one core under KVM, each reading 1.3GB of kernel source from an LZ4
erofs image with the page cache dropped before every pass. For v2 this
was remeasured with more runs on an idle machine: median of 140 passes.
The middle column is upstream v1.10.0 with LZ4_FAST_DEC_LOOP=0,
to separate the version bump from the decode loop upstream added in
v1.9.0.

                        erofs read, MB/s
  erofs cluster    today   v1.10.0   + fast loop    net
             4K     2486      2549          2665    +7%
            64K     3013      3104          3225    +7%

The same three decoders at the library level, each block decompressed
on its own the way zram treats a page. x86_64, the fork's and upstream's
sources built with the kernel's code generation flags (so no SSE), all
decoding the same compressed input, median of 21 interleaved runs. The
first corpus is upstream's tests/datagen with a fixed seed, so it is
byte-identical anywhere; the second is a tar of kernel sources:

                                 decompression, MB/s
  corpus           block  ratio    today   v1.10.0  + fast loop   net
  datagen -s0 -P60   4K  1.09x     4584      4535         5097   +11%
                    16K  1.34x     3960      3978         4828   +22%
                    64K  1.90x     4797      4802         5598   +17%
                   256K  1.92x     6749      6559         7600   +13%
  kernel source tar  4K  2.29x     3719      3832         4219   +13%
                    16K  2.57x     3778      3880         4203   +11%
                    64K  2.80x     3792      3886         4179   +10%
                   256K  2.95x     4165      4280         4750   +14%

Compression is not uniformly faster: lz4hc on small blocks of poorly
compressible data is up to 15% slower. Patches 10 and 11 have the
numbers.

The cost is size: lib/lz4 grows from 45K to 86K of text on x86_64,
lz4hc most (12K to 39K). That is upstream code the fork never had.

---
Changes in v2:
- Drop the RFC prefix
- New patches 1-2: move the pre-boot decompressor to
  LZ4_decompress_safe_partial() and remove LZ4_decompress_fast() and its
  variants from the fork, ahead of the import (Sergey)
- New patch 3: zram's lz4hc backend resets its stream once, not per page
- New patches 6-7: backport upstream's arm64 fast decode loop (Sergey)
  and its match length limit fix
- New patch 12: widen LZ4_DECOMPRESS_INPLACE_MARGIN for the fast decode
  loop
- Compressor entry points check wrkmem alignment, warn and fail (Sergey)
- Patch 13 names the upstream counterpart of each retired local patch
  (Sergey)
- MAINTAINERS: also cover lib/decompress_unlz4.c and
  include/linux/decompress/unlz4.h (Eric)
- Remeasure erofs reads with more runs on an idle machine
- Link to v1: https://lore.kernel.org/r/20260925-lz4-vendor-upstream-v1-0-1c7ffbe21c4b@samsung.com

---
Michal Wilczynski (15):
      lib/decompress_unlz4: use LZ4_decompress_safe_partial() before boot
      lib/lz4: remove LZ4_decompress_fast() 
```
