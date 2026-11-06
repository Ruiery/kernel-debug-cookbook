---
title: [PATCH v2 11/15] lib/lz4: switch the HC compressor to the vendored sources
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-11-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-11-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 11/15] lib/lz4: switch the HC compressor to the vendored sources

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-11-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-11-ee04c3f0d7dc@samsung.com/)

```
Replace the forked LZ4HC with thin entry points over the vendored
lz4hc.c.

Upstream routes levels 10 and up to its optimal parser, whose ~64K
workspace the kernel cannot provide. Clamp those levels to 9 rather than
reject them, so existing f2fs and zram settings keep working, and add
LZ4HC_CLAMP_CLEVEL to <linux/lz4.h>. Document the clamp in f2fs.rst.

Levels 1 and 2 now use upstream's lz4mid: on kernel source they are
50-84% faster for 4-9% larger output. Levels 3 to 9 compress the same,
but at 4K are up to 15% slower on poorly compressible data, including at
level 9, zram's lz4hc default.

LZ4_compress_HC() and LZ4_resetStreamHC() check the state's alignment
like the compressor's entry points.

LZ4_streamHC_t becomes incomplete and the macros that laid out the forked
structure go. LZ4HC_MEM_COMPRESS grows from 262192 to upstream's 262200,
static_asserted against LZ4_STREAMHC_MINSIZE. lz4hc.c pulls in lz4.c's
decoder tables, unused here when the fast decode loop is off, so silence
-Wunused-const-variable for this object.

This retires commit b08918fb3f27 ("lz4: do not export static symbol"):
the glue exports only the five LZ4HC entry points.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 Documentation/filesystems/f2fs.rst |   2 +
 drivers/block/zram/backend_lz4hc.c |   2 +-
 include/linux/lz4.h                |  54 +--
 lib/lz4/Makefile                   |   4 +
 lib/lz4/lz4hc_compress.c           | 792 ++++---------------------------------
 5 files changed, 91 insertions(+), 763 deletions(-)

diff --git a/Documentation/filesystems/f2fs.rst b/Documentation/filesystems/f2fs.rst
index 771216f45207a797356d5d2a10328b74d1ab302a..4a2d4545c2752cbcea4939839ba3d2457bf92299 100644
--- a/Documentation/filesystems/f2fs.rst
+++ b/Documentation/filesystems/f2fs.rst
@@ -318,6 +318,8 @@ compress_algorithm=%s:%d Control compress algorithm and its compress level, now,
 				 zstd           1 - 22
 				 =========      ===========
 
+			 lz4 levels above 9 compress as level 9.
+
 compress_log_size=%u	 Support configuring compress cluster size. The size will
 			 be 4KB * (1 << %u). The default and minimum sizes are 16KB.
 compress_extension=%s	 Support adding specified extension, so that f2fs can enable
diff --git a/drivers/block/zram/backend_lz4hc.c b/drivers/block/zram/backend_lz4hc.c
index 06286c805cf7c56bd760f460cc854dc4014f293b..e7ee3740219852f079d1e0866da6b213a3f3a583 100644
--- a/drivers/block/zram/backend_lz4hc.c
+++ b/drivers/block/zram/backend_lz4hc.c
@@ -69,7 +69,7 @@ static int lz4hc_create(struct zcomp_params *params, struct zcomp_ctx *ctx)
 		if (!zctx->dstrm)
 			goto error;
 
-		zctx->cstrm = kzalloc_obj(*zctx->cstrm);
+		zctx->cstrm = kzalloc(LZ4HC_MEM_COMPRESS, GFP_KERNEL);
 		if (!zctx->cstrm)
 			goto error;
 		LZ4_resetStreamHC(zctx->cstrm, params->level);
diff --git a/include/linux/lz4.h b/include/linux/lz4.h
index 031a410b8e3878e9a24cc49af36cfcbba399d991..05060b9790be4621ddbe744172fa0ae37f6191f4 100644
--- a/include/linux/lz4.h
+++ b/include/linux/lz4.h
@@ -59,19 +59,16 @@
 #define LZ4HC_DEFAULT_CLEVEL			9
 #define LZ4HC_MAX_CLEVEL			16
 
-#define LZ4HC_DICTIONARY_LOGSIZE 16
-#define LZ4HC_MAXD (1<<LZ4HC_DICTIONARY_LOGSIZE)
-#define LZ4HC_MAXD_MASK (LZ4HC_MAXD - 1)
-#define LZ4HC_HASH_LOG (LZ4HC_DICTIONARY_LOGSIZE - 1)
-#define LZ4HC_HASHTABLESIZE (1 << LZ4HC_HASH_LOG)
-#define LZ4HC_HASH_MASK (LZ4HC_HASHTABLESIZE - 1)
+/* Levels from here up select the optimal parser, which needs a ~64K
+ * workspace lib/lz4 cannot give it, so lib/lz4 compresses them as
+ * LZ4HC_CLAMP_CLEVEL - 1.  f2fs and zram still accept levels up to
+ * LZ4HC_MAX_CLEVEL.
+ */
+#define LZ4HC_CLAMP_CLEVEL			10
 
 /*-************************************************************************
  *	STREAMING CONSTANTS AND STRUCTURES
  **************************************************************************/
-#define LZ4_STREAMHCSIZE        262192
-#define LZ4_STREAMHCSIZE_SIZET (262192 / sizeof(size_t))
-
 #define LZ4_STREAMDECODESIZE_U64	4
 #define LZ4_STREAMDECODESIZE		 (LZ4_STREAMDECODESIZE_U64 * \
 	sizeof(unsigned long long))
@@ -83,29 +80,10 @@
 typedef union LZ4_stream_u LZ4_stream_t;
 
 /*
- * LZ4_streamHC_t - information structure to track an LZ4HC stream.
+ * LZ4_streamHC_t - an LZ4HC stream.  Incomplete: lib/lz4 owns the layout.
+ * Allocate LZ4HC_MEM_COMPRESS bytes and cast, do not sizeof().
  */
-typedef struct {
-	unsigned int	 hashTable[LZ4HC_HASHTABLESIZE];
-	unsigned short	 chainTable[LZ4HC_MAXD];
-	/* next block to continue on current prefix */
-	const unsigned char *end;
-	/* All index relative to this position */
-	const unsigned char *base;
-	/* alternate base for extDict */
-	const unsigned char *dictBase;
-	/* below that point, need extDict */
-	unsigned int	 dictLimit;
-	/* below that point, no more dict */
-	unsigned int	 lowLimit;
-	/* index from which to continue dict update */
-	unsigned int	 nextToUpdate;
-	unsigned int	 compressionLevel;
-} LZ4HC_CCtx_internal;
-typedef union {
-	size_t table[LZ4_STREAMHCSIZE_SIZET];
-	LZ4HC_CCtx_internal internal_donotuse;
-} LZ4_streamHC_t;
+typedef union LZ4_streamHC_u LZ4_streamHC_t;
 
 /*
  * LZ4_streamDecode_t - information structure to track an
@@ -133,7 +111,7 @@ typedef union {
  * points warn about a misaligned buffer and fail the call.
  */
 #define LZ4_MEM_COMPRESS	16416
-#define LZ4HC_MEM_COMPRESS	LZ4_STREAMHCSIZE
+#define LZ4HC_MEM_COMPRESS	262200
 
 /*-************************************************************************
  *	Compression Functions
@@ -289,9 +267,9 @@ int LZ4_decompress_safe_partial(const char *source, char *dest,
  * @srcSize: size of the input data. Max supported value is LZ4_MAX_INPUT_SIZE
  * @dstCapacity: full or partial size of buffer 'dst',
  *	which must be already allocated
- * @compressionLevel: Recommended values are between 4 and 9, although any
- *	value between 1 and LZ4HC_MAX_CLEVEL will work.
- *	Values >LZ4HC_MAX_CLEVEL behave the same as 16.
+ * @compressionLevel: Recommended values are between 4 and 9.  Levels of
+ *	LZ4HC_CLAMP_CLEVEL and above are clamped to LZ4HC_CLAMP_CLEVEL - 1;
+ *	see that macro.
  * @wrkmem: address of the working memory.
  *	This requires 'wrkmem' of size LZ4HC_MEM_COMPRESS, aligned to 8 bytes.
  *
@@ -307,9 +285,9 @@ int LZ4_compress_HC(const char *src, char *dst, int srcSize, int dstCapacity,
 /**
  * LZ4_resetStreamHC() - Init an allocated 'LZ4_streamHC_t' structure
  * @streamHCPtr: pointer to the 'LZ4_streamHC_t' structure
- * @compressionLevel: Recommended values are between 4 and 9, although any
- *	value between 1 and LZ4HC_MAX_CLEVEL will work.
- *	Values >LZ4HC_MAX_CLEVEL behave the same as 16.
+ * @compressionLevel: Recommended values are between 4 and 9.  Levels of
+ *	LZ4HC_CLAMP_CLEVEL and above are clamped to LZ4HC_CLAMP_CLEVEL - 1;
+ *	see that macro.
  *
  * An LZ4_streamHC_t structure can be allocated once
  * and re-used multiple times.
diff --git a/lib/lz4/Makefile b/lib/lz4/Makefile
index 8b4eb07694e67dd99ec7cc85212fb68138d3981e..5cbbe10beedce1199dee68992d542a1e52f89f8e 100644
--- a/lib/lz4/Makefile
+++ b/lib/lz4/Makefile
@@ -10,3 +10,7 @@ ccflags-y += -I $(src)/freestanding
 obj-$(CONFIG_LZ4_COMPRESS)	+= lz4_compress.o
 obj-$(CONFIG_LZ4HC_COMPRESS)	+= lz4hc_compress.o
 obj-$(CONFIG_LZ4_DECOMPRESS)	+= lz4_decompress.o
+
+# lz4hc.c pulls in lz4.c's common definitions, which include two decoder
+# tables nothing here uses when LZ4_FAST_DEC_LOOP is off.
+CFLAGS_lz4hc_compress.o += $(call cc-disable-warning, unused-const-variable)
diff --git a/lib/lz4/lz4hc_compress.c b/lib/lz4/lz4hc_compress.c
index 91936dc3d14bca31752a361693380aad8eb3b98a..4d56d45028110805628be766b2758a8dffd56f0c 100644
--- a/lib/lz4/lz4hc_compress.c
+++ b/lib/lz4/lz4hc_compress.c
@@ -1,766 +1,110 @@
+// SPDX-License-Identifier: GPL-2.0-only OR BSD-2-Clause
 /*
- * LZ4 HC - High Compression Mode of LZ4
- * Copyright (C) 2011-2015, Yann Collet.
+ * Copyright (C) 2011 - 2016, Yann Collet.
+ * Copyright (C) 2016, Sven Schmidt <4sschmid@in
```
