---
title: [PATCH v2 03/15] zram: lz4hc: reset the dictionary stream once, not per page
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-3-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-3-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 03/15] zram: lz4hc: reset the dictionary stream once, not per page

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-3-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-3-ee04c3f0d7dc@samsung.com/)

```
With a dictionary, lz4hc_compress() calls LZ4_resetStreamHC() and then
LZ4_loadDictHC() for every page. LZ4_loadDictHC() re-initialises the
stream itself and keeps the level, so one reset at creation is enough.

The reset is cheap today, but upstream LZ4, which lib/lz4 moves to later
in this series, clears the whole 256K state in both calls. Reset once in
lz4hc_create() instead.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 drivers/block/zram/backend_lz4hc.c | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/drivers/block/zram/backend_lz4hc.c b/drivers/block/zram/backend_lz4hc.c
index d8aa01bb258fec760b597a88296dfaa4e0049693..06286c805cf7c56bd760f460cc854dc4014f293b 100644
--- a/drivers/block/zram/backend_lz4hc.c
+++ b/drivers/block/zram/backend_lz4hc.c
@@ -72,6 +72,7 @@ static int lz4hc_create(struct zcomp_params *params, struct zcomp_ctx *ctx)
 		zctx->cstrm = kzalloc_obj(*zctx->cstrm);
 		if (!zctx->cstrm)
 			goto error;
+		LZ4_resetStreamHC(zctx->cstrm, params->level);
 	}
 
 	return 0;
@@ -92,8 +93,7 @@ static int lz4hc_compress(struct zcomp_params *params, struct zcomp_ctx *ctx,
 				      req->dst_len, params->level,
 				      zctx->mem);
 	} else {
-		/* Cstrm needs to be reset */
-		LZ4_resetStreamHC(zctx->cstrm, params->level);
+		/* Reloading the dict resets cstrm and keeps its level */
 		ret = LZ4_loadDictHC(zctx->cstrm, params->dict,
 				     params->dict_sz);
 		if (ret != params->dict_sz)

-- 
2.34.1
```
