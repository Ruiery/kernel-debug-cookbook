---
title: [PATCH RFC 7/9] lib/lz4: switch the decompressor to the vendored sources
list: linux-block
message_id: 20260925-lz4-vendor-upstream-v1-7-1c7ffbe21c4b@samsung.com
link: https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-7-1c7ffbe21c4b@samsung.com/
---

# [PATCH RFC 7/9] lib/lz4: switch the decompressor to the vendored sources

来源：[https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-7-1c7ffbe21c4b@samsung.com/](https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-7-1c7ffbe21c4b@samsung.com/)

```
Replace the forked decompressor with thin entry points over the vendored
lz4.c. The API is already signature-compatible, so every export is a
plain forwarder. lz4defs.h has no users left and goes.

lib/decompress_unlz4.c still includes this file for the pre-boot
decompressor; the exports stay behind #ifndef STATIC.

That include is why LZ4_streamDecode_t is incomplete: under PREBOOT the
translation unit has both <linux/lz4.h> and upstream's lz4.h, so both
must name the same type. Both repeat upstream's forward declaration,
and the file builds without guards.

LZ4_streamDecode_t is the last of the three, so LZ4_STREAMDECODESIZE and
LZ4_STREAMDECODESIZE_U64 go and LZ4_MEM_DECOMPRESS takes over, 32 bytes.

LZ4_COMPRESSBOUND is likewise defined by both headers; guard it.
LZ4_compressBound() cannot be guarded, so drop the inline wrapper:
lib/decompress_unlz4.c was its only caller and uses the macro now.

This picks up upstream's decoder fixes since v1.8.3 and retires six
local patches:

commit 8cb5d7482810 ("lib/lz4: make arrays static const, reduces object code size")
commit b1a3e75e466d ("lz4: fix kernel decompression speed")
commit 89b158635ad7 ("lib/lz4: explicitly support in-place decompression")
commit 7fde9d6e839d ("lz4_decompress: declare LZ4_decompress_safe_withPrefix64k static")
commit eafc0a02391b ("lz4: fix LZ4_decompress_safe_partial read out of bound")
commit 2d8867f3e083 ("lib: make LZ4_decompress_safe_forceExtDict() static")

The decompression speed fix has an upstream equivalent, carried since
v1.9.3 as upstream commit fe2a1b3707d5
("Call LZ4_memcpy() instead of memcpy()").

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 drivers/block/zram/backend_lz4.c   |   2 +-
 drivers/block/zram/backend_lz4hc.c |   2 +-
 include/linux/lz4.h                |  51 +--
 lib/decompress_unlz4.c             |   4 +-
 lib/lz4/lz4_decompress.c           | 718 +++----------------------------------
 lib/lz4/lz4defs.h                  | 247 -------------
 6 files changed, 74 insertions(+), 950 deletions(-)

diff --git a/drivers/block/zram/backend_lz4.c b/drivers/block/zram/backend_lz4.c
index 50265e3ce256490994cb6dae32a45da376e408e0..b9b8a5f678c155442fa3fd2c1984e45182e6fc38 100644
--- a/drivers/block/zram/backend_lz4.c
+++ b/drivers/block/zram/backend_lz4.c
@@ -84,7 +84,7 @@ static int lz4_create(struct zcomp_params *params, struct zcomp_ctx *ctx)
 		if (!zctx->mem)
 			goto error;
 	} else {
-		zctx->dstrm = kzalloc_obj(*zctx->dstrm);
+		zctx->dstrm = kzalloc(LZ4_MEM_DECOMPRESS, GFP_KERNEL);
 		if (!zctx->dstrm)
 			goto error;
 
diff --git a/drivers/block/zram/backend_lz4hc.c b/drivers/block/zram/backend_lz4hc.c
index 894695753d99bf2fec7e191c4ec2fff489b5bddd..7fabd0e6d66095d411007bec5eaa8e5f553b626d 100644
--- a/drivers/block/zram/backend_lz4hc.c
+++ b/drivers/block/zram/backend_lz4hc.c
@@ -65,7 +65,7 @@ static int lz4hc_create(struct zcomp_params *params, struct zcomp_ctx *ctx)
 		if (!zctx->mem)
 			goto error;
 	} else {
-		zctx->dstrm = kzalloc_obj(*zctx->dstrm);
+		zctx->dstrm = kzalloc(LZ4_MEM_DECOMPRESS, GFP_KERNEL);
 		if (!zctx->dstrm)
 			goto error;
 
diff --git a/include/linux/lz4.h b/include/linux/lz4.h
index 0e617c096653ba122f466b019c68a30661e04989..22adf26904754b3a274274d6b77955eb119e463f 100644
--- a/include/linux/lz4.h
+++ b/include/linux/lz4.h
@@ -48,10 +48,16 @@
  *	CONSTANTS
  **************************************************************************/
 #define LZ4_MAX_INPUT_SIZE	0x7E000000 /* 2 113 929 216 bytes */
+
+/* lib/decompress_unlz4.c sees this header and, under PREBOOT, upstream's
+ * lz4.h too; both define this identically.
+ */
+#ifndef LZ4_COMPRESSBOUND
 #define LZ4_COMPRESSBOUND(isize)	(\
 	(unsigned int)(isize) > (unsigned int)LZ4_MAX_INPUT_SIZE \
 	? 0 \
 	: (isize) + ((isize)/255) + 16)
+#endif
 
 #define LZ4_ACCELERATION_DEFAULT 1
 
@@ -66,12 +72,8 @@
 #define LZ4HC_CLAMP_CLEVEL			10
 
 /*-************************************************************************
- *	STREAMING CONSTANTS AND STRUCTURES
+ *	STREAMING STRUCTURES
  **************************************************************************/
-#define LZ4_STREAMDECODESIZE_U64	4
-#define LZ4_STREAMDECODESIZE		 (LZ4_STREAMDECODESIZE_U64 * \
-	sizeof(unsigned long long))
-
 /*
  * LZ4_stream_t - an LZ4 stream.  Incomplete: lib/lz4 owns the layout.
  * Allocate LZ4_MEM_COMPRESS bytes and cast, do not sizeof().
@@ -85,21 +87,11 @@ typedef union LZ4_stream_u LZ4_stream_t;
 typedef union LZ4_streamHC_u LZ4_streamHC_t;
 
 /*
- * LZ4_streamDecode_t - information structure to track an
- *	LZ4 stream during decompression.
- *
- * init this structure using LZ4_setStreamDecode (or memset()) before first use
+ * LZ4_streamDecode_t - an LZ4 stream during decompression.  Incomplete:
+ * lib/lz4 owns the layout.  Allocate LZ4_MEM_DECOMPRESS bytes and cast, do
+ * not sizeof().  Init with LZ4_setStreamDecode() (or zero it) before use.
  */
-typedef struct {
-	const uint8_t *externalDict;
-	size_t extDictSize;
-	const uint8_t *prefixEnd;
-	size_t prefixSize;
-} LZ4_streamDecode_t_internal;
-typedef union {
-	unsigned long long table[LZ4_STREAMDECODESIZE_U64];
-	LZ4_streamDecode_t_internal internal_donotuse;
-} LZ4_streamDecode_t;
+typedef union LZ4_streamDecode_u LZ4_streamDecode_t;
 
 /*-************************************************************************
  *	SIZE OF STATE
@@ -111,23 +103,12 @@ typedef union {
  */
 #define LZ4_MEM_COMPRESS	16416
 #define LZ4HC_MEM_COMPRESS	262200
+#define LZ4_MEM_DECOMPRESS	32
 
 /*-************************************************************************
  *	Compression Functions
  **************************************************************************/
 
-/**
- * LZ4_compressBound() - Max. output size in worst case szenarios
- * @isize: Size of the input data
- *
- * Return: Max. size LZ4 may output in a "worst case" szenario
- * (data not compressible)
- */
-static inline int LZ4_compressBound(size_t isize)
-{
-	return LZ4_COMPRESSBOUND(isize);
-}
-
 /**
  * LZ4_compress_default() - Compress data from source to dest
  * @source: source address of the original data
@@ -141,7 +122,7 @@ static inline int LZ4_compressBound(size_t isize)
  * Compresses 'sourceSize' bytes from buffer 'source'
  * into already allocated 'dest' buffer of size 'maxOutputSize'.
  * Compression is guaranteed to succeed if
- * 'maxOutputSize' >= LZ4_compressBound(inputSize).
+ * 'maxOutputSize' >= LZ4_COMPRESSBOUND(inputSize).
  * It also runs faster, so it's a recommended setting.
  * If the function cannot compress 'source' into a more limited 'dest' budget,
  * compression stops *immediately*, and the function result is zero.
@@ -295,7 +276,7 @@ int LZ4_decompress_safe_partial(const char *source, char *dest,
  *
  * Compress data from 'src' into 'dst', using the more powerful
  * but slower "HC" algorithm. Compression is guaranteed to succeed if
- * `dstCapacity >= LZ4_compressBound(srcSize)
+ * `dstCapacity >= LZ4_COMPRESSBOUND(srcSize)
  *
  * Return : the number of bytes written into 'dst' or 0 if compression fails.
  */
@@ -359,7 +340,7 @@ int	LZ4_loadDictHC(LZ4_streamHC_t *streamHCPtr, const char *dictionary,
  * (including initial dictionary when present) must remain accessible
  * and unmodified during compression.
  * 'dst' buffer should be sized to handle worst case scenarios, using
- *  LZ4_compressBound(), to ensure operation success.
+ *  LZ4_COMPRESSBOUND(), to ensure operation success.
  *  If, for any reason, previous data blocks can't be preserved unmodified
  *  in memory during next compression block,
  *  you must save it to a safer memory space, using LZ4_saveDictHC().
@@ -455,7 +436,7 @@ int LZ4_saveDict(LZ4_stream_t *streamPtr, char *safeBuffer, int dictSize);
  * as dictionary to improve compression ratio.
  * Important : Previous data blocks are assumed to still
  * be present and unmodified !
- * If maxDstSize >= LZ4_compressBound(srcSize),
+ * If maxDstSize >= LZ4_COMPRESSBOUND(srcSize),
  * compression is guaranteed to
```
