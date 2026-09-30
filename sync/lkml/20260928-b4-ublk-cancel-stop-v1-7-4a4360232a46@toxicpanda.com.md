---
title: [PATCH 7/9] ublk: mark queues and command in one cancel_mutex hold
list: linux-block
message_id: 20260928-b4-ublk-cancel-stop-v1-7-4a4360232a46@toxicpanda.com
link: https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-7-4a4360232a46@toxicpanda.com/
---

# [PATCH 7/9] ublk: mark queues and command in one cancel_mutex hold

来源：[https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-7-4a4360232a46@toxicpanda.com/](https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-7-4a4360232a46@toxicpanda.com/)

```
ublk_queue_rq() dispatches a request to a NULL io->cmd and the kernel
oopses when the last FETCH of a queue runs in the middle of
ublk_uring_cmd_cancel_fn(), which drops cancel_mutex between marking
the queues and marking the command:

    cancel callback                 last FETCH of the queue
    ublk_start_cancel()
      queues marked canceling
      cancel_mutex dropped
                                    ublk_mark_io_ready()
                                      queue is ready
                                      no canceled command found
                                      ->canceling = false
    ublk_cancel_cmd()
      UBLK_IO_FLAG_CANCELED set
      io->cmd = NULL, command done

ublk_queue_reset_io_flags() takes cancel_mutex for the ready
transition, so once the callback holds it across both steps the
transition comes either before or after them.

Move the locking of cancel_mutex from ublk_start_cancel() to its two
callers, and have ublk_uring_cmd_cancel_fn() claim the command with
ublk_claim_cmd() before it drops the mutex. The command is completed
after the unlock.

ublk_start_cancel() holds a reference on the disk, and dropping it used
to come after the unlock. Keep it that way by returning the reference to
the caller, the last put runs disk_release() and that should not happen
under cancel_mutex.

Fixes: 728cbac5fe21 ("ublk: move device reset into ublk_ch_release()")
Assisted-by: LLM
Signed-off-by: Josef Bacik <josef@toxicpanda.com>
---
 drivers/block/ublk_drv.c | 39 +++++++++++++++++++++++++++++++--------
 1 file changed, 31 insertions(+), 8 deletions(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 99ac56d36dd0..18046e2bf753 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -2748,11 +2748,15 @@ static void ublk_abort_queue(struct ublk_device *ub, struct ublk_queue *ubq)
 		ublk_abort_batch_queue(ub, ubq);
 }
 
-static void ublk_start_cancel(struct ublk_device *ub)
+/*
+ * Returns the disk reference it took.  The caller drops it after
+ * cancel_mutex, the last put ends up in disk_release().
+ */
+static struct gendisk *ublk_start_cancel(struct ublk_device *ub)
+	__must_hold(&ub->cancel_mutex)
 {
 	struct gendisk *disk = ublk_get_disk(ub);
 
-	mutex_lock(&ub->cancel_mutex);
 	if (ub->canceling)
 		goto out;
 
@@ -2774,8 +2778,7 @@ static void ublk_start_cancel(struct ublk_device *ub)
 		ublk_set_canceling(ub, true);
 	}
 out:
-	mutex_unlock(&ub->cancel_mutex);
-	ublk_put_disk(disk);
+	return disk;
 }
 
 /*
@@ -2900,8 +2903,13 @@ static void ublk_batch_cancel_fn(struct io_uring_cmd *cmd,
 	struct ublk_uring_cmd_pdu *pdu = ublk_get_uring_cmd_pdu(cmd);
 	struct ublk_batch_fetch_cmd *fcmd = pdu->fcmd;
 	struct ublk_queue *ubq = pdu->ubq;
+	struct ublk_device *ub = ubq->dev;
+	struct gendisk *disk;
 
-	ublk_start_cancel(ubq->dev);
+	mutex_lock(&ub->cancel_mutex);
+	disk = ublk_start_cancel(ub);
+	mutex_unlock(&ub->cancel_mutex);
+	ublk_put_disk(disk);
 
 	ublk_batch_cancel_cmd(ubq, fcmd, issue_flags);
 }
@@ -2926,7 +2934,10 @@ static void ublk_uring_cmd_cancel_fn(struct io_uring_cmd *cmd,
 {
 	struct ublk_uring_cmd_pdu *pdu = ublk_get_uring_cmd_pdu(cmd);
 	struct ublk_queue *ubq = pdu->ubq;
+	struct io_uring_cmd *claimed;
 	struct task_struct *task;
+	struct ublk_device *ub;
+	struct gendisk *disk;
 	struct ublk_io *io;
 
 	if (WARN_ON_ONCE(!ubq))
@@ -2935,15 +2946,27 @@ static void ublk_uring_cmd_cancel_fn(struct io_uring_cmd *cmd,
 	if (WARN_ON_ONCE(pdu->tag >= ubq->q_depth))
 		return;
 
+	ub = ubq->dev;
 	task = io_uring_cmd_get_task(cmd);
 	io = &ubq->ios[pdu->tag];
 	if (WARN_ON_ONCE(task && task != io->task))
 		return;
 
-	ublk_start_cancel(ubq->dev);
-
+	/*
+	 * Mark the queues and the command in one cancel_mutex section, so
+	 * that a queue getting ready meantime either finds the command
+	 * canceled or clears ->canceling first and gets marked again here.
+	 * Complete it outside, ublk_claim_cmd()'s other callers have to.
+	 */
+	mutex_lock(&ub->cancel_mutex);
+	disk = ublk_start_cancel(ub);
 	WARN_ON_ONCE(io->cmd != cmd);
-	ublk_cancel_cmd(ubq, pdu->tag, issue_flags);
+	claimed = ublk_claim_cmd(ubq, pdu->tag);
+	mutex_unlock(&ub->cancel_mutex);
+	ublk_put_disk(disk);
+
+	if (claimed)
+		io_uring_cmd_done(claimed, UBLK_IO_RES_ABORT, issue_flags);
 }
 
 static inline bool ublk_queue_ready(const struct ublk_queue *ubq)

-- 
2.55.0
```
