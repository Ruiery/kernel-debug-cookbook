---
title: [PATCH v2 04/17] zloop: take freeze protection for writes
list: linux-block
message_id: 20261116-work-fs-frozen_writes-v2-4-ecc4a2aac40e@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-4-ecc4a2aac40e@kernel.org/
---

# [PATCH v2 04/17] zloop: take freeze protection for writes

来源：[https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-4-ecc4a2aac40e@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-4-ecc4a2aac40e@kernel.org/)

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

Submit writes with kiocb_write_iter() and drop freeze protection in the
completion callback with kiocb_end_write_iter(). zloop_rw() also calls
the completion callback for I/O that wasn't queued or that failed before
it was submitted. kiocb_end_write_iter() does nothing for these.

Fixes: eb0570c7df23 ("block: new zoned loop block device driver")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/block/zloop.c | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

diff --git a/drivers/block/zloop.c b/drivers/block/zloop.c
index 65634a39b0bfc..76d54c9b89c0b 100644
--- a/drivers/block/zloop.c
+++ b/drivers/block/zloop.c
@@ -514,6 +514,7 @@ static void zloop_rw_complete(struct kiocb *iocb, long ret)
 {
 	struct zloop_cmd *cmd = container_of(iocb, struct zloop_cmd, iocb);
 
+	kiocb_end_write_iter(iocb);
 	cmd->ret = ret;
 	zloop_put_cmd(cmd);
 }
@@ -567,7 +568,7 @@ static int zloop_do_rw(struct zloop_cmd *cmd)
 	cmd->iocb.ki_ioprio = IOPRIO_PRIO_VALUE(IOPRIO_CLASS_NONE, 0);
 
 	if (rw == ITER_SOURCE)
-		return zone->file->f_op->write_iter(&cmd->iocb, &iter);
+		return kiocb_write_iter(&cmd->iocb, &iter);
 	return zone->file->f_op->read_iter(&cmd->iocb, &iter);
 }
 

-- 
2.53.0
```
