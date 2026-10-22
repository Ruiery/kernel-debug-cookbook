---
title: [PATCH v3 2/2] nbd: drop stale partitions on NBD_CLEAR_SOCK
list: linux-block
message_id: 20261022-b4-loop-nbd-stale-partitions-v3-2-7c58ecab69c8@amutable.com
link: https://lore.kernel.org/linux-block/20261022-b4-loop-nbd-stale-partitions-v3-2-7c58ecab69c8@amutable.com/
---

# [PATCH v3 2/2] nbd: drop stale partitions on NBD_CLEAR_SOCK

来源：[https://lore.kernel.org/linux-block/20261022-b4-loop-nbd-stale-partitions-v3-2-7c58ecab69c8@amutable.com/](https://lore.kernel.org/linux-block/20261022-b4-loop-nbd-stale-partitions-v3-2-7c58ecab69c8@amutable.com/)

```
From: Daan De Meyer <daan@amutable.com>

Commit 267ec4d7223a ("loop: fix partition scan race between udev and
loop_reread_partitions()") stopped disk_force_media_change() from
setting GD_NEED_PART_SCAN. Besides requesting a rescan, that bit was what
removed stale partitions on the next open, as bdev_disk_changed() drops
all partitions before it consults disk_has_partscan().

nbd_clear_sock_ioctl() relied on that. It zeroes the capacity through
nbd_bdev_reset(), but nothing removes the partitions of the disconnected
device anymore. With the default max_part=16 they linger until the next
connect sets GD_NEED_PART_SCAN again. With max_part=0 nothing ever sets
it, so they are never removed at all, even though nbd does not set
GENHD_FL_NO_PART and partitions can therefore still be added with BLKPG.

Set GD_NEED_PART_SCAN in nbd_clear_sock_ioctl() so the partitions are
dropped on the next open. Calling bdev_disk_changed() directly is not an
option as it needs open_mutex, which nbd_open() acquires under
config_lock.

Fixes: 267ec4d7223a ("loop: fix partition scan race between udev and loop_reread_partitions()")
Cc: stable@vger.kernel.org
Reviewed-by: Christian Brauner (Amutable) <brauner@kernel.org>
Reviewed-by: Bart Van Assche <bvanassche@acm.org>
Tested-by: Shin'ichiro Kawasaki <shinichiro.kawasaki@wdc.com>
Signed-off-by: Daan De Meyer <daan@amutable.com>
---
 drivers/block/nbd.c | 7 +++++++
 1 file changed, 7 insertions(+)

diff --git a/drivers/block/nbd.c b/drivers/block/nbd.c
index ffce519bf008..09b4ad70a5d7 100644
--- a/drivers/block/nbd.c
+++ b/drivers/block/nbd.c
@@ -1616,6 +1616,13 @@ static void nbd_clear_sock_ioctl(struct nbd_device *nbd)
 	nbd_clear_sock(nbd);
 	disk_force_media_change(nbd->disk);
 	nbd_bdev_reset(nbd);
+	/*
+	 * Drop the partitions of the disconnected device on the next open.
+	 * They can exist even with max_part zero as they may have been added
+	 * manually with BLKPG. Dropping them here is not possible as that
+	 * needs open_mutex, which nbd_open() acquires under config_lock.
+	 */
+	set_bit(GD_NEED_PART_SCAN, &nbd->disk->state);
 	if (test_and_clear_bit(NBD_RT_HAS_CONFIG_REF,
 			       &nbd->config->runtime_flags))
 		nbd_config_put(nbd);

-- 
2.54.0
```
