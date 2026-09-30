---
title: [PATCH RFC 6/9] lib/lz4: switch the HC compressor to the vendored sources
list: linux-block
message_id: 20260925-lz4-vendor-upstream-v1-6-1c7ffbe21c4b@samsung.com
link: https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-6-1c7ffbe21c4b@samsung.com/
---

# [PATCH RFC 6/9] lib/lz4: switch the HC compressor to the vendored sources

来源：[https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-6-1c7ffbe21c4b@samsung.com/](https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-6-1c7ffbe21c4b@samsung.com/)

```
Replace the forked LZ4HC with thin entry points over the vendored
lz4hc.c.

The HC entry points clamp the level below LZ4HC_CLEVEL_OPT_MIN, since
upstream routes levels 10 and up to the optimal parser whose ~64K
workspace does not fit a kernel stack. Levels are clamped rather than
rejected so existing f2fs and zram settings keep working; they now
compress as level 9.

f2fs and zram both take user levels up to LZ4HC_MAX_CLEVEL, so
<linux/lz4.h> gains LZ4HC_CLAMP_CLEVEL and says what happens at or above
it. A later patch ties that constant to upstream's LZ4HC_CLEVEL_OPT_MIN
with a static_assert, once <linux/lz4.h> is in scope of these files.

Levels 1 and 2 change in the other direction. Upstream routes them
through its new lz4mid strategy: at a 4K block that is 26% faster for
10% and 19% worse ratio, and at 64K it is 83% and 90% faster for 14% and
26% worse. In the fork level 1 was only 10% faster than level 3 while
compressing 17% worse, so this is a better point on the curve rather
than a loss, but it is a change. f2fs rejects levels below
LZ4HC_MIN_CLEVEL, so only zram can select them; a caller that wants the
old ratio should ask for level 3.

As with LZ4_stream_t, LZ4_streamHC_t becomes an incomplete type, and the
macros that laid the forked structure out (LZ4HC_DICTIONARY_LOGSIZE,
LZ4HC_MAXD, LZ4HC_MAXD_MASK, LZ4HC_HASH_LOG, LZ4HC_HASHTABLESIZE,
LZ4HC_HASH_MASK, LZ4_STREAMHCSIZE, LZ4_STREAMHCSIZE_SIZET) go with it.

LZ4HC_MEM_COMPRESS grows from 262192 to upstream's LZ4_STREAMHC_MINSIZE,
262200: upstream's LZ4HC_CCtx_internal has fields the forked one does
not, most visibly the dictionary context pointer. It has to grow in the
same commit; an allocation eight bytes short of what the compressor
initialises would overrun zram's compress path. The size is
static_asserted against upstream's own LZ4_STREAMHC_MINSIZE, so a future
re-sync that changes it fails the build rather than the allocation.

lz4hc.c pulls in lz4.c for its common definitions, which include two
decoder tables used there only by the fast decode loop. On architectures
where that loop is off, W=1 reports them as unused. Silence that one
warning for this one object rather than edit the vendored file.

This retires one local patch:

commit b08918fb3f27 ("lz4: do not export static symbol")

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 drivers/block/zram/backend_lz4hc.c |   2 +-
 include/linux/lz4.h                |  53 +--
 lib/lz4/Makefile                   |   4 +
 lib/lz4/lz4hc_compress.c           | 785 +++----------------------------------
 4 files changed, 76 insertions(+), 768 deletions(-)

diff --git a/drivers/block/zram/backend_lz4hc.c b/drivers/block/zram/backend_lz4hc.c
index d8aa01bb258fec760b597a88296dfaa4e0049693..894695753d99bf2fec7e191c4ec2fff489b5bddd 100644
--- a/drivers/block/zram/backend_lz4hc.c
+++ b/drivers/block/zram/backend_lz4hc.c
@@ -69,7 +69,7 @@ static int lz4hc_create(struct zcomp_params *params, struct zcomp_ctx *ctx)
 		if (!zctx->dstrm)
 			goto error;
 
-		zctx->cstrm = kzalloc_obj(*zctx->cstrm);
+		zctx->cstrm = kzalloc(LZ4HC_MEM_COMPRESS, GFP_KERNEL);
 		if (!zctx->cstrm)
 			goto error;
 	}
diff --git a/include/linux/lz4.h b/include/linux/lz4.h
index e96353a67d617a4d734cecaf3764814df692428b..0e617c096653ba122f466b019c68a30661e04989 100644
--- a/include/linux/lz4.h
+++ b/include/linux/lz4.h
@@ -59,19 +59,15 @@
 #define LZ4HC_DEFAULT_CLEVEL			9
 #define LZ4HC_MAX_CLEVEL			16
 
-#define LZ4HC_DICTIONARY_LOGSIZE 16
-#define LZ4HC_MAXD (1<<LZ4HC_DICTIONARY_LOGSIZE)
-#define LZ4HC_MAXD_MASK (LZ4HC_MAXD - 1)
-#define LZ4HC_HASH_LOG (LZ4HC_DICTIONARY_LOGSIZE - 1)
-#define LZ4HC_HASHTABLESIZE (1 << LZ4HC_HASH_LOG)
-#define LZ4HC_HASH_MASK (LZ4HC_HASHTABLESIZE - 1)
+/* Levels from here up select the optimal parser, whose ~64K workspace does
+ * not fit a kernel stack; lib/lz4 clamps them to LZ4HC_CLAMP_CLEVEL - 1.
+ * Anything up to LZ4HC_MAX_CLEVEL is still accepted, just no harder.
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
@@ -83,29 +79,10 @@
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
@@ -133,7 +110,7 @@ typedef union {
  * buffer is rejected, and the stateless entry points cannot report that.
  */
 #define LZ4_MEM_COMPRESS	16416
-#define LZ4HC_MEM_COMPRESS	LZ4_STREAMHCSIZE
+#define LZ4HC_MEM_COMPRESS	262200
 
 /*-************************************************************************
  *	Compression Functions
@@ -310,9 +287,9 @@ int LZ4_decompress_safe_partial(const char *source, char *dest,
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
@@ -328,9 +305,9 @@ int LZ4_compress_HC(const char *src, char *dst, int srcSize, int dstCapacity,
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
index e9d83cff4ea4efe1097f54caba72e268cecb04af..9ac36ada805cc99d6db43d141394e51b4b1f7598 100644
--- a/lib/lz4/Makefile
+++ b/lib/lz4/Makefile
@@ -9,3 +9,7 @@ ccflags-y += -I $(src)/freestanding
 obj-$(CONFIG_LZ4_COMPRESS)	+= lz4_compress.o
 obj-$(CONFIG_LZ4HC_COMPRESS)	+= lz4hc_compress.o
 obj-$(CONFIG_LZ4_DECOMPRESS)	+= lz4_decompress.o
+
+# lz4hc.c pulls in lz4.c's common definitions, which include two decoder
+# tables nothing here uses when LZ4_FAST_DEC_LOOP is off.
+CFLAGS_lz4hc_compress.o += $(call cc-disable-warning, unused-const-variable)
diff --git a/lib/lz4/lz4hc_compress.c b/lib/lz4/lz4hc_compress.c
index 91936dc3d14bca31752a361693380aad8eb3b98a..6070719bab54e90a8a163c088
```
