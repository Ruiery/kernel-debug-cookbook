---
title: [PATCH 04/12] target: fileio: don't free the aio command under the filesystem
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-4-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-4-f5ae61c898b1@kernel.org/
---

# [PATCH 04/12] target: fileio: don't free the aio command under the filesystem

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-4-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-4-f5ae61c898b1@kernel.org/)

```
With fd_async_io=1 the fileio backend allocates a command that holds the
kiocb for every read and write and frees it in the completion callback.
Nothing keeps the command alive until ->read_iter() or ->write_iter()
return. But a filesystem may use the kiocb after it queued the I/O. ext4
does that for direct reads:

  BUG: KASAN: slab-use-after-free in ext4_dio_read_iter+0x5e1/0x690
  Workqueue: target_submission target_queued_submit_work
  Call Trace:
   <TASK>
   dump_stack_lvl+0x5d/0x80
   print_report+0x14b/0x4b0
   kasan_report+0x108/0x130
   ext4_dio_read_iter+0x5e1/0x690
   fd_execute_rw+0xd30/0x1700
   __target_execute_cmd+0x53/0x190
   transport_generic_new_cmd+0x65a/0xdb0
   __target_submit+0x12c/0x380
   target_queued_submit_work+0x73/0x270
   process_one_work+0x946/0x1820
   worker_thread+0x4f1/0xd60
   kthread+0x364/0x460
   ret_from_fork+0x525/0x770
   ret_from_fork_asm+0x1a/0x30
   </TASK>

  Allocated by task 59:
   __kmalloc_noprof+0x223/0x830
   fd_execute_rw+0x766/0x1700
   __target_execute_cmd+0x53/0x190
   transport_generic_new_cmd+0x65a/0xdb0
   __target_submit+0x12c/0x380
   target_queued_submit_work+0x73/0x270

  Freed by task 14:
   kfree+0x267/0x6a0
   blk_update_request+0x3f5/0x1260
   blk_mq_end_request+0x59/0x450
   blk_complete_reqs+0xb0/0x130
   handle_softirqs+0x20c/0x860
   run_ksoftirqd+0x31/0x60

The read completed and freed the command before ext4_dio_read_iter() got
to file_accessed(iocb->ki_filp).

Do what loop, zloop and fs/backing-file.c do and hold a reference to the
command until the I/O is submitted.

Fixes: 769031c92c8b ("scsi: target: target/file: Add support of direct and async I/O")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/target/target_core_file.c | 13 ++++++++++++-
 1 file changed, 12 insertions(+), 1 deletion(-)

diff --git a/drivers/target/target_core_file.c b/drivers/target/target_core_file.c
index ab9824a4852f1..4dace29b6d662 100644
--- a/drivers/target/target_core_file.c
+++ b/drivers/target/target_core_file.c
@@ -15,6 +15,7 @@
 #include <linux/timer.h>
 #include <linux/blkdev.h>
 #include <linux/slab.h>
+#include <linux/refcount.h>
 #include <linux/spinlock.h>
 #include <linux/module.h>
 #include <linux/vmalloc.h>
@@ -244,10 +245,17 @@ static void fd_destroy_device(struct se_device *dev)
 struct target_core_file_cmd {
 	unsigned long	len;
 	struct se_cmd	*cmd;
+	refcount_t	ref;
 	struct kiocb	iocb;
 	struct bio_vec	bvecs[];
 };
 
+static void cmd_rw_aio_put(struct target_core_file_cmd *cmd)
+{
+	if (refcount_dec_and_test(&cmd->ref))
+		kfree(cmd);
+}
+
 static void cmd_rw_aio_complete(struct kiocb *iocb, long ret)
 {
 	struct target_core_file_cmd *cmd;
@@ -259,7 +267,7 @@ static void cmd_rw_aio_complete(struct kiocb *iocb, long ret)
 	else
 		target_complete_cmd(cmd->cmd, SAM_STAT_GOOD);
 
-	kfree(cmd);
+	cmd_rw_aio_put(cmd);
 }
 
 static sense_reason_t
@@ -288,6 +296,8 @@ fd_execute_rw_aio(struct se_cmd *cmd, struct scatterlist *sgl, u32 sgl_nents,
 
 	iov_iter_bvec(&iter, is_write, aio_cmd->bvecs, sgl_nents, len);
 
+	/* The filesystem may still use the kiocb after it queued the I/O. */
+	refcount_set(&aio_cmd->ref, 2);
 	aio_cmd->cmd = cmd;
 	aio_cmd->len = len;
 	aio_cmd->iocb.ki_pos = cmd->t_task_lba * dev->dev_attrib.block_size;
@@ -305,6 +315,7 @@ fd_execute_rw_aio(struct se_cmd *cmd, struct scatterlist *sgl, u32 sgl_nents,
 
 	if (ret != -EIOCBQUEUED)
 		cmd_rw_aio_complete(&aio_cmd->iocb, ret);
+	cmd_rw_aio_put(aio_cmd);
 
 	return 0;
 }

-- 
2.53.0
```
