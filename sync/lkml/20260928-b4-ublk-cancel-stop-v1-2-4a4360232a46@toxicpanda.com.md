---
title: [PATCH 2/9] ublk: clear ub->canceling with the queue's own flag
list: linux-block
message_id: 20260928-b4-ublk-cancel-stop-v1-2-4a4360232a46@toxicpanda.com
link: https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-2-4a4360232a46@toxicpanda.com/
---

# [PATCH 2/9] ublk: clear ub->canceling with the queue's own flag

来源：[https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-2-4a4360232a46@toxicpanda.com/](https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-2-4a4360232a46@toxicpanda.com/)

```
ublk_queue_rq() dispatches a request to a NULL io->cmd and the kernel
oopses when, during recovery, the task serving a queue which is ready
already exits before the last queue is ready. ublk_start_cancel() skips
marking and quiescing the queues while ub->canceling is set, since that
means every queue is marked. Since commit 3f3850785594 ("ublk: fix
batch I/O recovery -ENODEV error") it does not mean that any more:

    queue 0 gets ready:  ubq->canceling = false
                         ub->canceling stays set until the last queue
                         is ready
    queue 0 task exits:  ublk_start_cancel() sees ub->canceling, returns
                         queue 0 commands done, ubq->canceling unset

The disk is attached during recovery, and on a queue which got ready
only ->canceling holds requests back, so the next request for queue 0
is dispatched.

Fix by clearing ub->canceling together with the queue flag, under
cancel_mutex, so that the next cancel marks and quiesces every queue
again, and by dropping the clearing on full readiness.

Fixes: 3f3850785594 ("ublk: fix batch I/O recovery -ENODEV error")
Assisted-by: LLM
Signed-off-by: Josef Bacik <josef@toxicpanda.com>
---
 drivers/block/ublk_drv.c | 21 ++++++++++-----------
 1 file changed, 10 insertions(+), 11 deletions(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 183de080e008..50c99b28ef21 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -3049,14 +3049,21 @@ static bool ublk_queue_has_canceled_io(const struct ublk_queue *ubq)
 /* reset per-queue io flags */
 static void ublk_queue_reset_io_flags(struct ublk_queue *ubq)
 {
+	struct ublk_device *ub = ubq->dev;
+
+	mutex_lock(&ub->cancel_mutex);
 	spin_lock(&ubq->cancel_lock);
 	/*
 	 * A command canceled after being fetched is still counted as ready
 	 * but can't take requests, so the queue has to stay canceling.
 	 */
-	if (!ublk_queue_has_canceled_io(ubq))
+	if (!ublk_queue_has_canceled_io(ubq)) {
 		ubq->canceling = false;
+		/* not every queue is marked now, let the next cancel redo it */
+		ub->canceling = false;
+	}
 	spin_unlock(&ubq->cancel_lock);
+	mutex_unlock(&ub->cancel_mutex);
 	ubq->fail_io = false;
 	ubq->force_abort = false;
 }
@@ -3084,17 +3091,9 @@ static void ublk_mark_io_ready(struct ublk_device *ub, u16 q_id)
 		ublk_queue_reset_io_flags(ubq);
 	}
 
-	/* Check if all queues are ready */
-	if (ublk_dev_ready(ub)) {
-		/*
-		 * All queues ready - clear device-level canceling flag
-		 * and wake ublk_dev_ready() waiters.
-		 */
-		mutex_lock(&ub->cancel_mutex);
-		ub->canceling = false;
-		mutex_unlock(&ub->cancel_mutex);
+	/* All queues ready - wake ublk_dev_ready() waiters */
+	if (ublk_dev_ready(ub))
 		wake_up_var(&ub->nr_queue_ready);
-	}
 }
 
 static inline int ublk_check_cmd_op(u32 cmd_op)

-- 
2.55.0
```
