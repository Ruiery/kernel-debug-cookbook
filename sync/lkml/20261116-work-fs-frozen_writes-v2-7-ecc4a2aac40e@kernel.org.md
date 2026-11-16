---
title: [PATCH v2 07/17] target: fileio: take freeze protection for aio writes
list: linux-block
message_id: 20261116-work-fs-frozen_writes-v2-7-ecc4a2aac40e@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-7-ecc4a2aac40e@kernel.org/
---

# [PATCH v2 07/17] target: fileio: take freeze protection for aio writes

来源：[https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-7-ecc4a2aac40e@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-7-ecc4a2aac40e@kernel.org/)

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

Submit writes with kiocb_write_iter() and drop freeze protection in the
completion callback with kiocb_end_write_iter().

Note that the completion callback couldn't tell from the command whether
it completes a write anyway. COMPARE AND WRITE is a write but reads the
data to compare first. kiocb_write_iter() marks the kiocb with
IOCB_WRITE so the callback doesn't need to know.

Fixes: 769031c92c8b ("scsi: target: target/file: Add support of direct and async I/O")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/target/target_core_file.c | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

diff --git a/drivers/target/target_core_file.c b/drivers/target/target_core_file.c
index 4b23fadd7bb88..e8a44ddf6f5c9 100644
--- a/drivers/target/target_core_file.c
+++ b/drivers/target/target_core_file.c
@@ -268,6 +268,7 @@ static void cmd_rw_aio_complete(struct kiocb *iocb, long ret)
 	struct target_core_file_cmd *cmd;
 
 	cmd = container_of(iocb, struct target_core_file_cmd, iocb);
+	kiocb_end_write_iter(iocb);
 	cmd->ret = ret;
 	cmd_rw_aio_put(cmd);
 }
@@ -311,7 +312,7 @@ fd_execute_rw_aio(struct se_cmd *cmd, struct scatterlist *sgl, u32 sgl_nents,
 		aio_cmd->iocb.ki_flags |= IOCB_DSYNC;
 
 	if (is_write)
-		ret = file->f_op->write_iter(&aio_cmd->iocb, &iter);
+		ret = kiocb_write_iter(&aio_cmd->iocb, &iter);
 	else
 		ret = file->f_op->read_iter(&aio_cmd->iocb, &iter);
 

-- 
2.53.0
```
