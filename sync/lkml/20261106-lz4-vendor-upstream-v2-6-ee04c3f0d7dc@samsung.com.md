---
title: [PATCH v2 06/15] lib/lz4: backport upstream's aarch64 fast decode loop enablement
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-6-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-6-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 06/15] lib/lz4: backport upstream's aarch64 fast decode loop enablement

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-6-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-6-ee04c3f0d7dc@samsung.com/)

```
v1.10.0 leaves LZ4_FAST_DEC_LOOP off for aarch64 built with clang, after
a slowdown reported on some Android phones in 2019 (upstream PR #707).
An arm64 kernel built with clang therefore decodes with the slower loop.

Upstream has since enabled it for all aarch64, in three unreleased
commits:

commit 0aa33884faf5 ("[LZ4] Limit disabling LZ4_FAST_DEC_LOOP to aarch64+clang+android")
commit 51f8af506b4a ("Fix missing endif")
commit ed86bc1ed802 ("AArch64: Enable LZ4_FAST_DEC_LOOP for Android")

Arm measured +3.5% to +15.6% on Cortex-A510 to X4 with clang. Take the
lz4.c hunks of all three. This goes away at the next re-sync.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 lib/lz4/upstream/lz4.c | 7 +------
 1 file changed, 1 insertion(+), 6 deletions(-)

diff --git a/lib/lz4/upstream/lz4.c b/lib/lz4/upstream/lz4.c
index 0d474be0236a698d297ab9a430f5082485eb3709..ee69d57aae112f4057c050bbdab4cc0f2d30f9d9 100644
--- a/lib/lz4/upstream/lz4.c
+++ b/lib/lz4/upstream/lz4.c
@@ -478,12 +478,7 @@ static const int      dec64table[8] = {0, 0, 0, -1, -4,  1, 2, 3};
 #ifndef LZ4_FAST_DEC_LOOP
 #  if defined __i386__ || defined _M_IX86 || defined __x86_64__ || defined _M_X64
 #    define LZ4_FAST_DEC_LOOP 1
-#  elif defined(__aarch64__) && defined(__APPLE__)
-#    define LZ4_FAST_DEC_LOOP 1
-#  elif defined(__aarch64__) && !defined(__clang__)
-     /* On non-Apple aarch64, we disable this optimization for clang because
-      * on certain mobile chipsets, performance is reduced with clang. For
-      * more information refer to https://github.com/lz4/lz4/pull/707 */
+#  elif defined(__aarch64__)
 #    define LZ4_FAST_DEC_LOOP 1
 #  else
 #    define LZ4_FAST_DEC_LOOP 0

-- 
2.34.1
```
