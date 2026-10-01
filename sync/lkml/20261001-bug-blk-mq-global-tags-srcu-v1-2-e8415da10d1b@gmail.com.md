---
title: [PATCH 2/2] blk-mq: drop the tag_set argument from blk_mq_free_rq_map/tags
list: linux-block
message_id: 20261001-bug-blk-mq-global-tags-srcu-v1-2-e8415da10d1b@gmail.com
link: https://lore.kernel.org/linux-block/20261001-bug-blk-mq-global-tags-srcu-v1-2-e8415da10d1b@gmail.com/
---

# [PATCH 2/2] blk-mq: drop the tag_set argument from blk_mq_free_rq_map/tags

来源：[https://lore.kernel.org/linux-block/20261001-bug-blk-mq-global-tags-srcu-v1-2-e8415da10d1b@gmail.com/](https://lore.kernel.org/linux-block/20261001-bug-blk-mq-global-tags-srcu-v1-2-e8415da10d1b@gmail.com/)

```
Commit 9ad8e5af3279 ("blk-mq: Pass tag_set to blk_mq_free_rq_map/tags")
added the argument so that both helpers could reach the tag set's
tags_srcu. Now that the SRCU instance is global, nothing uses it.
Remove it.

No functional change.

Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
 block/blk-mq-tag.c |  2 +-
 block/blk-mq.c     | 10 +++++-----
 block/blk-mq.h     |  4 ++--
 3 files changed, 8 insertions(+), 8 deletions(-)

diff --git a/block/blk-mq-tag.c b/block/blk-mq-tag.c
index 6e01309226716..2b751bfa50e11 100644
--- a/block/blk-mq-tag.c
+++ b/block/blk-mq-tag.c
@@ -614,7 +614,7 @@ static void blk_mq_free_tags_callback(struct rcu_head *head)
 	kfree(tags);
 }
 
-void blk_mq_free_tags(struct blk_mq_tag_set *set, struct blk_mq_tags *tags)
+void blk_mq_free_tags(struct blk_mq_tags *tags)
 {
 	sbitmap_queue_free(&tags->bitmap_tags);
 	sbitmap_queue_free(&tags->breserved_tags);
diff --git a/block/blk-mq.c b/block/blk-mq.c
index f4ba1ac92a228..0c3c1481712a9 100644
--- a/block/blk-mq.c
+++ b/block/blk-mq.c
@@ -3496,14 +3496,14 @@ void blk_mq_free_rqs(struct blk_mq_tag_set *set, struct blk_mq_tags *tags,
 	 */
 }
 
-void blk_mq_free_rq_map(struct blk_mq_tag_set *set, struct blk_mq_tags *tags)
+void blk_mq_free_rq_map(struct blk_mq_tags *tags)
 {
 	kfree(tags->rqs);
 	tags->rqs = NULL;
 	kfree(tags->static_rqs);
 	tags->static_rqs = NULL;
 
-	blk_mq_free_tags(set, tags);
+	blk_mq_free_tags(tags);
 }
 
 static enum hctx_type hctx_idx_to_type(struct blk_mq_tag_set *set,
@@ -3565,7 +3565,7 @@ static struct blk_mq_tags *blk_mq_alloc_rq_map(struct blk_mq_tag_set *set,
 err_free_rqs:
 	kfree(tags->rqs);
 err_free_tags:
-	blk_mq_free_tags(set, tags);
+	blk_mq_free_tags(tags);
 	return NULL;
 }
 
@@ -4118,7 +4118,7 @@ struct blk_mq_tags *blk_mq_alloc_map_and_rqs(struct blk_mq_tag_set *set,
 
 	ret = blk_mq_alloc_rqs(set, tags, hctx_idx, depth);
 	if (ret) {
-		blk_mq_free_rq_map(set, tags);
+		blk_mq_free_rq_map(tags);
 		return NULL;
 	}
 
@@ -4146,7 +4146,7 @@ void blk_mq_free_map_and_rqs(struct blk_mq_tag_set *set,
 {
 	if (tags) {
 		blk_mq_free_rqs(set, tags, hctx_idx);
-		blk_mq_free_rq_map(set, tags);
+		blk_mq_free_rq_map(tags);
 	}
 }
 
diff --git a/block/blk-mq.h b/block/blk-mq.h
index e6b463da50712..1e64236d34d42 100644
--- a/block/blk-mq.h
+++ b/block/blk-mq.h
@@ -62,7 +62,7 @@ void blk_mq_put_rq_ref(struct request *rq);
  */
 void blk_mq_free_rqs(struct blk_mq_tag_set *set, struct blk_mq_tags *tags,
 		     unsigned int hctx_idx);
-void blk_mq_free_rq_map(struct blk_mq_tag_set *set, struct blk_mq_tags *tags);
+void blk_mq_free_rq_map(struct blk_mq_tags *tags);
 struct blk_mq_tags *blk_mq_alloc_map_and_rqs(struct blk_mq_tag_set *set,
 				unsigned int hctx_idx, unsigned int depth);
 void blk_mq_free_map_and_rqs(struct blk_mq_tag_set *set,
@@ -176,7 +176,7 @@ struct blk_mq_alloc_data {
 
 struct blk_mq_tags *blk_mq_init_tags(unsigned int nr_tags,
 		unsigned int reserved_tags, unsigned int flags, int node);
-void blk_mq_free_tags(struct blk_mq_tag_set *set, struct blk_mq_tags *tags);
+void blk_mq_free_tags(struct blk_mq_tags *tags);
 
 extern struct srcu_struct blk_mq_tags_srcu;
 

-- 
2.43.0
```
