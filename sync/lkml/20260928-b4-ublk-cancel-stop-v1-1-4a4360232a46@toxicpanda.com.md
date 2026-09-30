---
title: [PATCH 1/9] ublk: keep queue canceling over canceled commands
list: linux-block
message_id: 20260928-b4-ublk-cancel-stop-v1-1-4a4360232a46@toxicpanda.com
link: https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-1-4a4360232a46@toxicpanda.com/
---

# [PATCH 1/9] ublk: keep queue canceling over canceled commands

来源：[https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-1-4a4360232a46@toxicpanda.com/](https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-1-4a4360232a46@toxicpanda.com/)

```
ublk_queue_rq() dispatches a request to a NULL io->cmd and the kernel
oopses when a queue got ready over commands which were canceled after
being fetched. ublk_mark_io_ready() clears the queue's ->canceling once
q_depth commands got fetched, and that count does not go down when a
fetched command is canceled:

    task A                          task B
    FETCH part of the queue
    exits, its commands get
    canceled
    ublk_uring_cmd_cancel_fn()
      queues marked canceling
      io->cmd = NULL, command done
                                    FETCH the rest of the queue
                                    ublk_mark_io_ready()
                                      queue is ready
                                      ->canceling = false

During recovery the disk is attached at that point. Before the first
start START_DEV adds it afterwards.

The UBLK_IO_FLAG_CANCELED left from an earlier round is dropped after
the command is published, and ublk_cancel_dev() does not hold
ub->mutex, so a cancel coming in between loses its flag again.

A UBLK_F_BATCH_IO queue has no per-io flag for this, but STOP_DEV and
QUIESCE_DEV set its ->force_abort when they cancel its fetch commands,
so key on that for such a queue. ->force_abort is only cleared once the
queue is ready again, by ublk_queue_reset_io_flags() after this check
has read it, so one left set by the quiesce of a server which is gone
would keep the queue of the next server canceling. Clear it in
ublk_ch_release_work_fn() once the old server is gone, under ub->mutex
since ublk_stop_dev_unlocked() sets the flag under that mutex and needs
it set until del_gendisk() returns. From then on until the queue is
ready again, requests for a UBLK_F_USER_RECOVERY device are requeued
through ->canceling instead of failed through ->force_abort, as they
are on a queue without UBLK_F_BATCH_IO.

Fix by keeping ->canceling at the ready transition while a command of
the queue carries UBLK_IO_FLAG_CANCELED, or while ->force_abort is set
on a UBLK_F_BATCH_IO queue, and by dropping the stale flag and
publishing a fetched command in one cancel_lock section.

Fixes: 728cbac5fe21 ("ublk: move device reset into ublk_ch_release()")
Assisted-by: LLM
Signed-off-by: Josef Bacik <josef@toxicpanda.com>
---
 drivers/block/ublk_drv.c | 59 +++++++++++++++++++++++++++++++++++++++---------
 1 file changed, 48 insertions(+), 11 deletions(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 66eb55e7162e..183de080e008 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -2603,6 +2603,16 @@ static void ublk_ch_release_work_fn(struct work_struct *work)
 		}
 	}
 unlock:
+	/*
+	 * A ->force_abort left set here was set against the server which is
+	 * gone, clear it so that ublk_queue_reset_io_flags() does not count
+	 * it against the next one, whose requests ->canceling holds back
+	 * until its queues are ready.  Do it under ub->mutex, under which
+	 * ublk_stop_dev_unlocked() sets the flag and relies on it until
+	 * del_gendisk() returns.
+	 */
+	for (i = 0; i < ub->dev_info.nr_hw_queues; i++)
+		WRITE_ONCE(ublk_get_queue(ub, i)->force_abort, false);
 	mutex_unlock(&ub->mutex);
 	ublk_put_disk(disk);
 
@@ -3015,27 +3025,44 @@ static void ublk_stop_dev(struct ublk_device *ub)
 	ublk_cancel_dev(ub);
 }
 
-static void ublk_reset_io_flags(struct ublk_queue *ubq, struct ublk_io *io)
+static bool ublk_queue_has_canceled_io(const struct ublk_queue *ubq)
+	__must_hold(&ubq->cancel_lock)
 {
-	/* UBLK_IO_FLAG_CANCELED can be cleared now */
-	spin_lock(&ubq->cancel_lock);
-	io->flags &= ~UBLK_IO_FLAG_CANCELED;
-	spin_unlock(&ubq->cancel_lock);
+	u16 i;
+
+	/*
+	 * The ios of a UBLK_F_BATCH_IO queue are not canceled one by one,
+	 * canceling the queue sets ->force_abort instead.
+	 * ublk_ch_release_work_fn() clears the flag when a server goes away,
+	 * so one seen here was not left behind by an earlier server.
+	 */
+	if (ublk_support_batch_io(ubq))
+		return READ_ONCE(ubq->force_abort);
+
+	for (i = 0; i < ubq->q_depth; i++) {
+		if (ubq->ios[i].flags & UBLK_IO_FLAG_CANCELED)
+			return true;
+	}
+	return false;
 }
 
 /* reset per-queue io flags */
 static void ublk_queue_reset_io_flags(struct ublk_queue *ubq)
 {
 	spin_lock(&ubq->cancel_lock);
-	ubq->canceling = false;
+	/*
+	 * A command canceled after being fetched is still counted as ready
+	 * but can't take requests, so the queue has to stay canceling.
+	 */
+	if (!ublk_queue_has_canceled_io(ubq))
+		ubq->canceling = false;
 	spin_unlock(&ubq->cancel_lock);
 	ubq->fail_io = false;
 	ubq->force_abort = false;
 }
 
 /* device can only be started after all IOs are ready */
-static void ublk_mark_io_ready(struct ublk_device *ub, u16 q_id,
-	struct ublk_io *io)
+static void ublk_mark_io_ready(struct ublk_device *ub, u16 q_id)
 	__must_hold(&ub->mutex)
 {
 	struct ublk_queue *ubq = ublk_get_queue(ub, q_id);
@@ -3044,7 +3071,6 @@ static void ublk_mark_io_ready(struct ublk_device *ub, u16 q_id,
 		ub->unprivileged_daemons = true;
 
 	ubq->nr_io_ready++;
-	ublk_reset_io_flags(ubq, io);
 
 	/* Check if this specific queue is now fully ready */
 	if (ublk_queue_ready(ubq)) {
@@ -3269,6 +3295,8 @@ static int ublk_check_fetch_buf(const struct ublk_device *ub, __u64 buf_addr)
 static int __ublk_fetch(struct io_uring_cmd *cmd, struct ublk_device *ub,
 			struct ublk_io *io, u16 q_id)
 {
+	struct ublk_queue *ubq = ublk_get_queue(ub, q_id);
+
 	/* UBLK_IO_FETCH_REQ is only allowed before dev is setup */
 	if (ublk_dev_ready(ub))
 		return -EBUSY;
@@ -3279,7 +3307,16 @@ static int __ublk_fetch(struct io_uring_cmd *cmd, struct ublk_device *ub,
 
 	WARN_ON_ONCE(io->flags & UBLK_IO_FLAG_OWNED_BY_SRV);
 
+	/*
+	 * ublk_cancel_dev() runs without ub->mutex, publish the command under
+	 * cancel_lock so that a cancel either misses the io or finds it whole,
+	 * and drop a stale UBLK_IO_FLAG_CANCELED in the same section first so
+	 * that one set from now on stays.
+	 */
+	spin_lock(&ubq->cancel_lock);
+	io->flags &= ~UBLK_IO_FLAG_CANCELED;
 	ublk_fill_io_cmd(io, cmd);
+	spin_unlock(&ubq->cancel_lock);
 
 	if (ublk_dev_support_batch_io(ub))
 		WRITE_ONCE(io->task, NULL);
@@ -3306,7 +3343,7 @@ static int ublk_fetch(struct io_uring_cmd *cmd, struct ublk_device *ub,
 		ret = __ublk_fetch(cmd, ub, io, q_id);
 	if (!ret) {
 		ublk_apply_io_buf(ub, io, cmd, buf_addr, &auto_buf, NULL);
-		ublk_mark_io_ready(ub, q_id, io);
+		ublk_mark_io_ready(ub, q_id);
 	}
 	mutex_unlock(&ub->mutex);
 	return ret;
@@ -3723,7 +3760,7 @@ static int ublk_batch_prep_io(struct ublk_queue *ubq,
 	ublk_io_unlock(io);
 
 	if (!ret)
-		ublk_mark_io_ready(data->ub, ubq->q_id, io);
+		ublk_mark_io_ready(data->ub, ubq->q_id);
 
 	return ret;
 }

-- 
2.55.0
```
