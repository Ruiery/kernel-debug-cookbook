---
title: [PATCH RFC 1/3] zram: allow backends to decompress from two input buffers
list: linux-block
message_id: 20261122-zram-split-decomp-mm-rfc-v1-1-4e69b08c0fed@gmail.com
link: https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-1-4e69b08c0fed@gmail.com/
---

# [PATCH RFC 1/3] zram: allow backends to decompress from two input buffers

来源：[https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-1-4e69b08c0fed@gmail.com/](https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-1-4e69b08c0fed@gmail.com/)

```
Let backends decompress a spanning zsmalloc object directly from its
two scatterlist entries. Keep both fragments mapped for the call.

Use the linear path if the callback is absent or returns -EOPNOTSUPP
before writing output. Propagate other errors.

Signed-off-by: Xueyuan Chen <xueyuan.chen21@gmail.com>
---
 drivers/block/zram/zcomp.c | 28 ++++++++++++++++++++++++++++
 drivers/block/zram/zcomp.h |  8 ++++++++
 2 files changed, 36 insertions(+)

diff --git a/drivers/block/zram/zcomp.c b/drivers/block/zram/zcomp.c
index 028e2f0f587e..265108b9f332 100644
--- a/drivers/block/zram/zcomp.c
+++ b/drivers/block/zram/zcomp.c
@@ -159,6 +159,28 @@ int zcomp_compress(struct zcomp *comp, struct zcomp_strm *zstrm,
 	return ret;
 }
 
+static int zcomp_decompress_split(struct zcomp *comp, struct zcomp_strm *zstrm,
+				  struct scatterlist *sg, void *dst)
+{
+	struct scatterlist *next = sg_next(sg);
+	/* Each entry from the zsmalloc read path fits within one page. */
+	void *first = kmap_local_page(sg_page(sg));
+	void *second = kmap_local_page(sg_page(next));
+	struct zcomp_req head = {
+		.src = first + sg->offset,
+		.src_len = sg->length,
+		.dst = dst,
+		.dst_len = PAGE_SIZE,
+	};
+	int ret;
+
+	ret = comp->ops->decompress_split(comp->params, &zstrm->ctx, &head,
+					 second + next->offset, next->length);
+	kunmap_local(second);
+	kunmap_local(first);
+	return ret;
+}
+
 int zcomp_decompress(struct zcomp *comp, struct zcomp_strm *zstrm,
 		     struct scatterlist *sg, unsigned int src_len, void *dst)
 {
@@ -177,6 +199,12 @@ int zcomp_decompress(struct zcomp *comp, struct zcomp_strm *zstrm,
 		src = kmap_local_page(sg_page(sg));
 		req.src = src + sg->offset;
 	} else {
+		if (comp->ops->decompress_split) {
+			ret = zcomp_decompress_split(comp, zstrm, sg, dst);
+			if (ret != -EOPNOTSUPP)
+				return ret;
+		}
+
 		/* the object spans two pages, linearize it into local copy */
 		sg_copy_to_buffer(sg, 2, zstrm->local_copy, src_len);
 		req.src = zstrm->local_copy;
diff --git a/drivers/block/zram/zcomp.h b/drivers/block/zram/zcomp.h
index f38fd31f9e4e..92a93630aead 100644
--- a/drivers/block/zram/zcomp.h
+++ b/drivers/block/zram/zcomp.h
@@ -61,6 +61,14 @@ struct zcomp_ops {
 			struct zcomp_req *req);
 	int (*decompress)(struct zcomp_params *params, struct zcomp_ctx *ctx,
 			  struct zcomp_req *req);
+	/*
+	 * Decode one block from head->src and tail into head->dst. The input
+	 * mappings are valid during the call. Return 0 for a complete output
+	 * or -EOPNOTSUPP before writing output to request a linear retry.
+	 */
+	int (*decompress_split)(struct zcomp_params *params, struct zcomp_ctx *ctx,
+				const struct zcomp_req *head,
+				const void *tail, size_t tail_len);
 
 	int (*create_ctx)(struct zcomp_params *params, struct zcomp_ctx *ctx);
 	void (*destroy_ctx)(struct zcomp_ctx *ctx);

-- 
2.47.3
```
