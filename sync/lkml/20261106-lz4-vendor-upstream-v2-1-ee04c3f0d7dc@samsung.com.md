---
title: [PATCH v2 01/15] lib/decompress_unlz4: use LZ4_decompress_safe_partial() before boot
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-1-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-1-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 01/15] lib/decompress_unlz4: use LZ4_decompress_safe_partial() before boot

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-1-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-1-ee04c3f0d7dc@samsung.com/)

```
The pre-boot decompressor is the only in-tree user of
LZ4_decompress_fast(), which upstream has deprecated since v1.9. It
never checks the input against the chunk length in the header.

Decode with LZ4_decompress_safe_partial() instead, bounded by the chunk
length and by the expected output length. Count every chunk against the
size the image ends with, and fail a chunk that decodes short or comes
after that size is reached.

x86 decompresses in place; the margin arch/x86/boot/header.S reserves,
(output >> 8) + 128K, covers the safe decoder's 32-byte overshoot.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 lib/decompress_unlz4.c | 13 ++++++++-----
 1 file changed, 8 insertions(+), 5 deletions(-)

diff --git a/lib/decompress_unlz4.c b/lib/decompress_unlz4.c
index c0dbb3cea915eb91d8f4ac26c38c4785bbf19770..dc20c22e087900e21da49f9fcb267e6b511e1072 100644
--- a/lib/decompress_unlz4.c
+++ b/lib/decompress_unlz4.c
@@ -151,14 +151,17 @@ STATIC inline int INIT unlz4(u8 *input, long in_len,
 			}
 		}
 #ifdef PREBOOT
-		if (out_len >= uncomp_chunksize) {
+		if (out_len >= uncomp_chunksize)
 			dest_len = uncomp_chunksize;
-			out_len -= dest_len;
-		} else
+		else
 			dest_len = out_len;
+		out_len -= dest_len;
 
-		ret = LZ4_decompress_fast(inp, outp, dest_len);
-		chunksize = ret;
+		ret = LZ4_decompress_safe_partial(inp, outp, chunksize,
+						  dest_len, dest_len);
+		/* A chunk once the image's stated size is reached is corrupt. */
+		if (!dest_len || ret != (int)dest_len)
+			ret = -1;
 #else
 		dest_len = uncomp_chunksize;
 

-- 
2.34.1
```
