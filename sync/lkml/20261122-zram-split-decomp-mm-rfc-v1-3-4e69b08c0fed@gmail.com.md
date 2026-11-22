---
title: [PATCH RFC 3/3] zram: use split-input decompression for LZ4 and LZ4HC
list: linux-block
message_id: 20261122-zram-split-decomp-mm-rfc-v1-3-4e69b08c0fed@gmail.com
link: https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-3-4e69b08c0fed@gmail.com/
---

# [PATCH RFC 3/3] zram: use split-input decompression for LZ4 and LZ4HC

来源：[https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-3-4e69b08c0fed@gmail.com/](https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-3-4e69b08c0fed@gmail.com/)

```
Use the split decoder for dictionary-free LZ4 and LZ4HC blocks.
Keep dictionary-backed reads on the linear path and require the
split decoder to produce a full page.

Signed-off-by: Xueyuan Chen <xueyuan.chen21@gmail.com>
---
 drivers/block/zram/backend_lz4.c   |  1 +
 drivers/block/zram/backend_lz4.h   | 19 +++++++++++++++++++
 drivers/block/zram/backend_lz4hc.c |  2 ++
 3 files changed, 22 insertions(+)

diff --git a/drivers/block/zram/backend_lz4.c b/drivers/block/zram/backend_lz4.c
index 1e4ad31d39a6..2cf8ff656f13 100644
--- a/drivers/block/zram/backend_lz4.c
+++ b/drivers/block/zram/backend_lz4.c
@@ -150,6 +150,7 @@ static int lz4_decompress(struct zcomp_params *params, struct zcomp_ctx *ctx,
 const struct zcomp_ops backend_lz4 = {
 	.compress	= lz4_compress,
 	.decompress	= lz4_decompress,
+	.decompress_split = lz4_decompress_split,
 	.create_ctx	= lz4_create,
 	.destroy_ctx	= lz4_destroy,
 	.setup_params	= lz4_setup_params,
diff --git a/drivers/block/zram/backend_lz4.h b/drivers/block/zram/backend_lz4.h
index c11fa602a703..6c1736ea1a87 100644
--- a/drivers/block/zram/backend_lz4.h
+++ b/drivers/block/zram/backend_lz4.h
@@ -3,8 +3,27 @@
 #ifndef __BACKEND_LZ4_H__
 #define __BACKEND_LZ4_H__
 
+#include <linux/errno.h>
+#include <linux/lz4.h>
+
 #include "zcomp.h"
 
+static inline int lz4_decompress_split(struct zcomp_params *params,
+				       struct zcomp_ctx *ctx,
+				       const struct zcomp_req *head,
+				       const void *tail, size_t tail_len)
+{
+	int decoded;
+
+	if (params->dict_sz)
+		return -EOPNOTSUPP;
+	decoded = LZ4_decompress_safe_split(head->src, head->src_len, tail,
+					    tail_len, head->dst, head->dst_len);
+	if (decoded < 0)
+		return decoded;
+	return decoded == head->dst_len ? 0 : -EINVAL;
+}
+
 extern const struct zcomp_ops backend_lz4;
 
 #endif /* __BACKEND_LZ4_H__ */
diff --git a/drivers/block/zram/backend_lz4hc.c b/drivers/block/zram/backend_lz4hc.c
index d8aa01bb258f..56a6eecf8d67 100644
--- a/drivers/block/zram/backend_lz4hc.c
+++ b/drivers/block/zram/backend_lz4hc.c
@@ -7,6 +7,7 @@
 #include <linux/slab.h>
 #include <linux/vmalloc.h>
 
+#include "backend_lz4.h"
 #include "backend_lz4hc.h"
 
 struct lz4hc_ctx {
@@ -134,6 +135,7 @@ static int lz4hc_decompress(struct zcomp_params *params, struct zcomp_ctx *ctx,
 const struct zcomp_ops backend_lz4hc = {
 	.compress	= lz4hc_compress,
 	.decompress	= lz4hc_decompress,
+	.decompress_split = lz4_decompress_split,
 	.create_ctx	= lz4hc_create,
 	.destroy_ctx	= lz4hc_destroy,
 	.setup_params	= lz4hc_setup_params,

-- 
2.47.3
```
