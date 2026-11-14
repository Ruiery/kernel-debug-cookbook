---
title: [PATCH 08/12] target: fileio: take freeze protection for unmap
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-8-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-8-f5ae61c898b1@kernel.org/
---

# [PATCH 08/12] target: fileio: take freeze protection for unmap

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-8-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-8-f5ae61c898b1@kernel.org/)

```
UNMAP and WRITE SAME with UNMAP=1 end up in fd_execute_unmap() which
calls ->fallocate() of the backing file directly. That skips the freeze
protection vfs_fallocate() would have taken. So they go straight
through to a filesystem that is frozen, with and without fd_async_io.
With the backing file on ext4:

  WARNING: fs/ext4/ext4_jbd2.c:90 at ext4_journal_check_start+0x1f6/0x2d0, CPU#1: kworker/1:1/50
  Workqueue: target_submission target_queued_submit_work
  Call Trace:
   <TASK>
   __ext4_journal_start_sb+0x7a/0x470
   ext4_dirty_inode+0xa1/0x120
   __mark_inode_dirty+0x154/0x1110
   file_update_time_flags+0x3ab/0x4b0
   ext4_fallocate+0x286/0x3440
   fd_execute_unmap+0x1eb/0x6e0
   sbc_execute_write_same_unmap+0x93/0xe0
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

Take freeze protection around ->fallocate() like vfs_fallocate() does.

Fixes: 70d3ae5c8075 ("target/file: Add WRITE_SAME w/ UNMAP=1 emulation support")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/target/target_core_file.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/drivers/target/target_core_file.c b/drivers/target/target_core_file.c
index 27b266a092b18..3fe4035b22a94 100644
--- a/drivers/target/target_core_file.c
+++ b/drivers/target/target_core_file.c
@@ -596,7 +596,9 @@ fd_execute_unmap(struct se_cmd *cmd, sector_t lba, sector_t nolb)
 		if (!file->f_op->fallocate)
 			return TCM_LOGICAL_UNIT_COMMUNICATION_FAILURE;
 
+		file_start_write(file);
 		ret = file->f_op->fallocate(file, mode, pos, len);
+		file_end_write(file);
 		if (ret < 0) {
 			pr_warn("FILEIO: fallocate() failed: %d\n", ret);
 			return TCM_LOGICAL_UNIT_COMMUNICATION_FAILURE;

-- 
2.53.0
```
