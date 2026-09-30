---
title: [PATCH 8/9] ublk: claim commands under ub->mutex in ublk_stop_dev()
list: linux-block
message_id: 20260928-b4-ublk-cancel-stop-v1-8-4a4360232a46@toxicpanda.com
link: https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-8-4a4360232a46@toxicpanda.com/
---

# [PATCH 8/9] ublk: claim commands under ub->mutex in ublk_stop_dev()

来源：[https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-8-4a4360232a46@toxicpanda.com/](https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-8-4a4360232a46@toxicpanda.com/)

```
STOP_DEV followed by START_DEV on a device which is ready but was never
started oopses on the first read, which reaches ublk_queue_cmd() with a
NULL io->cmd. ublk_stop_dev() completes the fetched commands through
ublk_cancel_dev() after dropping ub->mutex, which is only safe once
del_gendisk() has returned:

    STOP_DEV on a ready device without a disk
      ublk_stop_dev_unlocked() returns early, state is UBLK_S_DEV_DEAD
      ublk_cancel_dev() completes the commands
      ->canceling is never set, the device still counts as ready
    START_DEV
      passes every check, adds the disk, schedules the partition scan

START_DEV can also take ub->mutex right after ublk_stop_dev() drops it.
The idle commands of a live disk are canceled then with nothing
serializing that against ublk_queue_rq(). Commit 1133b93fc7f6 ("ublk:
set canceling flag even when disk is not allocated") closed the same
window for the io_uring cancel callbacks and left the STOP_DEV side
open.

START_DEV has to take ub->mutex before it can add a disk, so once the
commands are claimed under that mutex a queue getting ready afterwards
finds them canceled and stays canceling. Cancel the partition scan work
before dropping ub->mutex too, so that a START_DEV right after the
unlock does not get its new scan canceled.

ublk_cancel_dev() runs without ub->mutex, after this pass and after
QUIESCE_DEV, and a queue which is no longer canceling then belongs to a
round which started after the marking. So far it completed the new
commands of such a queue too, for a QUIESCE_DEV sent to a quiesced
device while the queue was already taking requests. Decide once under
cancel_mutex whether the queue is still canceling, take its commands in
that section, the fetch commands of a UBLK_F_BATCH_IO queue as well, and
complete them after it, as with the per-io commands. The fetch commands
stay linked on the list they are moved to, so take each one off it under
evts_lock before completing it, as ublk_batch_cancel_cmd() does, since
the cancel callback of their ring may take one first.

Fix by marking the queues as canceling and claiming their fetched
commands while ub->mutex is still held, and completing them once it is
dropped.

Fixes: 85248d670b71 ("ublk: move ublk_cancel_dev() out of ub->mutex")
Assisted-by: LLM
Signed-off-by: Josef Bacik <josef@toxicpanda.com>
---
 drivers/block/ublk_drv.c | 145 ++++++++++++++++++++++++++++++++++++++---------
 1 file changed, 119 insertions(+), 26 deletions(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 18046e2bf753..5e86405b294b 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -129,6 +129,8 @@ struct ublk_uring_cmd_pdu {
 	union {
 		struct request *req;
 		struct request *req_list;
+		/* links commands claimed by ublk_claim_queue_cmds() */
+		struct io_uring_cmd *next_claimed;
 	};
 
 	/*
@@ -2417,7 +2419,7 @@ static void ublk_reset_ch_dev(struct ublk_device *ub)
 	for (i = 0; i < ub->dev_info.nr_hw_queues; i++) {
 		struct ublk_queue *ubq = ublk_get_queue(ub, i);
 
-		/* Sync with ublk_cancel_cmd() */
+		/* Sync with ublk_claim_cmd() */
 		spin_lock(&ubq->cancel_lock);
 		ublk_queue_reinit(ub, ubq);
 		spin_unlock(&ubq->cancel_lock);
@@ -2840,15 +2842,6 @@ static struct io_uring_cmd *ublk_claim_cmd(struct ublk_queue *ubq, u16 tag)
 	return cmd;
 }
 
-static void ublk_cancel_cmd(struct ublk_queue *ubq, u16 tag,
-			    unsigned int issue_flags)
-{
-	struct io_uring_cmd *cmd = ublk_claim_cmd(ubq, tag);
-
-	if (cmd)
-		io_uring_cmd_done(cmd, UBLK_IO_RES_ABORT, issue_flags);
-}
-
 /*
  * Cancel a batch fetch command if it hasn't been claimed by another path.
  *
@@ -2877,23 +2870,45 @@ static void ublk_batch_cancel_cmd(struct ublk_queue *ubq,
 	}
 }
 
-static void ublk_batch_cancel_queue(struct ublk_queue *ubq)
+/*
+ * Move the parked fetch commands of a batch queue to @fcmd_list, for
+ * ublk_batch_complete_fcmds(); the active one is left to its dispatcher.
+ * They stay linked, and the cancel callback of their ring may still take
+ * one off @fcmd_list first: whoever unlinks a command under evts_lock
+ * completes it.
+ */
+static void ublk_batch_claim_fcmds(struct ublk_queue *ubq,
+				   struct list_head *fcmd_list)
 {
 	struct ublk_batch_fetch_cmd *fcmd;
-	LIST_HEAD(fcmd_list);
 
 	spin_lock(&ubq->evts_lock);
 	ubq->force_abort = true;
-	list_splice_init(&ubq->fcmd_head, &fcmd_list);
+	list_splice_init(&ubq->fcmd_head, fcmd_list);
 	fcmd = READ_ONCE(ubq->active_fcmd);
 	if (fcmd)
 		list_move(&fcmd->node, &ubq->fcmd_head);
 	spin_unlock(&ubq->evts_lock);
+}
 
-	while (!list_empty(&fcmd_list)) {
-		fcmd = list_first_entry(&fcmd_list,
-				struct ublk_batch_fetch_cmd, node);
-		ublk_batch_cancel_cmd(ubq, fcmd, IO_URING_F_UNLOCKED);
+static void ublk_batch_complete_fcmds(struct ublk_queue *ubq,
+				      struct list_head *fcmd_list)
+{
+	struct ublk_batch_fetch_cmd *fcmd;
+
+	for (;;) {
+		spin_lock(&ubq->evts_lock);
+		fcmd = list_first_entry_or_null(fcmd_list,
+						struct ublk_batch_fetch_cmd, node);
+		if (fcmd)
+			list_del_init(&fcmd->node);
+		spin_unlock(&ubq->evts_lock);
+		if (!fcmd)
+			break;
+
+		io_uring_cmd_done(fcmd->cmd, UBLK_IO_RES_ABORT,
+				  IO_URING_F_UNLOCKED);
+		ublk_batch_free_fcmd(fcmd);
 	}
 }
 
@@ -2960,7 +2975,8 @@ static void ublk_uring_cmd_cancel_fn(struct io_uring_cmd *cmd,
 	 */
 	mutex_lock(&ub->cancel_mutex);
 	disk = ublk_start_cancel(ub);
-	WARN_ON_ONCE(io->cmd != cmd);
+	/* ublk_stop_dev() may have claimed the command already */
+	WARN_ON_ONCE(io->cmd && io->cmd != cmd);
 	claimed = ublk_claim_cmd(ubq, pdu->tag);
 	mutex_unlock(&ub->cancel_mutex);
 	ublk_put_disk(disk);
@@ -2979,20 +2995,75 @@ static inline bool ublk_dev_ready(const struct ublk_device *ub)
 	return ub->nr_queue_ready == ub->dev_info.nr_hw_queues;
 }
 
-static void ublk_cancel_queue(struct ublk_queue *ubq)
+/*
+ * Claim the fetched commands of a queue and link them for completion
+ * outside of cancel_mutex.  A batch queue keeps its commands on the fetch
+ * command list, mark it the way ublk_batch_claim_fcmds() does instead.
+ */
+static struct io_uring_cmd *ublk_claim_queue_cmds(struct ublk_queue *ubq,
+						  struct io_uring_cmd *claimed)
+	__must_hold(&ubq->dev->cancel_mutex)
 {
-	u16 i;
+	u16 tag;
 
 	if (ublk_support_batch_io(ubq)) {
-		ublk_batch_cancel_queue(ubq);
-		return;
+		spin_lock(&ubq->evts_lock);
+		ubq->force_abort = true;
+		spin_unlock(&ubq->evts_lock);
+		return claimed;
 	}
 
-	for (i = 0; i < ubq->q_depth; i++)
-		ublk_cancel_cmd(ubq, i, IO_URING_F_UNLOCKED);
+	for (tag = 0; tag < ubq->q_depth; tag++) {
+		struct io_uring_cmd *cmd = ublk_claim_cmd(ubq, tag);
+
+		if (cmd) {
+			ublk_get_uring_cmd_pdu(cmd)->next_claimed = claimed;
+			claimed = cmd;
+		}
+	}
+	return claimed;
 }
 
-/* Cancel all pending commands, must be called after del_gendisk() returns */
+static void ublk_complete_claimed_cmds(struct io_uring_cmd *cmd)
+{
+	while (cmd) {
+		struct io_uring_cmd *next =
+			ublk_get_uring_cmd_pdu(cmd)->next_claimed;
+
+		io_uring_cmd_done(cmd, UBLK_IO_RES_ABORT, IO_URING_F_UNLOCKED);
+		cmd = next;
+	}
+}
+
+static void ublk_cancel_queue(struct ublk_queue *ubq)
+{
+	struct ublk_device *ub = ubq->dev;
+	struct io_uring_cmd *claimed = NULL;
+	LIST_HEAD(fcmds);
+
+	/*
+	 * A queue which is not canceling any more was made ready by a new
+	 * server after the marking, leave it alone.  Decide that in the
+	 * cancel_mutex section which takes the commands, the fetch commands
+	 * of a batch queue too, and complete them after it.
+	 */
+	mutex_lock(&ub->cancel_mutex);
+	if (ubq->canceling) {
+		claimed = ublk_claim_queue_cmds(ubq, NULL);
+		if (ublk_support_batch_io(ubq))
+			ublk_batch_claim_fcmds(ubq, &fcmds);
+	}
+	mutex_unlock(&ub->cancel_mutex);
+	ublk_complete_claimed_cmds(claimed);
+	if (ublk_support_batch_io(ubq))
+		ublk_batch_complete_fcmds(ubq, &fcmds);
+}
+
+/*
+ * Complete the fetched commands of every queue which is still canceling,
+ * ublk_queue_rq() must not be able to dispatch to th
```
