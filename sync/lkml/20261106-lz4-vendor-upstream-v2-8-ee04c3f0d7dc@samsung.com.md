---
title: [PATCH v2 08/15] lib/lz4: add the build environment for the vendored sources
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-8-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-8-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 08/15] lib/lz4: add the build environment for the vendored sources

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-8-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-8-ee04c3f0d7dc@samsung.com/)

```
lz4_deps.h makes the vendored upstream sources build in the kernel. It
gives every upstream entry point internal linkage, so an object carries
only the codec it forwards, selects heap mode with failing allocators so
LZ4HC's ~64K optimal-parser buffer stays off the stack, and renames the
entry points the kernel re-exports so the kernel's own definitions can
use the real names. LZ4LIB_VISIBILITY carries __maybe_unused for the
functions an object does not use.

freestanding/ forwards the four ISO C headers upstream includes to their
<linux/> equivalents. lz4_kernel_api.h undoes the renaming; it carries
its own copy of the exported prototypes until a later patch can include
<linux/lz4.h> instead.

Two settings upstream leaves to the build:

 - Unaligned access goes through memcpy() where the architecture has
   efficient unaligned access, and through packed structs, as
   get_unaligned() does, elsewhere. Left alone, upstream uses plain
   misaligned loads on ARMv6.

 - On ppc64le, lz4.c marks functions __attribute__((optimize("O2"))) for
   GCC, which drops command line options such as -fno-strict-aliasing
   for them; see commit 080b6f407635 ("bpf: Don't rely on GCC
   __attribute__((optimize)) to disable GCSE"). lz4_deps.h defines
   optimize() to nothing for upstream's sources.

Nothing includes either header yet.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 lib/lz4/freestanding/limits.h |  14 +++++
 lib/lz4/freestanding/stddef.h |  15 ++++++
 lib/lz4/freestanding/stdint.h |  14 +++++
 lib/lz4/freestanding/string.h |  14 +++++
 lib/lz4/lz4_deps.h            | 118 ++++++++++++++++++++++++++++++++++++++++++
 lib/lz4/lz4_kernel_api.h      |  90 ++++++++++++++++++++++++++++++++
 6 files changed, 265 insertions(+)

diff --git a/lib/lz4/freestanding/limits.h b/lib/lz4/freestanding/limits.h
new file mode 100644
index 0000000000000000000000000000000000000000..0d1cafbc77eb5d2f564b51feaa911748446abf60
--- /dev/null
+++ b/lib/lz4/freestanding/limits.h
@@ -0,0 +1,14 @@
+/* SPDX-License-Identifier: GPL-2.0-only */
+/*
+ * Copyright (c) 2026 Samsung Electronics Co., Ltd.
+ * Author: Michal Wilczynski <m.wilczynski@samsung.com>
+ *
+ * Freestanding <limits.h> for the vendored upstream LZ4 sources; lz4.c needs
+ * UINT_MAX and lz4hc.c needs INT_MAX.
+ */
+#ifndef __LZ4_FREESTANDING_LIMITS_H__
+#define __LZ4_FREESTANDING_LIMITS_H__
+
+#include <linux/limits.h>
+
+#endif
diff --git a/lib/lz4/freestanding/stddef.h b/lib/lz4/freestanding/stddef.h
new file mode 100644
index 0000000000000000000000000000000000000000..aaafd2413849210fa4ec4fa03ba0e9453a9fe026
--- /dev/null
+++ b/lib/lz4/freestanding/stddef.h
@@ -0,0 +1,15 @@
+/* SPDX-License-Identifier: GPL-2.0-only */
+/*
+ * Copyright (c) 2026 Samsung Electronics Co., Ltd.
+ * Author: Michal Wilczynski <m.wilczynski@samsung.com>
+ *
+ * Freestanding <stddef.h> for the vendored upstream LZ4 sources; -nostdinc
+ * drops the compiler's copy, and lz4.h needs size_t and NULL.
+ */
+#ifndef __LZ4_FREESTANDING_STDDEF_H__
+#define __LZ4_FREESTANDING_STDDEF_H__
+
+#include <linux/stddef.h>	/* NULL, offsetof */
+#include <linux/types.h>	/* size_t, ptrdiff_t */
+
+#endif
diff --git a/lib/lz4/freestanding/stdint.h b/lib/lz4/freestanding/stdint.h
new file mode 100644
index 0000000000000000000000000000000000000000..923db05b19f23fb4051d16e5df2bf134cd5ac11e
--- /dev/null
+++ b/lib/lz4/freestanding/stdint.h
@@ -0,0 +1,14 @@
+/* SPDX-License-Identifier: GPL-2.0-only */
+/*
+ * Copyright (c) 2026 Samsung Electronics Co., Ltd.
+ * Author: Michal Wilczynski <m.wilczynski@samsung.com>
+ *
+ * Freestanding <stdint.h> for the vendored upstream LZ4 sources; forwards to
+ * <linux/types.h>.
+ */
+#ifndef __LZ4_FREESTANDING_STDINT_H__
+#define __LZ4_FREESTANDING_STDINT_H__
+
+#include <linux/types.h>
+
+#endif
diff --git a/lib/lz4/freestanding/string.h b/lib/lz4/freestanding/string.h
new file mode 100644
index 0000000000000000000000000000000000000000..8f3ea3b63013608a780a52fe9c33bf5df557584e
--- /dev/null
+++ b/lib/lz4/freestanding/string.h
@@ -0,0 +1,14 @@
+/* SPDX-License-Identifier: GPL-2.0-only */
+/*
+ * Copyright (c) 2026 Samsung Electronics Co., Ltd.
+ * Author: Michal Wilczynski <m.wilczynski@samsung.com>
+ *
+ * Freestanding <string.h> for the vendored upstream LZ4 sources; lz4.c
+ * includes it for memcpy()/memset(), which must resolve under -nostdinc.
+ */
+#ifndef __LZ4_FREESTANDING_STRING_H__
+#define __LZ4_FREESTANDING_STRING_H__
+
+#include <linux/string.h>
+
+#endif
diff --git a/lib/lz4/lz4_deps.h b/lib/lz4/lz4_deps.h
new file mode 100644
index 0000000000000000000000000000000000000000..23d69c75867f71224cb533e9341bd38439b9dee8
--- /dev/null
+++ b/lib/lz4/lz4_deps.h
@@ -0,0 +1,118 @@
+/* SPDX-License-Identifier: GPL-2.0-only OR BSD-2-Clause */
+/*
+ * Copyright (c) 2026 Samsung Electronics Co., Ltd.
+ * Author: Michal Wilczynski <m.wilczynski@samsung.com>
+ *
+ * Build environment for the vendored upstream LZ4 sources.
+ *
+ * upstream/ is LZ4 v1.10.0 plus three backports: 5ef1f16929b5, the aarch64
+ * fast loop (0aa33884faf5, 51f8af506b4a, ed86bc1ed802) and the match length
+ * limit of 587ed9557708, adapted.  Replace it with a later release rather
+ * than patch it further.  The three entry point files include this header
+ * first.
+ */
+
+#ifndef __LZ4_DEPS_H__
+#define __LZ4_DEPS_H__
+
+#include <linux/build_bug.h>	/* static_assert */
+#include <linux/compiler.h>	/* __maybe_unused */
+#include <linux/string.h>
+#include <linux/types.h>
+
+/* lz4.c uses "current" as a local; <asm/current.h> breaks the build. */
+#undef current
+
+/* Static so an object carries only the codec it forwards.  Each object
+ * forwards only some of them, so mark them __maybe_unused rather than turn
+ * off -Wunused-function, which the pre-boot builds would not see anyway.
+ */
+#define LZ4LIB_VISIBILITY static __maybe_unused
+
+/* Route upstream's "static linking only" entry points through
+ * LZ4LIB_VISIBILITY too.
+ */
+#define LZ4_PUBLISH_STATIC_FUNCTIONS
+
+/* Heap mode only: the stack mode puts LZ4HC's ~64K opt[] in a frame.
+ * Allocation goes through the failing stubs below; upstream handles
+ * NULL by returning 0.
+ */
+#define LZ4_USER_MEMORY_FUNCTIONS
+#define LZ4_HEAPMODE 1
+#define LZ4HC_HEAPMODE 1
+
+/* Failing stubs; nothing in the kernel reaches these. */
+static void *LZ4_malloc(size_t s) { return NULL; }
+static void *LZ4_calloc(size_t n, size_t s) { return NULL; }
+static void LZ4_free(void *p) { }
+
+/* Left alone, upstream reads unaligned words through packed structs, and
+ * on ARMv6 through plain misaligned dereferences.  Use memcpy(), upstream's
+ * documented default, where unaligned access is cheap, and packed structs,
+ * as get_unaligned() does, where it is not: there GCC builds a memcpy()'d
+ * word through a stack slot.
+ */
+#ifdef CONFIG_HAVE_EFFICIENT_UNALIGNED_ACCESS
+#define LZ4_FORCE_MEMORY_ACCESS 0
+#else
+#define LZ4_FORCE_MEMORY_ACCESS 1
+#endif
+
+/* On ppc64le GCC, lz4.c marks its decompression entry points and every
+ * LZ4_FORCE_INLINE helper optimize("O2"), which makes GCC forget command
+ * line options such as -fno-strict-aliasing for those functions (see commit
+ * 080b6f407635).  Expand the attribute to nothing; lz4_kernel_api.h undoes
+ * this.
+ */
+#define optimize(level)
+
+/* lz4.c sets this before including lz4.h, since its own code calls
+ * deprecated entry points.  lz4.h is included below, ahead of lz4.c.
+ */
+#define LZ4_DISABLE_DEPRECATE_WARNINGS 1
+
+/* Rename upstream's entry points out of the way; four of them take a
+ * trailing wrkmem argument in the kernel.
+ */
+#define LZ4_compress_fast		__lz4_compress_fast
+#define LZ4_compress_default		__lz4_compress_default
+#define LZ4_compress_destSize		__lz4_compress_destSize
+#define LZ4_resetStream			__lz4_resetStream
+#define LZ4_loadDict			__lz4_loadDict
+#define LZ4_saveDict			__lz4_saveDict
+#define LZ4_compress_fast_continue	__lz4_compress_fast_continue
+
+#define LZ4_decompress_safe		__lz4_decompress_safe
+#define LZ4_
```
