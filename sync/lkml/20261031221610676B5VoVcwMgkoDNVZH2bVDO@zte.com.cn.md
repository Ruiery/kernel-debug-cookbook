---
title: [PATCH] zloop: reject mismatched conventional zone files on restore
list: linux-block
message_id: 20261031221610676B5VoVcwMgkoDNVZH2bVDO@zte.com.cn
link: https://lore.kernel.org/linux-block/20261031221610676B5VoVcwMgkoDNVZH2bVDO@zte.com.cn/
---

# [PATCH] zloop: reject mismatched conventional zone files on restore

来源：[https://lore.kernel.org/linux-block/20261031221610676B5VoVcwMgkoDNVZH2bVDO@zte.com.cn/](https://lore.kernel.org/linux-block/20261031221610676B5VoVcwMgkoDNVZH2bVDO@zte.com.cn/)

```
From: Shao Mingyin <shao.mingyin@zte.com.cn>

When restoring a zloop device, zloop_init_zone() checks that the size of
each conventional zone file matches the configured zone size.  The check
prints an error and then jumps to out_fput, which releases the zone file
and returns the value left in "ret" by the preceding vfs_getattr() call,
that is, zero.  zloop_ctl_add() therefore treats the zone as initialized
and continues with a zone->file pointer that was already released; any
I/O to that zone then dereferences it.

Return -EINVAL, like the sequential zone path does for the same kind of
inconsistency.

While at it, print the zone size that is actually compared instead of the
zone capacity, which may be smaller and only made the message confusing.

Fixes: eb0570c7df23 ("block: new zoned loop block device driver")
Signed-off-by: Shao Mingyin <shao.mingyin@zte.com.cn>
---

diff --git a/drivers/block/zloop.c b/drivers/block/zloop.c
index 65634a39b0bf..fb541969a47c 100644
--- a/drivers/block/zloop.c
+++ b/drivers/block/zloop.c
@@ -1161,7 +1161,8 @@ static int zloop_init_zone(struct zloop_device *zlo, struct zloop_options *opts,

 		if (restore && file_sectors != zlo->zone_size) {
 			pr_err("Invalid conventional zone %u file size (%llu sectors != %llu)\n",
-			       zone_no, file_sectors, zlo->zone_capacity);
+			       zone_no, file_sectors, zlo->zone_size);
+			ret = -EINVAL;
 			goto out_fput;
 		}
```
