---
title: [PATCH v2 2/2] block: rename the out_unfreeze label in elevator_switch()
list: linux-block
message_id: 20261015-bug-block-elevator-init-quiesce-v2-2-505a2b0b1c07@gmail.com
link: https://lore.kernel.org/linux-block/20261015-bug-block-elevator-init-quiesce-v2-2-505a2b0b1c07@gmail.com/
---

# [PATCH v2 2/2] block: rename the out_unfreeze label in elevator_switch()

来源：[https://lore.kernel.org/linux-block/20261015-bug-block-elevator-init-quiesce-v2-2-505a2b0b1c07@gmail.com/](https://lore.kernel.org/linux-block/20261015-bug-block-elevator-init-quiesce-v2-2-505a2b0b1c07@gmail.com/)

```
Commit f8e111c859b9 ("block: don't call freeze queue in
elevator_switch() and elevator_disable()") moved freezing the queue
out of elevator_switch() into its callers, but kept the out_unfreeze
label, which used to unquiesce and unfreeze the queue.

The code at the label now unquiesces the queue but never unfreezes it,
so the name is misleading.

Rename the label to out_unquiesce.

Suggested-by: Nilay Shroff <nilay@linux.ibm.com>
Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
 block/elevator.c | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/block/elevator.c b/block/elevator.c
index da9ba70ac9321..80cbac91581b0 100644
--- a/block/elevator.c
+++ b/block/elevator.c
@@ -584,7 +584,7 @@ static int elevator_switch(struct request_queue *q, struct elv_change_ctx *ctx)
 	if (new_e) {
 		ret = blk_mq_init_sched(q, new_e, &ctx->res);
 		if (ret)
-			goto out_unfreeze;
+			goto out_unquiesce;
 		ctx->new = q->elevator;
 	} else {
 		blk_queue_flag_clear(QUEUE_FLAG_SQ_SCHED, q);
@@ -594,7 +594,7 @@ static int elevator_switch(struct request_queue *q, struct elv_change_ctx *ctx)
 	}
 	blk_add_trace_msg(q, "elv switch: %s", ctx->name);
 
-out_unfreeze:
+out_unquiesce:
 	if (!ctx->no_quiesce)
 		blk_mq_unquiesce_queue(q);
 

-- 
2.43.0
```
