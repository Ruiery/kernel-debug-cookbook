---
title: [PATCH RFC 1/9] lib/lz4: import upstream LZ4 sources verbatim
list: linux-block
message_id: 20260925-lz4-vendor-upstream-v1-1-1c7ffbe21c4b@samsung.com
link: https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-1-1c7ffbe21c4b@samsung.com/
---

# [PATCH RFC 1/9] lib/lz4: import upstream LZ4 sources verbatim

来源：[https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-1-1c7ffbe21c4b@samsung.com/](https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-1-1c7ffbe21c4b@samsung.com/)

```
Add the four upstream files under lib/lz4/upstream/ without modification.
Nothing builds them yet; a later patch adds the build environment.

Copied without modification from the v1.10.0 release tag of
https://github.com/lz4/lz4, tagged 2024-07-21.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 lib/lz4/upstream/lz4.c   | 2829 ++++++++++++++++++++++++++++++++++++++++++++++
 lib/lz4/upstream/lz4.h   |  884 +++++++++++++++
 lib/lz4/upstream/lz4hc.c | 2192 +++++++++++++++++++++++++++++++++++
 lib/lz4/upstream/lz4hc.h |  414 +++++++
 4 files changed, 6319 insertions(+)

diff --git a/lib/lz4/upstream/lz4.c b/lib/lz4/upstream/lz4.c
new file mode 100644
index 0000000000000000000000000000000000000000..a2f7abee19fb9a5c768f2a6c266acf5b571f0855
--- /dev/null
+++ b/lib/lz4/upstream/lz4.c
@@ -0,0 +1,2829 @@
+/*
+   LZ4 - Fast LZ compression algorithm
+   Copyright (C) 2011-2023, Yann Collet.
+
+   BSD 2-Clause License (http://www.opensource.org/licenses/bsd-license.php)
+
+   Redistribution and use in source and binary forms, with or without
+   modification, are permitted provided that the following conditions are
+   met:
+
+       * Redistributions of source code must retain the above copyright
+   notice, this list of conditions and the following disclaimer.
+       * Redistributions in binary form must reproduce the above
+   copyright notice, this list of conditions and the following disclaimer
+   in the documentation and/or other materials provided with the
+   distribution.
+
+   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
+   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
+   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
+   A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
+   OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
+   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
+   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
+   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
+   THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
+   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
+   OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
+
+   You can contact the author at :
+    - LZ4 homepage : http://www.lz4.org
+    - LZ4 source repository : https://github.com/lz4/lz4
+*/
+
+/*-************************************
+*  Tuning parameters
+**************************************/
+/*
+ * LZ4_HEAPMODE :
+ * Select how stateless compression functions like `LZ4_compress_default()`
+ * allocate memory for their hash table,
+ * in memory stack (0:default, fastest), or in memory heap (1:requires malloc()).
+ */
+#ifndef LZ4_HEAPMODE
+#  define LZ4_HEAPMODE 0
+#endif
+
+/*
+ * LZ4_ACCELERATION_DEFAULT :
+ * Select "acceleration" for LZ4_compress_fast() when parameter value <= 0
+ */
+#define LZ4_ACCELERATION_DEFAULT 1
+/*
+ * LZ4_ACCELERATION_MAX :
+ * Any "acceleration" value higher than this threshold
+ * get treated as LZ4_ACCELERATION_MAX instead (fix #876)
+ */
+#define LZ4_ACCELERATION_MAX 65537
+
+
+/*-************************************
+*  CPU Feature Detection
+**************************************/
+/* LZ4_FORCE_MEMORY_ACCESS
+ * By default, access to unaligned memory is controlled by `memcpy()`, which is safe and portable.
+ * Unfortunately, on some target/compiler combinations, the generated assembly is sub-optimal.
+ * The below switch allow to select different access method for improved performance.
+ * Method 0 (default) : use `memcpy()`. Safe and portable.
+ * Method 1 : `__packed` statement. It depends on compiler extension (ie, not portable).
+ *            This method is safe if your compiler supports it, and *generally* as fast or faster than `memcpy`.
+ * Method 2 : direct access. This method is portable but violate C standard.
+ *            It can generate buggy code on targets which assembly generation depends on alignment.
+ *            But in some circumstances, it's the only known way to get the most performance (ie GCC + ARMv6)
+ * See https://fastcompression.blogspot.fr/2015/08/accessing-unaligned-memory.html for details.
+ * Prefer these methods in priority order (0 > 1 > 2)
+ */
+#ifndef LZ4_FORCE_MEMORY_ACCESS   /* can be defined externally */
+#  if defined(__GNUC__) && \
+  ( defined(__ARM_ARCH_6__) || defined(__ARM_ARCH_6J__) || defined(__ARM_ARCH_6K__) \
+  || defined(__ARM_ARCH_6Z__) || defined(__ARM_ARCH_6ZK__) || defined(__ARM_ARCH_6T2__) )
+#    define LZ4_FORCE_MEMORY_ACCESS 2
+#  elif (defined(__INTEL_COMPILER) && !defined(_WIN32)) || defined(__GNUC__) || defined(_MSC_VER)
+#    define LZ4_FORCE_MEMORY_ACCESS 1
+#  endif
+#endif
+
+/*
+ * LZ4_FORCE_SW_BITCOUNT
+ * Define this parameter if your target system or compiler does not support hardware bit count
+ */
+#if defined(_MSC_VER) && defined(_WIN32_WCE)   /* Visual Studio for WinCE doesn't support Hardware bit count */
+#  undef  LZ4_FORCE_SW_BITCOUNT  /* avoid double def */
+#  define LZ4_FORCE_SW_BITCOUNT
+#endif
+
+
+
+/*-************************************
+*  Dependency
+**************************************/
+/*
+ * LZ4_SRC_INCLUDED:
+ * Amalgamation flag, whether lz4.c is included
+ */
+#ifndef LZ4_SRC_INCLUDED
+#  define LZ4_SRC_INCLUDED 1
+#endif
+
+#ifndef LZ4_DISABLE_DEPRECATE_WARNINGS
+#  define LZ4_DISABLE_DEPRECATE_WARNINGS /* due to LZ4_decompress_safe_withPrefix64k */
+#endif
+
+#ifndef LZ4_STATIC_LINKING_ONLY
+#  define LZ4_STATIC_LINKING_ONLY
+#endif
+#include "lz4.h"
+/* see also "memory routines" below */
+
+
+/*-************************************
+*  Compiler Options
+**************************************/
+#if defined(_MSC_VER) && (_MSC_VER >= 1400)  /* Visual Studio 2005+ */
+#  include <intrin.h>               /* only present in VS2005+ */
+#  pragma warning(disable : 4127)   /* disable: C4127: conditional expression is constant */
+#  pragma warning(disable : 6237)   /* disable: C6237: conditional expression is always 0 */
+#  pragma warning(disable : 6239)   /* disable: C6239: (<non-zero constant> && <expression>) always evaluates to the result of <expression> */
+#  pragma warning(disable : 6240)   /* disable: C6240: (<expression> && <non-zero constant>) always evaluates to the result of <expression> */
+#  pragma warning(disable : 6326)   /* disable: C6326: Potential comparison of a constant with another constant */
+#endif  /* _MSC_VER */
+
+#ifndef LZ4_FORCE_INLINE
+#  if defined (_MSC_VER) && !defined (__clang__)    /* MSVC */
+#    define LZ4_FORCE_INLINE static __forceinline
+#  else
+#    if defined (__cplusplus) || defined (__STDC_VERSION__) && __STDC_VERSION__ >= 199901L   /* C99 */
+#      if defined (__GNUC__) || defined (__clang__)
+#        define LZ4_FORCE_INLINE static inline __attribute__((always_inline))
+#      else
+#        define LZ4_FORCE_INLINE static inline
+#      endif
+#    else
+#      define LZ4_FORCE_INLINE static
+#    endif /* __STDC_VERSION__ */
+#  endif  /* _MSC_VER */
+#endif /* LZ4_FORCE_INLINE */
+
+/* LZ4_FORCE_O2 and LZ4_FORCE_INLINE
+ * gcc on ppc64le generates an unrolled SIMDized loop for LZ4_wildCopy8,
+ * together with a simple 8-byte copy loop as a fall-back path.
+ * However, this optimization hurts the decompression speed by >30%,
+ * because the execution does not go to the optimized loop
+ * for typical compressible data, and all of the preamble checks
+ * before going to the fall-back path become useless overhead.
+ * This optimization happens only with the -O3 flag, and -O2 generates
+ * a simple 8-byte copy loop.
+ * With gcc on ppc64le, all of the LZ4_decompress_* and LZ4_wildCopy8
+ * functions are annotated with __attribute__((optimize("O2"))),
+ * and also LZ4_wildCopy8 is forcibly inlined, so that the O2 attribute
+ * of LZ4_wildCopy8 does not affect the compression speed.
+ */
+#if defined(__PPC64__) && defined(__LITTLE_ENDIAN__) && d
```
