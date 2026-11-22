---
title: [PATCH RFC 2/3] lib/lz4: add safe decompression from two input buffers
list: linux-block
message_id: 20261122-zram-split-decomp-mm-rfc-v1-2-4e69b08c0fed@gmail.com
link: https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-2-4e69b08c0fed@gmail.com/
---

# [PATCH RFC 2/3] lib/lz4: add safe decompression from two input buffers

来源：[https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-2-4e69b08c0fed@gmail.com/](https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-2-4e69b08c0fed@gmail.com/)

```
LZ4_decompress_generic() assumes contiguous input. Its wide literal
loads can cross the boundary between independently mapped fragments.

Add a dictionary-free block decoder that reads from two buffers and
handles literals, lengths and offsets that cross the split.

Signed-off-by: Xueyuan Chen <xueyuan.chen21@gmail.com>
---
 include/linux/lz4.h      |  18 ++++++
 lib/lz4/lz4_decompress.c | 163 +++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 181 insertions(+)

diff --git a/include/linux/lz4.h b/include/linux/lz4.h
index ad6042a718b5..3b6217bd9a9b 100644
--- a/include/linux/lz4.h
+++ b/include/linux/lz4.h
@@ -292,6 +292,24 @@ int LZ4_decompress_fast(const char *source, char *dest, int originalSize);
 int LZ4_decompress_safe(const char *source, char *dest, int compressedSize,
 	int maxDecompressedSize);
 
+/**
+ * LZ4_decompress_safe_split() - Decode a single block from two buffers
+ * @first: address of the first input fragment
+ * @first_len: bytes in the first input fragment
+ * @second: address of the second input fragment
+ * @second_len: bytes in the second input fragment
+ * @dst: output buffer, disjoint from the input buffers
+ * @capacity: bytes available in the output buffer
+ *
+ * The fragments, in order, contain one dictionary-free LZ4 block.
+ * Their addresses need not be adjacent. An empty fragment may be NULL.
+ *
+ * Return: the decoded size, or -EINVAL on error.
+ */
+int LZ4_decompress_safe_split(const u8 *first, size_t first_len,
+			      const u8 *second, size_t second_len,
+			      u8 *dst, int capacity);
+
 /**
  * LZ4_decompress_safe_partial() - Decompress a block of size 'compressedSize'
  *	at position 'source' into buffer 'dest'
diff --git a/lib/lz4/lz4_decompress.c b/lib/lz4/lz4_decompress.c
index 3a2cd9acada4..548197faa3e3 100644
--- a/lib/lz4/lz4_decompress.c
+++ b/lib/lz4/lz4_decompress.c
@@ -39,6 +39,11 @@
 #include <linux/kernel.h>
 #include <linux/unaligned.h>
 
+#ifndef STATIC
+#include <linux/errno.h>
+#include <linux/limits.h>
+#endif
+
 /*-*****************************
  *	Decompression functions
  *******************************/
@@ -705,6 +710,164 @@ int LZ4_decompress_fast_usingDict(const char *source, char *dest,
 }
 
 #ifndef STATIC
+struct lz4_split_input {
+	const u8 *first;
+	const u8 *second;
+	size_t split;
+	size_t size;
+	size_t pos;
+};
+
+static __always_inline size_t
+lz4_split_input_left(const struct lz4_split_input *in)
+{
+	return in->size - in->pos;
+}
+
+static __always_inline int lz4_split_get_byte(struct lz4_split_input *in)
+{
+	size_t pos = in->pos;
+
+	if (unlikely(pos == in->size))
+		return -1;
+	in->pos++;
+	if (pos < in->split)
+		return in->first[pos];
+	return in->second[pos - in->split];
+}
+
+/* The caller has checked that two bytes remain in the block. */
+static __always_inline int lz4_split_get_offset(struct lz4_split_input *in)
+{
+	size_t pos = in->pos;
+
+	in->pos += 2;
+	if (pos >= in->split)
+		return get_unaligned_le16(in->second + (pos - in->split));
+	if (in->split - pos >= 2)
+		return get_unaligned_le16(in->first + pos);
+	return in->first[pos] | (in->second[0] << 8);
+}
+
+static __always_inline bool
+lz4_split_copy_literals(struct lz4_split_input *in, u8 *dst, size_t len)
+{
+	size_t pos = in->pos;
+
+	if (unlikely(len > lz4_split_input_left(in)))
+		return false;
+	if (!len)
+		return true;
+	if (pos < in->split) {
+		size_t n = min(len, in->split - pos);
+
+		memcpy(dst, in->first + pos, n);
+		pos += n;
+		dst += n;
+		len -= n;
+	}
+	if (len)
+		memcpy(dst, in->second + (pos - in->split), len);
+	in->pos = pos + len;
+	return true;
+}
+
+/* The decoder has checked the lookbehind distance and output capacity. */
+static __always_inline void
+lz4_split_copy_match(u8 *dst, size_t distance, size_t len)
+{
+	size_t copied = min(distance, len);
+
+	if (distance == 1) {
+		memset(dst, dst[-1], len);
+		return;
+	}
+
+	memcpy(dst, dst - distance, copied);
+	/* Reuse the period already written, keeping each copy disjoint. */
+	while (len - copied > copied) {
+		memcpy(dst + copied, dst, copied);
+		copied *= 2;
+	}
+	if (copied < len)
+		memcpy(dst + copied, dst, len - copied);
+}
+
+static __always_inline int
+lz4_split_read_length(struct lz4_split_input *in, int length, int limit)
+{
+	int byte;
+
+	if (length > limit)
+		return -EINVAL;
+	if (length < RUN_MASK)
+		return length;
+
+	do {
+		byte = lz4_split_get_byte(in);
+		if (byte < 0 || byte > limit - length)
+			return -EINVAL;
+		length += byte;
+	} while (byte == 255);
+	return length;
+}
+
+int LZ4_decompress_safe_split(const u8 *first, size_t first_len,
+			      const u8 *second, size_t second_len,
+			      u8 *dst, int capacity)
+{
+	struct lz4_split_input in = {
+		.first = first,
+		.second = second,
+		.split = first_len,
+	};
+	int written = 0, min_last_literals = 0;
+
+	if (capacity < 0 || !dst || (!first && first_len) ||
+	    (!second && second_len) || first_len > SIZE_MAX - second_len)
+		return -EINVAL;
+	in.size = first_len + second_len;
+
+	for (;;) {
+		int token, literal, distance, match;
+
+		token = lz4_split_get_byte(&in);
+		if (token < 0)
+			return -EINVAL;
+		literal = lz4_split_read_length(&in, token >> ML_BITS,
+						capacity - written);
+		if (literal < 0 ||
+		    !lz4_split_copy_literals(&in, dst + written, literal))
+			return -EINVAL;
+		written += literal;
+		if (!lz4_split_input_left(&in))
+			return literal >= min_last_literals ? written : -EINVAL;
+
+		/* A match must leave room for the final literal sequence. */
+		if (lz4_split_input_left(&in) < 2 + 1 + LASTLITERALS ||
+		    capacity - written < MFLIMIT)
+			return -EINVAL;
+
+		distance = lz4_split_get_offset(&in);
+		if (!distance || distance > written)
+			return -EINVAL;
+		match = lz4_split_read_length(&in, token & ML_MASK,
+					      capacity - written - MINMATCH -
+					      LASTLITERALS);
+		if (match < 0)
+			return -EINVAL;
+		match += MINMATCH;
+		lz4_split_copy_match(dst + written, distance, match);
+		written += match;
+		/*
+		 * Leave at least LASTLITERALS bytes and end at least MFLIMIT
+		 * bytes past the start of the last match.
+		 */
+		min_last_literals = max(LASTLITERALS, MFLIMIT - match);
+	}
+}
+EXPORT_SYMBOL_GPL(LZ4_decompress_safe_split);
+
 EXPORT_SYMBOL(LZ4_decompress_safe);
 EXPORT_SYMBOL(LZ4_decompress_safe_partial);
 EXPORT_SYMBOL(LZ4_decompress_fast);

-- 
2.47.3
```
