---
title: [PATCH RFC 5/9] lib/lz4: switch the compressor to the vendored sources
list: linux-block
message_id: 20260925-lz4-vendor-upstream-v1-5-1c7ffbe21c4b@samsung.com
link: https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-5-1c7ffbe21c4b@samsung.com/
---

# [PATCH RFC 5/9] lib/lz4: switch the compressor to the vendored sources

来源：[https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-5-1c7ffbe21c4b@samsung.com/](https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-5-1c7ffbe21c4b@samsung.com/)

```
Replace the forked compressor with thin entry points over the vendored
lz4.c.

LZ4_compress_default(), LZ4_compress_fast() and LZ4_compress_destSize()
keep the trailing wrkmem argument and forward to upstream's *_extState()
entry points. The rest are plain forwarders.

Compressed output is not quite bit-for-bit identical: it differs on a
small fraction of inputs by a byte or two, with no measurable change in
ratio. Both implementations decode each other's output, so nothing
already on disk changes meaning.

<linux/lz4.h> spelled out LZ4_stream_t's layout for the fork's benefit:
lz4defs.h included the public header and the fork read internal_donotuse
back out. The vendored compressor brings upstream's own definition, so
make the public type incomplete, repeating upstream's forward
declaration. Both headers then name the same type, which
lib/decompress_unlz4.c needs since it ends up including both.

LZ4_MEMORY_USAGE, LZ4_HASHLOG, LZ4_HASHTABLESIZE, LZ4_HASH_SIZE_U32,
LZ4_STREAMSIZE_U64 and LZ4_STREAMSIZE only existed to lay that structure
out, and go with it. LZ4_MEM_COMPRESS keeps its value, 16416, as a
plain number.

Callers now allocate LZ4_MEM_COMPRESS bytes instead of
sizeof(LZ4_stream_t). Every caller but zram already did; zram is
adjusted here.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 drivers/block/zram/backend_lz4.c |   6 +-
 include/linux/lz4.h              |  47 +-
 lib/lz4/Makefile                 |  11 +-
 lib/lz4/lz4_compress.c           | 941 ++-------------------------------------
 4 files changed, 68 insertions(+), 937 deletions(-)

diff --git a/drivers/block/zram/backend_lz4.c b/drivers/block/zram/backend_lz4.c
index 1e4ad31d39a63f45b3bddd3d8a467d8d7d095beb..50265e3ce256490994cb6dae32a45da376e408e0 100644
--- a/drivers/block/zram/backend_lz4.c
+++ b/drivers/block/zram/backend_lz4.c
@@ -42,7 +42,7 @@ static int lz4_setup_params(struct zcomp_params *params)
 	if (!params->dict || !params->dict_sz)
 		return 0;
 
-	dict_stream = kzalloc_obj(*dict_stream);
+	dict_stream = kzalloc(LZ4_MEM_COMPRESS, GFP_KERNEL);
 	if (!dict_stream)
 		return -ENOMEM;
 
@@ -88,7 +88,7 @@ static int lz4_create(struct zcomp_params *params, struct zcomp_ctx *ctx)
 		if (!zctx->dstrm)
 			goto error;
 
-		zctx->cstrm = kzalloc_obj(*zctx->cstrm);
+		zctx->cstrm = kzalloc(LZ4_MEM_COMPRESS, GFP_KERNEL);
 		if (!zctx->cstrm)
 			goto error;
 	}
@@ -112,7 +112,7 @@ static int lz4_compress(struct zcomp_params *params, struct zcomp_ctx *ctx,
 					zctx->mem);
 	} else {
 		/* Cstrm needs to be reset */
-		memcpy(zctx->cstrm, params->drv_data, sizeof(*zctx->cstrm));
+		memcpy(zctx->cstrm, params->drv_data, LZ4_MEM_COMPRESS);
 		ret = LZ4_compress_fast_continue(zctx->cstrm, req->src,
 						 req->dst, req->src_len,
 						 req->dst_len, params->level);
diff --git a/include/linux/lz4.h b/include/linux/lz4.h
index ad6042a718b5428792b795db7a8d4ad44c24a985..e96353a67d617a4d734cecaf3764814df692428b 100644
--- a/include/linux/lz4.h
+++ b/include/linux/lz4.h
@@ -47,16 +47,6 @@
 /*-************************************************************************
  *	CONSTANTS
  **************************************************************************/
-/*
- * LZ4_MEMORY_USAGE :
- * Memory usage formula : N->2^N Bytes
- * (examples : 10 -> 1KB; 12 -> 4KB ; 16 -> 64KB; 20 -> 1MB; etc.)
- * Increasing memory usage improves compression ratio
- * Reduced memory usage can improve speed, due to cache effect
- * Default value is 14, for 16KB, which nicely fits into Intel x86 L1 cache
- */
-#define LZ4_MEMORY_USAGE 14
-
 #define LZ4_MAX_INPUT_SIZE	0x7E000000 /* 2 113 929 216 bytes */
 #define LZ4_COMPRESSBOUND(isize)	(\
 	(unsigned int)(isize) > (unsigned int)LZ4_MAX_INPUT_SIZE \
@@ -64,9 +54,6 @@
 	: (isize) + ((isize)/255) + 16)
 
 #define LZ4_ACCELERATION_DEFAULT 1
-#define LZ4_HASHLOG	 (LZ4_MEMORY_USAGE-2)
-#define LZ4_HASHTABLESIZE (1 << LZ4_MEMORY_USAGE)
-#define LZ4_HASH_SIZE_U32 (1 << LZ4_HASHLOG)
 
 #define LZ4HC_MIN_CLEVEL			3
 #define LZ4HC_DEFAULT_CLEVEL			9
@@ -82,9 +69,6 @@
 /*-************************************************************************
  *	STREAMING CONSTANTS AND STRUCTURES
  **************************************************************************/
-#define LZ4_STREAMSIZE_U64 ((1 << (LZ4_MEMORY_USAGE - 3)) + 4)
-#define LZ4_STREAMSIZE	(LZ4_STREAMSIZE_U64 * sizeof(unsigned long long))
-
 #define LZ4_STREAMHCSIZE        262192
 #define LZ4_STREAMHCSIZE_SIZET (262192 / sizeof(size_t))
 
@@ -93,20 +77,10 @@
 	sizeof(unsigned long long))
 
 /*
- * LZ4_stream_t - information structure to track an LZ4 stream.
+ * LZ4_stream_t - an LZ4 stream.  Incomplete: lib/lz4 owns the layout.
+ * Allocate LZ4_MEM_COMPRESS bytes and cast, do not sizeof().
  */
-typedef struct {
-	uint32_t hashTable[LZ4_HASH_SIZE_U32];
-	uint32_t currentOffset;
-	uint32_t initCheck;
-	const uint8_t *dictionary;
-	uint8_t *bufferStart;
-	uint32_t dictSize;
-} LZ4_stream_t_internal;
-typedef union {
-	unsigned long long table[LZ4_STREAMSIZE_U64];
-	LZ4_stream_t_internal internal_donotuse;
-} LZ4_stream_t;
+typedef union LZ4_stream_u LZ4_stream_t;
 
 /*
  * LZ4_streamHC_t - information structure to track an LZ4HC stream.
@@ -153,7 +127,12 @@ typedef union {
 /*-************************************************************************
  *	SIZE OF STATE
  **************************************************************************/
-#define LZ4_MEM_COMPRESS	LZ4_STREAMSIZE
+/*
+ * Working memory for the compressors.  It must be aligned to at least 8
+ * bytes; anything from kmalloc() or vmalloc() already is.  A misaligned
+ * buffer is rejected, and the stateless entry points cannot report that.
+ */
+#define LZ4_MEM_COMPRESS	16416
 #define LZ4HC_MEM_COMPRESS	LZ4_STREAMHCSIZE
 
 /*-************************************************************************
@@ -180,7 +159,7 @@ static inline int LZ4_compressBound(size_t isize)
  * @maxOutputSize: full or partial size of buffer 'dest'
  *	which must be already allocated
  * @wrkmem: address of the working memory.
- *	This requires 'workmem' of LZ4_MEM_COMPRESS.
+ *	This requires 'workmem' of LZ4_MEM_COMPRESS, aligned to 8 bytes.
  *
  * Compresses 'sourceSize' bytes from buffer 'source'
  * into already allocated 'dest' buffer of size 'maxOutputSize'.
@@ -206,7 +185,7 @@ int LZ4_compress_default(const char *source, char *dest, int inputSize,
  *	which must be already allocated
  * @acceleration: acceleration factor
  * @wrkmem: address of the working memory.
- *	This requires 'workmem' of LZ4_MEM_COMPRESS.
+ *	This requires 'workmem' of LZ4_MEM_COMPRESS, aligned to 8 bytes.
  *
  * Same as LZ4_compress_default(), but allows to select an "acceleration"
  * factor. The larger the acceleration value, the faster the algorithm,
@@ -230,7 +209,7 @@ int LZ4_compress_fast(const char *source, char *dest, int inputSize,
  *	from 'source' to fill 'dest'. New value is necessarily <= old value.
  * @targetDestSize: Size of buffer 'dest' which must be already allocated
  * @wrkmem: address of the working memory.
- *	This requires 'workmem' of LZ4_MEM_COMPRESS.
+ *	This requires 'workmem' of LZ4_MEM_COMPRESS, aligned to 8 bytes.
  *
  * Reverse the logic, by compressing as much data as possible
  * from 'source' buffer into already allocated buffer 'dest'
@@ -335,7 +314,7 @@ int LZ4_decompress_safe_partial(const char *source, char *dest,
  *	value between 1 and LZ4HC_MAX_CLEVEL will work.
  *	Values >LZ4HC_MAX_CLEVEL behave the same as 16.
  * @wrkmem: address of the working memory.
- *	This requires 'wrkmem' of size LZ4HC_MEM_COMPRESS.
+ *	This requires 'wrkmem' of size LZ4HC_MEM_COMPRESS, aligned to 8 bytes.
  *
  * Compress data from 'src' into 'dst', using the more powerful
  * but slower "HC" algorithm. Compression is guaranteed to succeed if
diff --git a/lib/lz4/Makefile b/lib/lz4/Makefile
index 5b42242afaa20deb165d8a2f0b1c0c842dfcdc39..e9d83cff4ea4efe1097f54caba72e268cecb04af 100644
--- a/lib/lz4/Makefile
+++ b/lib/lz4/Makefile
@@ -1,6 +1,11 @@
 # SPD
```
