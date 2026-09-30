---
title: [PATCH RFC 3/9] lib/lz4: add the build environment for the vendored sources
list: linux-block
message_id: 20260925-lz4-vendor-upstream-v1-3-1c7ffbe21c4b@samsung.com
link: https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-3-1c7ffbe21c4b@samsung.com/
---

# [PATCH RFC 3/9] lib/lz4: add the build environment for the vendored sources

来源：[https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-3-1c7ffbe21c4b@samsung.com/](https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-3-1c7ffbe21c4b@samsung.com/)

```
lz4_deps.h makes the unmodified upstream sources compile in the kernel:
it supplies the ISO C spellings they expect, gives every upstream entry
point internal linkage so an object carries only the codec it forwards,
keeps every workspace off the stack, and renames the entry points the
kernel re-exports with a trailing wrkmem argument.

freestanding/ forwards the four ISO C headers upstream includes
(stddef.h, stdint.h, limits.h, string.h) to their <linux/> equivalents.

The vendored functions an object does not forward are unreferenced, so
LZ4LIB_VISIBILITY carries __maybe_unused rather than disabling
-Wunused-function for a directory. This also covers the pre-boot
decompressors, which compile lz4_decompress.c textually and never see
lib/lz4's ccflags.

For the same reason this header includes <linux/build_bug.h>: the entry
points static_assert upstream's structure sizes, and only some
architectures' pre-boot environments have static_assert in scope.

lz4_kernel_api.h undoes the renaming for the entry point files and
declares what lib/lz4 exports. It starts out carrying its own copy of
those prototypes, because it cannot include <linux/lz4.h> while that
header still defines the three stream types upstream's headers also
define. A later patch folds it away once they are incomplete.

Nothing includes either header yet.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 lib/lz4/freestanding/limits.h | 14 +++++++
 lib/lz4/freestanding/stddef.h | 15 +++++++
 lib/lz4/freestanding/stdint.h | 14 +++++++
 lib/lz4/freestanding/string.h | 14 +++++++
 lib/lz4/lz4_deps.h            | 96 ++++++++++++++++++++++++++++++++++++++++++
 lib/lz4/lz4_kernel_api.h      | 98 +++++++++++++++++++++++++++++++++++++++++++
 6 files changed, 251 insertions(+)

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
index 0000000000000000000000000000000000000000..3855aac051585f216df71c5039cff19bcee37ca4
--- /dev/null
+++ b/lib/lz4/lz4_deps.h
@@ -0,0 +1,96 @@
+/* SPDX-License-Identifier: GPL-2.0-only OR BSD-2-Clause */
+/*
+ * Copyright (c) 2026 Samsung Electronics Co., Ltd.
+ * Author: Michal Wilczynski <m.wilczynski@samsung.com>
+ *
+ * Build environment for the vendored upstream LZ4 sources.
+ *
+ * The four files under upstream/ are copied verbatim; do not edit them.  The
+ * three entry point files include this header before them.
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
+/* Static so an object carries only the codec it forwards; __maybe_unused
+ * for the ones it does not, which the pre-boot decompressors compile
+ * without lib/lz4's ccflags.
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
+/* LZ4_decompress_fast() and LZ4_resetStream() are still kernel API. */
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
+#define LZ4_decompress_safe_partial	__lz4_decompress_safe_partial
+#define LZ4_decompress_fast		__lz4_decompress_fast
+#define LZ4_setStreamDecode		__lz4_setStreamDecode
+#define LZ4_decompress_safe_continue	__lz4_decompress_safe_continue
+#define LZ4_decompress_fast_continue	__lz4_decompress_fast_continue
+#define LZ4_decompress_safe_usingDict	__lz4_decompress_safe_usingDict
+#define LZ4_decompress_fast_usingDict	__lz4_decompress_fast_usingDict
+
+#define LZ4_compress_HC			__lz4_compress_HC
+#define LZ4_resetStreamHC		__lz4_resetStreamHC
+#define LZ4_loadDictHC			__lz4_loadDictHC
+#define LZ4_compress_HC_continue	__lz4_compress_HC_continue
+#define LZ4_saveDictHC			__lz4_saveDictHC
+
+/* Upstream declares these bare, so both entry point objects would define
+ * them.  Declaring them static first gives them internal linkage (C11
+ * 6.2.2p4): this one in lz4.h, the three below in lz4.c.
+ */
+static __maybe_unused int LZ4_compress_destSize_extState(void *state, const char *src,
+		char *dst, int *srcSizePtr, int targetDstSize,
+		int acceleration);
+
+#include "upstream/lz4.h"
+
+static __maybe_unus
```
