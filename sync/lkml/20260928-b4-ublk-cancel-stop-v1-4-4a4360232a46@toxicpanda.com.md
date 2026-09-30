---
title: [PATCH 4/9] ublk: read the io under io->lock in ublk_cancel_cmd()
list: linux-block
message_id: 20260928-b4-ublk-cancel-stop-v1-4-4a4360232a46@toxicpanda.com
link: https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-4-4a4360232a46@toxicpanda.com/
---

# [PATCH 4/9] ublk: read the io under io->lock in ublk_cancel_cmd()

来源：[https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-4-4a4360232a46@toxicpanda.com/](https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-4-4a4360232a46@toxicpanda.com/)

```
ublk_cancel_cmd() looks at three things before it takes a command: the
io is active, the request of its tag is not started, and the io was not
canceled before. Only the last one is read under a lock.

Since the previous patch ublk_fill_io_cmd() sets io->cmd and
UBLK_IO_FLAG_ACTIVE under io->lock. Take io->lock in ublk_cancel_cmd()
around all three checks and the read of io->cmd, so that a cancel from
the control path either finds the io not active or finds the command
which was stored with the flag.

The request check belongs in the same section. COMMIT_AND_FETCH ends
the request it commits after it has stored the new command. A cancel
which finds that request idle holds io->lock at that point, so it runs
after ublk_fill_io_cmd() dropped it and reads the new command, not the
request pointer which was in the union before.

Requests cannot be dispatched to the io meanwhile, every caller has the
queue marked as canceling or the disk deleted, so the dispatch side does
not need the lock.

ubq->cancel_lock nests inside of io->lock, as it does for
ublk_batch_prep_io() already.

Assisted-by: LLM
Signed-off-by: Josef Bacik <josef@toxicpanda.com>
---
 drivers/block/ublk_drv.c | 19 +++++++++++++------
 1 file changed, 13 insertions(+), 6 deletions(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 17a33539f271..1455ce27d3d1 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -2777,10 +2777,16 @@ static void ublk_cancel_cmd(struct ublk_queue *ubq, u16 tag,
 	struct ublk_device *ub = ubq->dev;
 	struct io_uring_cmd *cmd = NULL;
 	struct request *req;
-	bool done;
 
+	/*
+	 * ublk_fill_io_cmd() runs under io->lock, so either the io is not
+	 * active yet or its command is in io->cmd.  The request the command
+	 * was committed for is ended after that, check it in here as well, so
+	 * that one seen idle goes with the command fetched for the next one.
+	 */
+	ublk_io_lock(io);
 	if (!(io->flags & UBLK_IO_FLAG_ACTIVE))
-		return;
+		goto unlock;
 
 	/*
 	 * Don't try to cancel this command if the request is started for
@@ -2794,18 +2800,19 @@ static void ublk_cancel_cmd(struct ublk_queue *ubq, u16 tag,
 	 */
 	req = blk_mq_tag_to_rq(ub->tag_set.tags[ubq->q_id], tag);
 	if (req && blk_mq_request_started(req) && req->tag == tag)
-		return;
+		goto unlock;
 
 	spin_lock(&ubq->cancel_lock);
-	done = !!(io->flags & UBLK_IO_FLAG_CANCELED);
-	if (!done) {
+	if (!(io->flags & UBLK_IO_FLAG_CANCELED)) {
 		io->flags |= UBLK_IO_FLAG_CANCELED;
 		cmd = io->cmd;
 		io->cmd = NULL;
 	}
 	spin_unlock(&ubq->cancel_lock);
+unlock:
+	ublk_io_unlock(io);
 
-	if (!done && cmd)
+	if (cmd)
 		io_uring_cmd_done(cmd, UBLK_IO_RES_ABORT, issue_flags);
 }
 

-- 
2.55.0
```
