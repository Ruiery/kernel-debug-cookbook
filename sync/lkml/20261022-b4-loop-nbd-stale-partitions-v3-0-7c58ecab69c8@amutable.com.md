---
title: [PATCH v3 0/2] loop, nbd: drop partitions left behind by the GD_NEED_PART_SCAN removal
list: linux-block
message_id: 20261022-b4-loop-nbd-stale-partitions-v3-0-7c58ecab69c8@amutable.com
link: https://lore.kernel.org/linux-block/20261022-b4-loop-nbd-stale-partitions-v3-0-7c58ecab69c8@amutable.com/
---

# [PATCH v3 0/2] loop, nbd: drop partitions left behind by the GD_NEED_PART_SCAN removal

来源：[https://lore.kernel.org/linux-block/20261022-b4-loop-nbd-stale-partitions-v3-0-7c58ecab69c8@amutable.com/](https://lore.kernel.org/linux-block/20261022-b4-loop-nbd-stale-partitions-v3-0-7c58ecab69c8@amutable.com/)

```
Commit 267ec4d7223a ("loop: fix partition scan race between udev and
loop_reread_partitions()") stopped disk_force_media_change() from setting
GD_NEED_PART_SCAN. The caller audit in that commit only considered the bit
as a request to rescan partitions, but it did more than that:
bdev_disk_changed() drops every entry in disk->part_tbl before it consults
disk_has_partscan(), and only the re-adding half is gated on partition
scanning being enabled. The lazy scan on the next open was therefore also
the only thing removing partitions from a device that has partitions but
no partition scanning.

Loop devices without LO_FLAGS_PARTSCAN are exactly such devices, and they
are not unusual. bdev_add_partition() only rejects GENHD_FL_NO_PART disks,
so BLKPG_ADD_PARTITION works while GD_SUPPRESS_PART_SCAN is set, and
parted, libfdisk and systemd all fall back to BLKPG when BLKRRPART fails
with -EINVAL, which is what a loop device without LO_FLAGS_PARTSCAN
returns.

Commit c4f4c0fc551c ("loop: remove manually added partitions on detach")
fixed the detach path after this was reported as loop devices picking up
partition devices from a previously built image:

  https://bugs.debian.org/1141434

These two patches fix the two remaining places that relied on the same
lazy cleanup, LOOP_CHANGE_FD and NBD_CLEAR_SOCK.

Regression tests for both paths have been submitted to blktests:

  https://github.com/linux-blktests/blktests/pull/259
  https://github.com/linux-blktests/blktests/pull/260

Signed-off-by: Daan De Meyer <daan@amutable.com>
---
Changes in v3:
- Rebase onto current mainline.
- No functional changes.
- Link to v2: https://patch.msgid.link/20260824-b4-loop-nbd-stale-partitions-v2-0-9815a577cebd@amutable.com

Changes in v2:
- Rewrap the comments added by both patches so they fit in 80 columns
  (Christoph Hellwig).
- No functional change, so the review and test tags from v1 were carried
  over.
- Link to v1: https://patch.msgid.link/20260806-b4-loop-nbd-stale-partitions-v1-0-67bb75a8d7be@amutable.com

To: Jens Axboe <axboe@kernel.dk>
To: Daan De Meyer <daan.j.demeyer@gmail.com>
To: Christian Brauner <brauner@kernel.org>
To: Josef Bacik <josef@toxicpanda.com>
Cc: linux-block@vger.kernel.org
Cc: linux-kernel@vger.kernel.org
Cc: nbd@other.debian.org

---
Daan De Meyer (2):
      loop: drop stale partitions on LOOP_CHANGE_FD
      nbd: drop stale partitions on NBD_CLEAR_SOCK

 drivers/block/loop.c | 10 ++++++----
 drivers/block/nbd.c  |  7 +++++++
 2 files changed, 13 insertions(+), 4 deletions(-)
---
base-commit: 7be4bc52fd9e0e55dc9a2e0232b89427d2c4b614
change-id: 20260806-b4-loop-nbd-stale-partitions-2d10ede71a2a

Best regards,
--  
Daan De Meyer <daan@amutable.com>
```
