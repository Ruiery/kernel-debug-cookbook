---
title: [PATCH RFC 0/9] lib/lz4: stop forking upstream LZ4, vendor it instead
list: linux-block
message_id: 20260925-lz4-vendor-upstream-v1-0-1c7ffbe21c4b@samsung.com
link: https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-0-1c7ffbe21c4b@samsung.com/
---

# [PATCH RFC 0/9] lib/lz4: stop forking upstream LZ4, vendor it instead

来源：[https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-0-1c7ffbe21c4b@samsung.com/](https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-0-1c7ffbe21c4b@samsung.com/)

```
The in-kernel LZ4 is a fork. The decompressor was last synced with
upstream v1.8.3 in 2018 and the compressor with v1.7.3 in 2017, both by
hand. Upstream has made 488 commits against lib/ since, and the gap is
maintained one cherry-pick at a time.

That has left real bugs in place for example the forked
LZ4_decompress_fast() has no bounds checks, so corrupted input runs off
the output buffer in both directions. 

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

Patch 1 imports the sources. Patch 2 backports the one upstream fix the
kernel's warning flags require. Patch 3 adds the build environment.
Patch 4 puts the freestanding headers on the pre-boot decompressor path.
Patches 5-7 convert the compressor, HC compressor and decompressor in
turn. Patch 8 folds away the last duplicated prototype list. Patch 9
gives lib/lz4 a MAINTAINERS entry, which it has never had.

The exported API changes in three ways.

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

There are some behaviour changes. All of them come from upstream rather
than from this series and I have kept them rather than patching them
out: a local fix on top of vendored sources is exactly the divergence
this series exists to remove.

 - LZ4HC levels 10 and up are clamped to 9. Upstream routes them to its
   optimal parser, whose ~64K opt[] does not fit a kernel stack. The
   fork had no optimal parser at all - level only scaled search depth -
   so its levels 10-16 beat its own level 9 by 0.01%. Clamping rather
   than rejecting keeps existing f2fs and zram settings working.

 - LZ4_decompress_fast() stops running off the output buffer.
   Upstream routes it through LZ4_decompress_unsafe_generic(), which
   bounds-checks. 

 - LZ4_decompress_safe_partial() with a zero-length target returns 0
   rather than -1, matching upstream since 725cb0aafdf7. No in-tree
   caller passes zero.

 - The compressors require wrkmem aligned to 8 bytes. Upstream checks
   this and LZ4_initStream() returns NULL, which the stateless entry
   points cannot report, so a misaligned buffer faults rather than
   failing cleanly. Every in-tree caller uses kmalloc() or vmalloc() and
   is already aligned; <linux/lz4.h> now documents the requirement.
   Turning upstream's LZ4_ALIGN_TEST off would trade a loud failure for
   a silent one.

The layout follows lib/zstd, which keeps upstream's sources in a
subdirectory and the kernel glue on top. zstd has an upstream import
tool and an upstream zstd_deps.h; LZ4 has neither, so the kernel glue
here lives outside the vendored files.

The import is the v1.10.0 release tag. It does not build under
-Wmissing-prototypes without upstream commit 5ef1f16929b5, which patch 2
backports; that is the only deviation from the tag. The decoder fixes
in PR #1753 landed after v1.10.0 and do not backport cleanly; they will
come with the next release.

checkpatch reports some 3500 errors against patch 1: upstream's coding
style, and no SPDX tags, in files kept verbatim.

Measured in the kernel: three kernels differing only in lib/lz4, booted
one core under KVM, each reading 1.3GB of kernel source from an LZ4
erofs image with the page cache dropped before every pass. Median of 21
passes. The middle column is upstream v1.10.0 with LZ4_FAST_DEC_LOOP=0,
to separate the version bump from the decode loop upstream added in
v1.9.0.

                        erofs read, MB/s
  erofs cluster    today   v1.10.0   + fast loop    net
             4K     2363      2404          2630   +11%
            64K     2788      2904          3168   +14%

The same three decoders at the library level, each block decompressed
on its own the way zram treats a page. x86_64, the fork's and upstream's
sources built with the kernel's code generation flags (so no SSE), all
decoding the same compressed input, median of 21 interleaved runs. The
first corpus is upstream's tests/datagen with a fixed seed, so it is
byte-identical anywhere; the second is a tar of kernel sources:

                                 decompression, MB/s
  corpus           block  ratio    today   v1.10.0  + fast loop   net
  datagen -s0 -P60   4K  1.09x     4588      4702         5086   +11%
                    16K  1.34x     3950      4016         4779   +21%
                    64K  1.90x     4761      4866         5588   +17%
                   256K  1.92x     6596      6714         7258   +10%
  kernel source tar  4K  2.29x     3694      3830         4190   +13%
                    16K  2.57x     3653      3842         4091   +12%
                    64K  2.80x     3655      3818         4039   +11%
                   256K  2.95x     4072      4231         4542   +12%

The cost is size: lib/lz4 grows from 45K to 89K of text on x86_64,
lz4hc most (12K to 39K). That is upstream code the fork never had, and
the optimal parser the level clamp leaves unreachable is only 6K of it.

---
Michal Wilczynski (9):
      lib/lz4: import upstream LZ4 sources verbatim
      lib/lz4: backport upstream's -Wmissing-prototypes fix
      lib/lz4: add the build environment for the vendored sources
      arch: boot: put the LZ4 freestanding headers on the decompressor path
      lib/lz4: switch the compressor to the vendored sources
      lib/lz4: switch the HC compressor to the vendored sources
      lib/lz4: switch the decompressor to the vendored sources
      lib/lz4: fold lz4_kernel_api.h into <linux/lz4.h>
      MAINTAINERS: add an entry for the LZ4 compression library

 MAINTAINERS                          |    6 +
 arch/arm/boot/compressed/Makefile    |    3 +
 arch/mips/boot/compressed/Makefile   |    4 +
 arch/parisc/boot/compressed/Makefile |    3 +
 arch/s390/boot/Makefile              |    3 +
 arch/x86/boot/compressed/Makefile    |    3 +
 drivers/block/zram/backend_lz4.c     |    8 +-
 drivers/block/zram/backend_lz4hc.c   |    4 +-
 include/linux/lz4.h                  |  151 +-
 lib/decompress_unlz4.c               |    4 +-
 lib/lz4/Makefile                     |   15 +-
 lib/lz4/freestanding/limits.h        |   14 +
 lib/lz4/freestanding/stddef.h        |   15 +
 lib/lz4/freestanding/stdint.h        |   14 +
 lib/lz4/freestanding/string.h        |   14 +
 lib/lz4/lz4_compress.c               |  941 +----------
 lib/lz4/lz4_decompress.c             |  718 +--------
 lib/lz4/lz4_deps.h                   |   96 ++
 lib/lz4/lz4_kernel_api.h             |   35 +
 lib/lz4/lz4defs.h                    |  247 ---
 lib/lz4/lz4hc_compress.c             |  785 +---------
 lib/lz4/upstream/lz4.c               | 2829 ++++++++
```
