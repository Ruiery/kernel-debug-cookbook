---
title: [PATCH 9/9] ublk: refuse to go live over canceled io commands
list: linux-block
message_id: 20260928-b4-ublk-cancel-stop-v1-9-4a4360232a46@toxicpanda.com
link: https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-9-4a4360232a46@toxicpanda.com/
---

# [PATCH 9/9] ublk: refuse to go live over canceled io commands

来源：[https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-9-4a4360232a46@toxicpanda.com/](https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-9-4a4360232a46@toxicpanda.com/)

```
START_DEV on a ready device whose commands got canceled adds a disk on
which every request fails. With UBLK_F_USER_RECOVERY, unless
UBLK_F_USER_RECOVERY_FAIL_IO is set, the requests are requeued instead
and never kicked again, so the partition scan read hangs with
disk->open_mutex held until the device is stopped again or deleted.
Every opener blocks behind it. END_USER_RECOVERY on a queue which kept
->canceling marks the device live and leaves its requests parked the
same way.

A command canceled by ublk_claim_cmd() cannot be fetched again before
the queues are reinitialized: FETCH fails with -EBUSY once the device
is ready and with -EINVAL on an active io. Since commit 1133b93fc7f6
("ublk: set canceling flag even when disk is not allocated") and the
previous patches such a device keeps ->canceling set, but nothing stops
it from going live.

In ublk_ctrl_start_dev() check for that and publish ub->ub_disk in one
cancel_mutex section, so that either START_DEV sees the canceled
commands or ublk_start_cancel() sees the disk and quiesces it.

Fix by failing START_DEV and END_USER_RECOVERY with -ENODEV when a
queue is canceling or holds a command canceled after being fetched.

Fixes: 1133b93fc7f6 ("ublk: set canceling flag even when disk is not allocated")
Assisted-by: LLM
Signed-off-by: Josef Bacik <josef@toxicpanda.com>
---
 Documentation/block/ublk.rst | 15 +++++++++--
 drivers/block/ublk_drv.c     | 63 ++++++++++++++++++++++++++++++++++++++------
 2 files changed, 68 insertions(+), 10 deletions(-)

diff --git a/Documentation/block/ublk.rst b/Documentation/block/ublk.rst
index 28300fee22bf..05d702f66a93 100644
--- a/Documentation/block/ublk.rst
+++ b/Documentation/block/ublk.rst
@@ -118,7 +118,13 @@ managing and controlling ublk devices with help of several control commands:
   After the server prepares userspace resources (such as creating I/O handler
   threads & io_uring for handling ublk IO), this command is sent to the
   driver for allocating & exposing ``/dev/ublkb*``. Parameters set via
-  ``UBLK_CMD_SET_PARAMS`` are applied for creating the device.
+  ``UBLK_CMD_SET_PARAMS`` are applied for creating the device. The command
+  fails with ``-ENODEV`` if any fetched io command got canceled meantime,
+  by ``UBLK_CMD_STOP_DEV`` or because its io_uring is gone, and the device
+  has to be deleted then. With ``UBLK_F_BATCH_IO`` it fails the same way
+  after a ``UBLK_CMD_STOP_DEV`` sent while no process had ``/dev/ublkc*``
+  open, or after the current one opened it, even if no io command had
+  been fetched yet.
 
 - ``UBLK_CMD_STOP_DEV``
 
@@ -195,7 +201,12 @@ managing and controlling ublk devices with help of several control commands:
   command is accepted after ublk device is quiesced and a new process has
   opened ``/dev/ublkc*`` and get all ublk queues be ready. When this command
   returns, ublk device is unquiesced and new I/O requests are passed to the
-  new process.
+  new process. It fails with ``-ENODEV`` if any of the new io commands got
+  canceled already, and with ``UBLK_F_BATCH_IO`` also if the cancel of a
+  ``UBLK_CMD_QUIESCE_DEV`` reached one of its queues after the old process
+  released ``/dev/ublkc*`` and before that queue got ready. The device has
+  to be deleted then, or the recovery
+  started over after the new process has closed ``/dev/ublkc*``.
 
 - user recovery feature description
 
diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 5e86405b294b..19efa13c205a 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -2757,6 +2757,7 @@ static void ublk_abort_queue(struct ublk_device *ub, struct ublk_queue *ubq)
 static struct gendisk *ublk_start_cancel(struct ublk_device *ub)
 	__must_hold(&ub->cancel_mutex)
 {
+	/* sync with ublk_ctrl_start_dev() publishing the disk */
 	struct gendisk *disk = ublk_get_disk(ub);
 
 	if (ub->canceling)
@@ -2772,10 +2773,10 @@ static struct gendisk *ublk_start_cancel(struct ublk_device *ub)
 		blk_mq_unquiesce_queue(disk->queue);
 	} else {
 		/*
-		 * Disk not yet allocated by ublk_ctrl_start_dev(), so
-		 * there is no request queue and ublk_queue_rq() cannot
-		 * be running.  Just set the flag; if start_dev proceeds
-		 * later, new I/O will see canceling and be aborted.
+		 * Disk not published by ublk_ctrl_start_dev() or detached
+		 * already, so ublk_queue_rq() cannot be running.  Just set
+		 * the flag, START_DEV fails on canceled commands instead
+		 * of adding a disk on top of them.
 		 */
 		ublk_set_canceling(ub, true);
 	}
@@ -4652,11 +4653,35 @@ static bool ublk_validate_user_pid(struct ublk_device *ub, pid_t ublksrv_pid)
 	return ub->ublksrv_tgid == ublksrv_pid;
 }
 
+/*
+ * The commands canceled by ublk_claim_cmd() can't be fetched again
+ * before the queues are reinitialized, so a ready device must not go live
+ * while a queue is canceling or holds a command canceled after the fetch.
+ */
+static bool ublk_dev_cmds_canceled(struct ublk_device *ub)
+	__must_hold(&ub->cancel_mutex)
+{
+	u16 i;
+
+	for (i = 0; i < ub->dev_info.nr_hw_queues; i++) {
+		struct ublk_queue *ubq = ublk_get_queue(ub, i);
+		bool canceled;
+
+		spin_lock(&ubq->cancel_lock);
+		canceled = ubq->canceling || ublk_queue_has_canceled_io(ubq);
+		spin_unlock(&ubq->cancel_lock);
+		if (canceled)
+			return true;
+	}
+	return false;
+}
+
 /*
  * Wait until all queues have fetched their I/O commands, and return with
- * ub->mutex held and readiness guaranteed: then every queue's ->canceling
- * is cleared. Ready may regress between wakeup and mutex_lock() (F_BATCH
- * UNPREP, daemon death), so re-check it under the mutex and wait again.
+ * ub->mutex held and readiness guaranteed. Ready may regress between wakeup
+ * and mutex_lock() (F_BATCH UNPREP, daemon death), so re-check it under the
+ * mutex and wait again. The commands may still get canceled after being
+ * fetched, callers check ublk_dev_cmds_canceled().
  */
 static int ublk_wait_dev_ready_and_lock(struct ublk_device *ub)
 {
@@ -4691,6 +4716,7 @@ static int ublk_ctrl_start_dev(struct ublk_device *ub,
 	};
 	struct gendisk *disk;
 	int ret = -EINVAL;
+	bool canceled;
 
 	if (ublksrv_pid <= 0)
 		return -EINVAL;
@@ -4776,8 +4802,20 @@ static int ublk_ctrl_start_dev(struct ublk_device *ub,
 	disk->fops = &ub_fops;
 	disk->private_data = ub;
 
+	/*
+	 * Check and publish under cancel_mutex, so either the canceled
+	 * commands are seen here or ublk_start_cancel() sees the disk.
+	 */
+	mutex_lock(&ub->cancel_mutex);
+	canceled = ublk_dev_cmds_canceled(ub);
+	if (!canceled)
+		ub->ub_disk = disk;
+	mutex_unlock(&ub->cancel_mutex);
+	if (canceled) {
+		ret = -ENODEV;
+		goto out_put_disk;
+	}
 	ub->dev_info.ublksrv_pid = ub->ublksrv_tgid;
-	ub->ub_disk = disk;
 
 	ublk_apply_params(ub);
 
@@ -4824,6 +4862,7 @@ static int ublk_ctrl_start_dev(struct ublk_device *ub,
 		ublk_detach_disk(ub);
 		ublk_put_device(ub);
 	}
+out_put_disk:
 	if (ret)
 		put_disk(disk);
 out_unlock:
@@ -5350,6 +5389,7 @@ static int ublk_ctrl_end_recovery(struct ublk_device *ub,
 {
 	int ublksrv_pid = (int)header->data[0];
 	int ret = -EINVAL;
+	bool canceled;
 
 	pr_devel("%s: Waiting for all FETCH_REQs, dev id %d...\n", __func__,
 		 header->dev_id);
@@ -5372,6 +5412,13 @@ static int ublk_ctrl_end_recovery(struct ublk_device *ub,
 		ret = -EBUSY;
 		goto out_unlock;
 	}
+	mutex_lock(&ub->cancel_mutex);
+	canceled = ublk_dev_cmds_canceled(ub);
+	mutex_unlock(&ub->cancel_mutex);
+	if (canceled) {
+		ret = -ENODEV;
+		goto out_unlock;
+	}
 	ub->dev_info.ublksrv_pid = ub->ublksrv_tgid;
 	ub->dev_info.state = UBLK_S_DEV_LIVE;
 	pr_devel("%s: new ublksrv_pid %d, dev id %d\n",

-- 
2.55.0
```
