---
title: [PATCH 02/12] zloop: take freeze protection for writes
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-2-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-2-f5ae61c898b1@kernel.org/
---

# [PATCH 02/12] zloop: take freeze protection for writes

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-2-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-2-f5ae61c898b1@kernel.org/)

```
zloop calls ->write_iter() of the zone files without taking freeze
protection. So a write to a zloop device goes through to a filesystem
that is frozen. With the zone files on ext4:

  WARNING: fs/ext4/ext4_jbd2.c:90 at ext4_journal_check_start+0x1f6/0x2d0, CPU#3: kworker/u16:4/507
  Workqueue: zloop0 zloop_cmd_workfn
  Call Trace:
   <TASK>
   __ext4_journal_start_sb+0x7a/0x470
   ext4_dirty_inode+0xa1/0x120
   __mark_inode_dirty+0x154/0x1110
   file_update_time_flags+0x3ab/0x4b0
   ext4_buffered_write_iter+0x143/0x630
   ext4_file_write_iter+0x7b9/0x1570
   zloop_do_rw+0x8ac/0xe10
   zloop_cmd_workfn+0xac5/0x1ff0
   process_one_work+0x946/0x1820
   worker_thread+0x4f1/0xd60
   kthread+0x364/0x460
   ret_from_fork+0x525/0x770
   ret_from_fork_asm+0x1a/0x30
   </TASK>

Take freeze protection around the write like loop does. A write that
wasn't queued drops it right away. A write that was queued drops it in
the completion callback.

Note that zloop_rw() also called the completion callback for I/O that
wasn't queued or that failed before it was submitted. It completes
these itself now so the callback only ever sees queued I/O.

Fixes: eb0570c7df23 ("block: new zoned loop block device driver")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/block/zloop.c | 22 +++++++++++++++++-----
 1 file changed, 17 insertions(+), 5 deletions(-)

diff --git a/drivers/block/zloop.c b/drivers/block/zloop.c
index 65634a39b0bfc..34ed925e86f1a 100644
--- a/drivers/block/zloop.c
+++ b/drivers/block/zloop.c
@@ -514,6 +514,10 @@ static void zloop_rw_complete(struct kiocb *iocb, long ret)
 {
 	struct zloop_cmd *cmd = container_of(iocb, struct zloop_cmd, iocb);
 
+	/* A queued write still holds freeze protection. */
+	if (req_op(blk_mq_rq_from_pdu(cmd)) != REQ_OP_READ)
+		kiocb_end_write(iocb);
+
 	cmd->ret = ret;
 	zloop_put_cmd(cmd);
 }
@@ -527,6 +531,7 @@ static int zloop_do_rw(struct zloop_cmd *cmd)
 	struct zloop_zone *zone = &zlo->zones[rq_zone_no(rq)];
 	struct req_iterator rq_iter;
 	struct iov_iter iter;
+	int ret;
 
 	if (rq->bio != rq->biotail) {
 		struct bio_vec tmp, *bvec;
@@ -566,9 +571,14 @@ static int zloop_do_rw(struct zloop_cmd *cmd)
 		cmd->iocb.ki_flags = IOCB_DIRECT;
 	cmd->iocb.ki_ioprio = IOPRIO_PRIO_VALUE(IOPRIO_CLASS_NONE, 0);
 
-	if (rw == ITER_SOURCE)
-		return zone->file->f_op->write_iter(&cmd->iocb, &iter);
-	return zone->file->f_op->read_iter(&cmd->iocb, &iter);
+	if (rw == ITER_DEST)
+		return zone->file->f_op->read_iter(&cmd->iocb, &iter);
+
+	kiocb_start_write(&cmd->iocb);
+	ret = zone->file->f_op->write_iter(&cmd->iocb, &iter);
+	if (ret != -EIOCBQUEUED)
+		kiocb_end_write(&cmd->iocb);
+	return ret;
 }
 
 static int zloop_seq_write_prep(struct zloop_cmd *cmd)
@@ -690,8 +700,10 @@ static void zloop_rw(struct zloop_cmd *cmd)
 		ret = zloop_do_rw(cmd);
 	}
 out:
-	if (ret != -EIOCBQUEUED)
-		zloop_rw_complete(&cmd->iocb, ret);
+	if (ret != -EIOCBQUEUED) {
+		cmd->ret = ret;
+		zloop_put_cmd(cmd);
+	}
 	zloop_put_cmd(cmd);
 }
 

-- 
2.53.0
```
