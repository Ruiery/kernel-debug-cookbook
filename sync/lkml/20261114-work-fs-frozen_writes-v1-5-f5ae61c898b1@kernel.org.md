---
title: [PATCH 05/12] target: fileio: take freeze protection for aio writes
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-5-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-5-f5ae61c898b1@kernel.org/
---

# [PATCH 05/12] target: fileio: take freeze protection for aio writes

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-5-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-5-f5ae61c898b1@kernel.org/)

```
With fd_async_io=1 the fileio backend calls ->write_iter() of the
backing file without taking freeze protection. So a write to the LUN
goes through to a filesystem that is frozen. With the backing file on
ext4:

  WARNING: fs/ext4/ext4_jbd2.c:90 at ext4_journal_check_start+0x1f6/0x2d0, CPU#0: kworker/0:2/40
  Workqueue: target_submission target_queued_submit_work
  Call Trace:
   <TASK>
   __ext4_journal_start_sb+0x7a/0x470
   ext4_dirty_inode+0xa1/0x120
   __mark_inode_dirty+0x154/0x1110
   file_update_time_flags+0x3ab/0x4b0
   ext4_file_write_iter+0xf11/0x1570
   fd_execute_rw+0xb01/0x1700
   __target_execute_cmd+0x53/0x190
   tcm_loop_write_pending+0xe/0x20
   transport_generic_new_cmd+0x612/0xdb0
   __target_submit+0x12c/0x380
   target_queued_submit_work+0x73/0x270
   process_one_work+0x946/0x1820
   worker_thread+0x4f1/0xd60
   kthread+0x364/0x460
   ret_from_fork+0x525/0x770
   ret_from_fork_asm+0x1a/0x30
   </TASK>

The synchronous path doesn't have that problem. vfs_iter_write() takes
freeze protection.

Take freeze protection around the write. A write that wasn't queued
drops it right away. A write that was queued drops it in the completion
callback.

Note that the completion callback can't tell from the command whether
it completes a write. COMPARE AND WRITE is a write but reads the data to
compare first. So remember the direction of the I/O in the aio command.

Fixes: 769031c92c8b ("scsi: target: target/file: Add support of direct and async I/O")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/target/target_core_file.c | 31 +++++++++++++++++++++++--------
 1 file changed, 23 insertions(+), 8 deletions(-)

diff --git a/drivers/target/target_core_file.c b/drivers/target/target_core_file.c
index 4dace29b6d662..27b266a092b18 100644
--- a/drivers/target/target_core_file.c
+++ b/drivers/target/target_core_file.c
@@ -246,6 +246,7 @@ struct target_core_file_cmd {
 	unsigned long	len;
 	struct se_cmd	*cmd;
 	refcount_t	ref;
+	bool		is_write;
 	struct kiocb	iocb;
 	struct bio_vec	bvecs[];
 };
@@ -256,12 +257,8 @@ static void cmd_rw_aio_put(struct target_core_file_cmd *cmd)
 		kfree(cmd);
 }
 
-static void cmd_rw_aio_complete(struct kiocb *iocb, long ret)
+static void cmd_rw_aio_done(struct target_core_file_cmd *cmd, long ret)
 {
-	struct target_core_file_cmd *cmd;
-
-	cmd = container_of(iocb, struct target_core_file_cmd, iocb);
-
 	if (ret != cmd->len)
 		target_complete_cmd(cmd->cmd, SAM_STAT_CHECK_CONDITION);
 	else
@@ -270,6 +267,19 @@ static void cmd_rw_aio_complete(struct kiocb *iocb, long ret)
 	cmd_rw_aio_put(cmd);
 }
 
+static void cmd_rw_aio_complete(struct kiocb *iocb, long ret)
+{
+	struct target_core_file_cmd *cmd;
+
+	cmd = container_of(iocb, struct target_core_file_cmd, iocb);
+
+	/* A queued write still holds freeze protection. */
+	if (cmd->is_write)
+		kiocb_end_write(iocb);
+
+	cmd_rw_aio_done(cmd, ret);
+}
+
 static sense_reason_t
 fd_execute_rw_aio(struct se_cmd *cmd, struct scatterlist *sgl, u32 sgl_nents,
 	      enum dma_data_direction data_direction)
@@ -300,6 +310,7 @@ fd_execute_rw_aio(struct se_cmd *cmd, struct scatterlist *sgl, u32 sgl_nents,
 	refcount_set(&aio_cmd->ref, 2);
 	aio_cmd->cmd = cmd;
 	aio_cmd->len = len;
+	aio_cmd->is_write = is_write;
 	aio_cmd->iocb.ki_pos = cmd->t_task_lba * dev->dev_attrib.block_size;
 	aio_cmd->iocb.ki_filp = file;
 	aio_cmd->iocb.ki_complete = cmd_rw_aio_complete;
@@ -308,13 +319,17 @@ fd_execute_rw_aio(struct se_cmd *cmd, struct scatterlist *sgl, u32 sgl_nents,
 	if (is_write && (cmd->se_cmd_flags & SCF_FUA))
 		aio_cmd->iocb.ki_flags |= IOCB_DSYNC;
 
-	if (is_write)
+	if (is_write) {
+		kiocb_start_write(&aio_cmd->iocb);
 		ret = file->f_op->write_iter(&aio_cmd->iocb, &iter);
-	else
+		if (ret != -EIOCBQUEUED)
+			kiocb_end_write(&aio_cmd->iocb);
+	} else {
 		ret = file->f_op->read_iter(&aio_cmd->iocb, &iter);
+	}
 
 	if (ret != -EIOCBQUEUED)
-		cmd_rw_aio_complete(&aio_cmd->iocb, ret);
+		cmd_rw_aio_done(aio_cmd, ret);
 	cmd_rw_aio_put(aio_cmd);
 
 	return 0;

-- 
2.53.0
```
