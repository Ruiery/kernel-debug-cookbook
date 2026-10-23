---
title: [PATCH v4 1/2] loop: drop stale partitions on LOOP_CHANGE_FD
list: linux-block
message_id: 20261023-b4-loop-nbd-stale-partitions-v4-1-2baf05e4b2cb@amutable.com
link: https://lore.kernel.org/linux-block/20261023-b4-loop-nbd-stale-partitions-v4-1-2baf05e4b2cb@amutable.com/
---

# [PATCH v4 1/2] loop: drop stale partitions on LOOP_CHANGE_FD

来源：[https://lore.kernel.org/linux-block/20261023-b4-loop-nbd-stale-partitions-v4-1-2baf05e4b2cb@amutable.com/](https://lore.kernel.org/linux-block/20261023-b4-loop-nbd-stale-partitions-v4-1-2baf05e4b2cb@amutable.com/)

```
From: Daan De Meyer <daan@amutable.com>

Commit 267ec4d7223a ("loop: fix partition scan race between udev and
loop_reread_partitions()") stopped disk_force_media_change() from
setting GD_NEED_PART_SCAN. That bit did more than request a rescan:
bdev_disk_changed() drops every partition before it consults
disk_has_partscan(), so the lazy scan on the next open was also what
removed partitions from a loop device without LO_FLAGS_PARTSCAN.

Such devices are not unusual. bdev_add_partition() only rejects
GENHD_FL_NO_PART disks, so BLKPG_ADD_PARTITION works while
GD_SUPPRESS_PART_SCAN is set, and parted, libfdisk and systemd all fall
back to BLKPG when BLKRRPART fails with -EINVAL, which is what a loop
device without LO_FLAGS_PARTSCAN returns.

loop_change_fd() only rescans when LO_FLAGS_PARTSCAN is set, so those
partitions now survive the backing file swap and keep describing the old
file. The new backing file must have the same size, but its partition
table can be completely different, leaving the partition devices mapping
the wrong ranges.

Call loop_reread_partitions() unconditionally. Without LO_FLAGS_PARTSCAN,
blk_add_partitions() returns early, so this drops the stale partitions
without scanning the new backing file.

Fixes: 267ec4d7223a ("loop: fix partition scan race between udev and loop_reread_partitions()")
Cc: stable@vger.kernel.org
Reviewed-by: Christian Brauner (Amutable) <brauner@kernel.org>
Reviewed-by: Bart Van Assche <bvanassche@acm.org>
Tested-by: Shin'ichiro Kawasaki <shinichiro.kawasaki@wdc.com>
Signed-off-by: Daan De Meyer <daan@amutable.com>
---
 drivers/block/loop.c | 10 ++++++----
 1 file changed, 6 insertions(+), 4 deletions(-)

diff --git a/drivers/block/loop.c b/drivers/block/loop.c
index 758c20678bf6..378163fdf957 100644
--- a/drivers/block/loop.c
+++ b/drivers/block/loop.c
@@ -552,7 +552,6 @@ static int loop_change_fd(struct loop_device *lo, struct block_device *bdev,
 	struct file *old_file;
 	unsigned int memflags;
 	int error;
-	bool partscan;
 	bool is_loop;
 
 	if (!file)
@@ -606,7 +605,6 @@ static int loop_change_fd(struct loop_device *lo, struct block_device *bdev,
 	loop_assign_backing_file(lo, file);
 	loop_update_dio(lo);
 	blk_mq_unfreeze_queue(lo->lo_queue, memflags);
-	partscan = lo->lo_flags & LO_FLAGS_PARTSCAN;
 	loop_global_unlock(lo, is_loop);
 
 	/*
@@ -624,8 +622,12 @@ static int loop_change_fd(struct loop_device *lo, struct block_device *bdev,
 	 */
 	fput(old_file);
 	dev_set_uevent_suppress(disk_to_dev(lo->lo_disk), 0);
-	if (partscan)
-		loop_reread_partitions(lo);
+	/*
+	 * Rescan or, without LO_FLAGS_PARTSCAN, just drop the partitions of
+	 * the old backing file. They can exist without LO_FLAGS_PARTSCAN as
+	 * they may have been added manually with BLKPG.
+	 */
+	loop_reread_partitions(lo);
 
 	error = 0;
 done:

-- 
2.54.0
```
