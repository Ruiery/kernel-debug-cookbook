---
title: [PATCH v2 13/15] lib/lz4: switch the decompressor to the vendored sources
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-13-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-13-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 13/15] lib/lz4: switch the decompressor to the vendored sources

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-13-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-13-ee04c3f0d7dc@samsung.com/)

```
Replace the forked decompressor with thin entry points over the vendored
lz4.c; the API is signature-compatible, so every export is a plain
forwarder. lz4defs.h has no users left and goes.

lib/decompress_unlz4.c includes this file before boot, together with
<linux/lz4.h>, so LZ4_streamDecode_t becomes incomplete as upstream
declares it, and LZ4_MEM_DECOMPRESS (32) replaces the
LZ4_STREAMDECODESIZE macros. LZ4_COMPRESSBOUND is defined by both
headers and gets a guard; the LZ4_compressBound() wrapper goes, as
lib/decompress_unlz4.c now uses the macro.

LZ4_decompress_safe_partial() on a truncated block can now return the
bytes decoded so far rather than an error, depending on where the cut
falls; the kernel-doc says so.

This retires six local patches:

commit 8cb5d7482810 ("lib/lz4: make arrays static const, reduces object code size")
  upstream 75fb878a9019 ("decompress_generic: Add fastpath for small offsets"), v1.9.0
commit b1a3e75e466d ("lz4: fix kernel decompression speed")
  upstream fe2a1b3707d5 ("Call LZ4_memcpy() instead of memcpy()"), v1.9.3
commit 89b158635ad7 ("lib/lz4: explicitly support in-place decompression")
  upstream 33cb8518ac38 ("decompress: changed final memcpy() into memmove()"), v1.9.2
commit 7fde9d6e839d ("lz4_decompress: declare LZ4_decompress_safe_withPrefix64k static")
  LZ4LIB_VISIBILITY in lz4_deps.h, which makes every upstream entry point static
commit eafc0a02391b ("lz4: fix LZ4_decompress_safe_partial read out of bound")
  upstream c5d6f8a8be39 ("fix #783"), v1.9.3
commit 2d8867f3e083 ("lib: make LZ4_decompress_safe_forceExtDict() static")
  the static forward declaration in lz4_deps.h

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 drivers/block/zram/backend_lz4.c   |   2 +-
 drivers/block/zram/backend_lz4hc.c |   2 +-
 include/linux/lz4.h                |  60 ++--
 lib/decompress_unlz4.c             |   4 +-
 lib/lz4/lz4_decompress.c           | 640 +++----------------------------------
 lib/lz4/lz4defs.h                  | 247 --------------
 6 files changed, 71 insertions(+), 884 deletions(-)

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
index e7ee3740219852f079d1e0866da6b213a3f3a583..1e09c93016264259c149e2913b2819571b56fab6 100644
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
index e809149747c3dc97d129e42e0ce4385b5a219930..fd9d7a162e04655a9d19639515466a6ba8e1e892 100644
--- a/include/linux/lz4.h
+++ b/include/linux/lz4.h
@@ -48,10 +48,16 @@
  *	CONSTANTS
  **************************************************************************/
 #define LZ4_MAX_INPUT_SIZE	0x7E000000 /* 2 113 929 216 bytes */
+
+/* Upstream's lz4.h defines the same macro, and lib/lz4's entry points and
+ * the pre-boot lib/decompress_unlz4.c see both headers.
+ */
+#ifndef LZ4_COMPRESSBOUND
 #define LZ4_COMPRESSBOUND(isize)	(\
 	(unsigned int)(isize) > (unsigned int)LZ4_MAX_INPUT_SIZE \
 	? 0 \
 	: (isize) + ((isize)/255) + 16)
+#endif
 
 #define LZ4_ACCELERATION_DEFAULT 1
 
@@ -67,12 +73,8 @@
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
@@ -86,21 +88,11 @@ typedef union LZ4_stream_u LZ4_stream_t;
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
@@ -112,23 +104,12 @@ typedef union {
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
@@ -142,7 +123,7 @@ static inline int LZ4_compressBound(size_t isize)
  * Compresses 'sourceSize' bytes from buffer 'source'
  * into already allocated 'dest' buffer of size 'maxOutputSize'.
  * Compression is guaranteed to succeed if
- * 'maxOutputSize' >= LZ4_compressBound(inputSize).
+ * 'maxOutputSize' >= LZ4_COMPRESSBOUND(inputSize).
  * It also runs faster, so it's a recommended setting.
  * If the function cannot compress 'source' into a more limited 'dest' budget,
  * compression stops *immediately*, and the function result is zero.
@@ -234,7 +215,7 @@ int LZ4_decompress_safe(const char *source, char *dest, int compressedSize,
  * @source: source address of the compressed data
  * @dest: output buffer address of the decompressed data which must be
  *	already allocated
- * @compressedSize: is the precise full size of the compressed block.
+ * @compressedSize: size of the compressed data at 'source'
  * @targetOutputSize: the decompression operation will try
  *	to stop as soon as 'targetOutputSize' has been reached
  * @maxDecompressedSize: is the size of destination buffer
@@ -249,8 +230,11 @@ int LZ4_decompress_safe(const char *source, char *dest, int compressedSize,
  * It is therefore protected against malicious data packets.
  *
  * Return: the number of bytes decoded in the destination buffer
- *	(necessarily <= maxDecompressedSize)
- *	or a negative result in case of error
+ *	(necessarily <= targetOutputSize and maxDecompressedSize)
+ *	or a negative result in case of error.  For a block cut short the
+ *	result is either the bytes decoded so far, below targetOutputSize,
+ *	or an error, depending on where the cut falls; check it against the
+ *	size you expect.
  *
  */
 int LZ4_decompress_safe_partial(const char *source, char *dest,
@@ -275,7 +259,7 @@ int LZ4_decompress_safe_partial(const char
```
