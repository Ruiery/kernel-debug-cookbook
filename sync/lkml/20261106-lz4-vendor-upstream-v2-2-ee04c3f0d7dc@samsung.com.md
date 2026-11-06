---
title: [PATCH v2 02/15] lib/lz4: remove LZ4_decompress_fast() and its variants
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-2-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-2-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 02/15] lib/lz4: remove LZ4_decompress_fast() and its variants

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-2-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-2-ee04c3f0d7dc@samsung.com/)

```
LZ4_decompress_fast(), LZ4_decompress_fast_continue() and
LZ4_decompress_fast_usingDict() have no users left. Upstream has
deprecated all three since v1.9: they take only the decompressed size,
so a corrupt or malicious stream has nothing to stop the decoder from
reading past the end of its input.

Remove them, their exports and their declarations in <linux/lz4.h>,
along with the two helpers only they used. Doing it before lib/lz4 moves
to upstream LZ4 keeps them out of the glue that move adds.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 include/linux/lz4.h      | 81 ----------------------------------------------
 lib/lz4/lz4_decompress.c | 84 ------------------------------------------------
 2 files changed, 165 deletions(-)

diff --git a/include/linux/lz4.h b/include/linux/lz4.h
index ad6042a718b5428792b795db7a8d4ad44c24a985..0df69e2b1ad523c291e3a96ab5595df9239f7252 100644
--- a/include/linux/lz4.h
+++ b/include/linux/lz4.h
@@ -249,27 +249,6 @@ int LZ4_compress_destSize(const char *source, char *dest, int *sourceSizePtr,
  *	Decompression Functions
  **************************************************************************/
 
-/**
- * LZ4_decompress_fast() - Decompresses data from 'source' into 'dest'
- * @source: source address of the compressed data
- * @dest: output buffer address of the uncompressed data
- *	which must be already allocated with 'originalSize' bytes
- * @originalSize: is the original and therefore uncompressed size
- *
- * Decompresses data from 'source' into 'dest'.
- * This function fully respect memory boundaries for properly formed
- * compressed data.
- * It is a bit faster than LZ4_decompress_safe().
- * However, it does not provide any protection against intentionally
- * modified data stream (malicious input).
- * Use this function in trusted environment only
- * (data to decode comes from a trusted source).
- *
- * Return: number of bytes read from the source buffer
- *	or a negative result if decompression fails.
- */
-int LZ4_decompress_fast(const char *source, char *dest, int originalSize);
-
 /**
  * LZ4_decompress_safe() - Decompression protected against buffer overflow
  * @source: source address of the compressed data
@@ -561,44 +540,6 @@ int LZ4_decompress_safe_continue(LZ4_streamDecode_t *LZ4_streamDecode,
 	const char *source, char *dest, int compressedSize,
 	int maxDecompressedSize);
 
-/**
- * LZ4_decompress_fast_continue() - Decompress blocks in streaming mode
- * @LZ4_streamDecode: the 'LZ4_streamDecode_t' structure
- * @source: source address of the compressed data
- * @dest: output buffer address of the uncompressed data
- *	which must be already allocated with 'originalSize' bytes
- * @originalSize: is the original and therefore uncompressed size
- *
- * This decoding function allows decompression of multiple blocks
- * in "streaming" mode.
- * Previously decoded blocks *must* remain available at the memory position
- * where they were decoded (up to 64 KB)
- * In the case of a ring buffers, decoding buffer must be either :
- *    - Exactly same size as encoding buffer, with same update rule
- *      (block boundaries at same positions) In which case,
- *      the decoding & encoding ring buffer can have any size,
- *      including very small ones ( < 64 KB).
- *    - Larger than encoding buffer, by a minimum of maxBlockSize more bytes.
- *      maxBlockSize is implementation dependent.
- *      It's the maximum size you intend to compress into a single block.
- *      In which case, encoding and decoding buffers do not need
- *      to be synchronized, and encoding ring buffer can have any size,
- *      including small ones ( < 64 KB).
- *    - _At least_ 64 KB + 8 bytes + maxBlockSize.
- *      In which case, encoding and decoding buffers do not need to be
- *      synchronized, and encoding ring buffer can have any size,
- *      including larger than decoding buffer. W
- * Whenever these conditions are not possible, save the last 64KB of decoded
- * data into a safe buffer, and indicate where it is saved
- * using LZ4_setStreamDecode()
- *
- * Return: number of bytes decompressed into destination buffer
- *	(necessarily <= maxDecompressedSize)
- *	or a negative result in case of error
- */
-int LZ4_decompress_fast_continue(LZ4_streamDecode_t *LZ4_streamDecode,
-	const char *source, char *dest, int originalSize);
-
 /**
  * LZ4_decompress_safe_usingDict() - Same as LZ4_setStreamDecode()
  *	followed by LZ4_decompress_safe_continue()
@@ -623,28 +564,6 @@ int LZ4_decompress_safe_usingDict(const char *source, char *dest,
 	int compressedSize, int maxDecompressedSize, const char *dictStart,
 	int dictSize);
 
-/**
- * LZ4_decompress_fast_usingDict() - Same as LZ4_setStreamDecode()
- *	followed by LZ4_decompress_fast_continue()
- * @source: source address of the compressed data
- * @dest: output buffer address of the uncompressed data
- *	which must be already allocated with 'originalSize' bytes
- * @originalSize: is the original and therefore uncompressed size
- * @dictStart: pointer to the start of the dictionary in memory
- * @dictSize: size of dictionary
- *
- * This decoding function works the same as
- * a combination of LZ4_setStreamDecode() followed by
- * LZ4_decompress_fast_continue()
- * It is stand-alone, and doesn't need an LZ4_streamDecode_t structure.
- *
- * Return: number of bytes decompressed into destination buffer
- *	(necessarily <= maxDecompressedSize)
- *	or a negative result in case of error
- */
-int LZ4_decompress_fast_usingDict(const char *source, char *dest,
-	int originalSize, const char *dictStart, int dictSize);
-
 #define LZ4_DECOMPRESS_INPLACE_MARGIN(compressedSize)          (((compressedSize) >> 8) + 32)
 
 #ifndef LZ4_DISTANCE_MAX	/* history window size; can be user-defined at compile time */
diff --git a/lib/lz4/lz4_decompress.c b/lib/lz4/lz4_decompress.c
index 3a2cd9acada4a09ef70a344090d48167c46088a1..f89b0e547f2156990c16770f69f89e0d8b46156d 100644
--- a/lib/lz4/lz4_decompress.c
+++ b/lib/lz4/lz4_decompress.c
@@ -474,14 +474,6 @@ int LZ4_decompress_safe_partial(const char *src, char *dst,
 				      noDict, (BYTE *)dst, NULL, 0);
 }
 
-int LZ4_decompress_fast(const char *source, char *dest, int originalSize)
-{
-	return LZ4_decompress_generic(source, dest, 0, originalSize,
-				      endOnOutputSize, decode_full_block,
-				      withPrefix64k,
-				      (BYTE *)dest - 64 * KB, NULL, 0);
-}
-
 /* ===== Instantiate a few more decoding cases, used more than once. ===== */
 
 static int LZ4_decompress_safe_withPrefix64k(const char *source, char *dest,
@@ -517,17 +509,6 @@ static int LZ4_decompress_safe_forceExtDict(const char *source, char *dest,
 				      (const BYTE *)dictStart, dictSize);
 }
 
-static int LZ4_decompress_fast_extDict(const char *source, char *dest,
-				       int originalSize,
-				       const void *dictStart, size_t dictSize)
-{
-	return LZ4_decompress_generic(source, dest,
-				      0, originalSize,
-				      endOnOutputSize, decode_full_block,
-				      usingExtDict, (BYTE *)dest,
-				      (const BYTE *)dictStart, dictSize);
-}
-
 /*
  * The "double dictionary" mode, for use with e.g. ring buffers: the first part
  * of the dictionary is passed as prefix, and the second via dictStart + dictSize.
@@ -546,18 +527,6 @@ int LZ4_decompress_safe_doubleDict(const char *source, char *dest,
 				      (const BYTE *)dictStart, dictSize);
 }
 
-static FORCE_INLINE
-int LZ4_decompress_fast_doubleDict(const char *source, char *dest,
-				   int originalSize, size_t prefixSize,
-				   const void *dictStart, size_t dictSize)
-{
-	return LZ4_decompress_generic(source, dest,
-				      0, originalSize,
-				      endOnOutputSize, decode_full_block,
-				      usingExtDict, (BYTE *)dest - prefixSize,
-				      (const BYTE *)dictStart, dictSize);
-}
-
 /* ===== streaming decompression functions ===== */
 
 int LZ4_setStreamDecode(LZ4_streamDecode_t *LZ4_streamDecode,
@@ -636,45 +605,6 @@ int LZ4_decompress_safe_continue(LZ4_stream
```
