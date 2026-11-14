---
title: [PATCH 06/12] loop: take freeze protection for discard and write zeroes
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-6-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-6-f5ae61c898b1@kernel.org/
---

# [PATCH 06/12] loop: take freeze protection for discard and write zeroes

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-6-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-6-f5ae61c898b1@kernel.org/)

```
Discard and write zeroes requests end up in lo_fallocate() which calls
->fallocate() of the backing file directly. That skips the freeze
protection vfs_fallocate() would have taken. So they go straight
through to a filesystem that is frozen. With the backing file on ext4:

  WARNING: fs/ext4/ext4_jbd2.c:90 at ext4_journal_check_start+0x1f6/0x2d0, CPU#3: kworker/u16:1/44
  Workqueue: loop1 loop_rootcg_workfn
  Call Trace:
   <TASK>
   __ext4_journal_start_sb+0x7a/0x470
   ext4_dirty_inode+0xa1/0x120
   __mark_inode_dirty+0x154/0x1110
   file_update_time_flags+0x3ab/0x4b0
   ext4_fallocate+0x286/0x3440
   lo_fallocate+0x13e/0x290
   loop_process_work+0x486/0xe70
   process_one_work+0x946/0x1820
   worker_thread+0x4f1/0xd60
   kthread+0x364/0x460
   ret_from_fork+0x525/0x770
   ret_from_fork_asm+0x1a/0x30
   </TASK>

Take freeze protection around ->fallocate() like vfs_fallocate() does.

Fixes: dfaa2ef68e80 ("loop: add discard support for loop devices")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/block/loop.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/drivers/block/loop.c b/drivers/block/loop.c
index a3325ceab484a..77f0601475bb9 100644
--- a/drivers/block/loop.c
+++ b/drivers/block/loop.c
@@ -259,7 +259,9 @@ static int lo_fallocate(struct loop_device *lo, struct request *rq, loff_t pos,
 	if (!bdev_max_discard_sectors(lo->lo_device))
 		return -EOPNOTSUPP;
 
+	file_start_write(file);
 	ret = file->f_op->fallocate(file, mode, pos, blk_rq_bytes(rq));
+	file_end_write(file);
 	if (unlikely(ret && ret != -EINVAL && ret != -EOPNOTSUPP))
 		return -EIO;
 

-- 
2.53.0
```
