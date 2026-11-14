---
title: [PATCH 07/12] zloop: take freeze protection when recording write pointers
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-7-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-7-f5ae61c898b1@kernel.org/
---

# [PATCH 07/12] zloop: take freeze protection when recording write pointers

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-7-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-7-f5ae61c898b1@kernel.org/)

```
With discard_write_cache a flush records the write pointer of each
active zone in an xattr of its zone file. zloop_record_safe_wps() uses
vfs_setxattr() for that which leaves freeze protection to the caller.
So a flush rewrites the xattrs on a filesystem that is frozen. With the
zone files on ext4:

  WARNING: fs/ext4/ext4_jbd2.c:90 at ext4_journal_check_start+0x1f6/0x2d0, CPU#0: kworker/u16:2/46
  Workqueue: zloop0 zloop_cmd_workfn
  Call Trace:
   <TASK>
   __ext4_journal_start_sb+0x7a/0x470
   ext4_xattr_set+0x20d/0x380
   __vfs_setxattr+0x10f/0x170
   __vfs_setxattr_noperm+0xf4/0x5e0
   vfs_setxattr+0x14d/0x3d0
   zloop_cmd_workfn+0x384/0x1ff0
   process_one_work+0x946/0x1820
   worker_thread+0x4f1/0xd60
   kthread+0x364/0x460
   ret_from_fork+0x525/0x770
   ret_from_fork_asm+0x1a/0x30
   </TASK>

Take freeze protection around vfs_setxattr() with mnt_want_write_file()
like fsetxattr() does.

Fixes: 829def1e35ca ("zloop: forget write cache on force removal")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/block/zloop.c | 9 +++++++--
 1 file changed, 7 insertions(+), 2 deletions(-)

diff --git a/drivers/block/zloop.c b/drivers/block/zloop.c
index 34ed925e86f1a..a695aa8405d22 100644
--- a/drivers/block/zloop.c
+++ b/drivers/block/zloop.c
@@ -730,8 +730,13 @@ static int zloop_record_safe_wps(struct zloop_device *zlo)
 
 		if (!zloop_zone_is_active(zone))
 			continue;
-		ret = vfs_setxattr(file_mnt_idmap(file), file_dentry(file),
-				"user.zloop.wp", &zone->wp, sizeof(zone->wp), 0);
+		ret = mnt_want_write_file(file);
+		if (!ret) {
+			ret = vfs_setxattr(file_mnt_idmap(file),
+					file_dentry(file), "user.zloop.wp",
+					&zone->wp, sizeof(zone->wp), 0);
+			mnt_drop_write_file(file);
+		}
 		if (ret) {
 			pr_err("%pg: failed to record write pointer (%d)\n",
 				zlo->disk->part0, ret);

-- 
2.53.0
```
