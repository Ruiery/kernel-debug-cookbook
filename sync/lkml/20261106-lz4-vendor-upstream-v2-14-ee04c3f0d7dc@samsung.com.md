---
title: [PATCH v2 14/15] lib/lz4: replace lz4_kernel_api.h's prototypes with <linux/lz4.h>
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-14-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-14-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 14/15] lib/lz4: replace lz4_kernel_api.h's prototypes with <linux/lz4.h>

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-14-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-14-ee04c3f0d7dc@samsung.com/)

```
lz4_kernel_api.h carried its own copy of the twenty public prototypes
because it could not include <linux/lz4.h>, which defined the stream
types that upstream's headers also define.

The types are incomplete now, so it can. Two prototype lists for one
ABI is a drift hazard: the entry points were built against one and their
callers against the other, so no compiler ever saw both, and MODVERSIONS
would not catch a mismatch either, since it hashes the exporter's view
only. Now there is one list.

It also puts the public constants in scope of the entry points, so the
size assertions can name them, and the HC level clamp can use
LZ4HC_CLAMP_CLEVEL, static_asserted equal to upstream's
LZ4HC_CLEVEL_OPT_MIN.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 lib/lz4/lz4_compress.c   |  2 +-
 lib/lz4/lz4_decompress.c |  2 +-
 lib/lz4/lz4_kernel_api.h | 64 +++---------------------------------------------
 lib/lz4/lz4hc_compress.c |  8 +++---
 4 files changed, 11 insertions(+), 65 deletions(-)

diff --git a/lib/lz4/lz4_compress.c b/lib/lz4/lz4_compress.c
index 941e32a19ac972aef543c9a03b447a8a98bf5215..3e272584ea0c905b48b6bf0b7e77acfbad131bd1 100644
--- a/lib/lz4/lz4_compress.c
+++ b/lib/lz4/lz4_compress.c
@@ -30,7 +30,7 @@
 
 /* Catch any divergence from upstream's layout at build time. */
 static_assert(sizeof(LZ4_stream_t) == LZ4_STREAM_MINSIZE);
-static_assert(LZ4_STREAM_MINSIZE == 16416); /* LZ4_MEM_COMPRESS */
+static_assert(LZ4_STREAM_MINSIZE == LZ4_MEM_COMPRESS);
 
 /* LZ4_initStream() returns NULL for a misaligned state, which
  * LZ4_compress_fast_extState() dereferences and
diff --git a/lib/lz4/lz4_decompress.c b/lib/lz4/lz4_decompress.c
index 60b57862a2e387aa89fa26f6f8e2b5485b5d9995..5d68a6f59a62ddb3701dd3531cf606c05ef4e607 100644
--- a/lib/lz4/lz4_decompress.c
+++ b/lib/lz4/lz4_decompress.c
@@ -31,7 +31,7 @@
 #endif
 
 static_assert(sizeof(LZ4_streamDecode_t) == LZ4_STREAMDECODE_MINSIZE);
-static_assert(LZ4_STREAMDECODE_MINSIZE == 32); /* LZ4_MEM_DECOMPRESS */
+static_assert(LZ4_STREAMDECODE_MINSIZE == LZ4_MEM_DECOMPRESS);
 
 int LZ4_decompress_safe(const char *source, char *dest, int compressedSize,
 			int maxDecompressedSize)
diff --git a/lib/lz4/lz4_kernel_api.h b/lib/lz4/lz4_kernel_api.h
index de75e5d976eb9dd318da5318a26b91d7aed81042..43605a0e4d7f543662af83251184968f0d1b70dd 100644
--- a/lib/lz4/lz4_kernel_api.h
+++ b/lib/lz4/lz4_kernel_api.h
@@ -3,19 +3,10 @@
  * Copyright (c) 2026 Samsung Electronics Co., Ltd.
  * Author: Michal Wilczynski <m.wilczynski@samsung.com>
  *
- * lz4_kernel_api.h -- the LZ4 API this directory exports
+ * lz4_kernel_api.h -- hand the LZ4 names back to the kernel
  *
- * lz4_deps.h renames upstream's entry points to __lz4_* so that the kernel's
- * own definitions can use the real names; this header undoes that renaming
- * and the optimize() override, and declares what lib/lz4 exports.
- *
- * The same functions are declared to callers in <linux/lz4.h>, in terms of
- * opaque stream types.  We cannot include that header here -- it and
- * upstream's lz4.h describe the same library and collide -- so the
- * declarations are repeated, expressed in upstream's own types.  Keep the two
- * in step; <linux/lz4.h> is the one callers compile against.
- *
- * Include after upstream/lz4.c or upstream/lz4hc.c.
+ * Undo lz4_deps.h's renaming and its optimize() override, and pull in
+ * <linux/lz4.h>.  Include after upstream/lz4.c or upstream/lz4hc.c.
  */
 
 #undef LZ4_compress_fast
@@ -40,51 +31,4 @@
 
 #undef optimize
 
-/*
- * The objects that do not build lz4hc.c never see this type, and it is only
- * ever used through a pointer here.  Upstream declares it the same way.
- */
-typedef union LZ4_streamHC_u LZ4_streamHC_t;
-
-/* Compression.  wrkmem is LZ4_MEM_COMPRESS bytes, supplied by the caller. */
-int LZ4_compress_default(const char *source, char *dest, int inputSize,
-			 int maxOutputSize, void *wrkmem);
-int LZ4_compress_fast(const char *source, char *dest, int inputSize,
-		      int maxOutputSize, int acceleration, void *wrkmem);
-int LZ4_compress_destSize(const char *source, char *dest, int *sourceSizePtr,
-			  int targetDestSize, void *wrkmem);
-
-/* Streaming compression. */
-void LZ4_resetStream(LZ4_stream_t *LZ4_stream);
-int LZ4_loadDict(LZ4_stream_t *streamPtr, const char *dictionary,
-		 int dictSize);
-int LZ4_saveDict(LZ4_stream_t *streamPtr, char *safeBuffer, int dictSize);
-int LZ4_compress_fast_continue(LZ4_stream_t *streamPtr, const char *src,
-			       char *dst, int srcSize, int maxDstSize,
-			       int acceleration);
-
-/* Decompression. */
-int LZ4_decompress_safe(const char *source, char *dest, int compressedSize,
-			int maxDecompressedSize);
-int LZ4_decompress_safe_partial(const char *source, char *dest,
-				int compressedSize, int targetOutputSize,
-				int maxDecompressedSize);
-int LZ4_setStreamDecode(LZ4_streamDecode_t *LZ4_streamDecode,
-			const char *dictionary, int dictSize);
-int LZ4_decompress_safe_continue(LZ4_streamDecode_t *LZ4_streamDecode,
-				 const char *source, char *dest,
-				 int compressedSize, int maxDecompressedSize);
-int LZ4_decompress_safe_usingDict(const char *source, char *dest,
-				  int compressedSize, int maxDecompressedSize,
-				  const char *dictStart, int dictSize);
-
-/* HC compression.  wrkmem is LZ4HC_MEM_COMPRESS bytes. */
-int LZ4_compress_HC(const char *src, char *dst, int srcSize, int dstCapacity,
-		    int compressionLevel, void *wrkmem);
-void LZ4_resetStreamHC(LZ4_streamHC_t *streamHCPtr, int compressionLevel);
-int LZ4_loadDictHC(LZ4_streamHC_t *streamHCPtr, const char *dictionary,
-		   int dictSize);
-int LZ4_compress_HC_continue(LZ4_streamHC_t *streamHCPtr, const char *src,
-			     char *dst, int srcSize, int maxDstSize);
-int LZ4_saveDictHC(LZ4_streamHC_t *streamHCPtr, char *safeBuffer,
-		   int maxDictSize);
+#include <linux/lz4.h>
diff --git a/lib/lz4/lz4hc_compress.c b/lib/lz4/lz4hc_compress.c
index 4d56d45028110805628be766b2758a8dffd56f0c..4f40a12df17cfed2bab7f5d87ac087b4d423cef7 100644
--- a/lib/lz4/lz4hc_compress.c
+++ b/lib/lz4/lz4hc_compress.c
@@ -39,7 +39,7 @@ static int LZ4_compressBound(int isize)
 
 /* Catch any divergence from upstream's layout at build time. */
 static_assert(sizeof(LZ4_streamHC_t) == LZ4_STREAMHC_MINSIZE);
-static_assert(LZ4_STREAMHC_MINSIZE == 262200); /* LZ4HC_MEM_COMPRESS */
+static_assert(LZ4_STREAMHC_MINSIZE == LZ4HC_MEM_COMPRESS);
 
 /* Levels >= LZ4HC_CLEVEL_OPT_MIN (10) reach the optimal parser, which needs
  * a ~64K opt[]: too big for a kernel stack, and in the heap mode lz4_deps.h
@@ -48,10 +48,12 @@ static_assert(LZ4_STREAMHC_MINSIZE == 262200); /* LZ4HC_MEM_COMPRESS */
  * working.  Levels 3..9 keep their meaning; 1 and 2 are upstream's lz4mid,
  * faster and weaker than the shallow hash chain the fork used for them.
  */
+static_assert(LZ4HC_CLAMP_CLEVEL == LZ4HC_CLEVEL_OPT_MIN);
+
 static int lz4hc_clamp_level(int compressionLevel)
 {
-	if (compressionLevel >= LZ4HC_CLEVEL_OPT_MIN)
-		return LZ4HC_CLEVEL_OPT_MIN - 1;
+	if (compressionLevel >= LZ4HC_CLAMP_CLEVEL)
+		return LZ4HC_CLAMP_CLEVEL - 1;
 
 	return compressionLevel;
 }

-- 
2.34.1
```
