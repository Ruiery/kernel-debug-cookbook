---
title: [PATCH] block: don't wait for all RCU callbacks when freeing zone write plugs
list: linux-block
message_id: 20261121-feat-blk-zoned-rcu-barrier-v1-1-766875b525be@linux.dev
link: https://lore.kernel.org/linux-block/20261121-feat-blk-zoned-rcu-barrier-v1-1-766875b525be@linux.dev/
---

# [PATCH] block: don't wait for all RCU callbacks when freeing zone write plugs

来源：[https://lore.kernel.org/linux-block/20261121-feat-blk-zoned-rcu-barrier-v1-1-766875b525be@linux.dev/](https://lore.kernel.org/linux-block/20261121-feat-blk-zoned-rcu-barrier-v1-1-766875b525be@linux.dev/)

```
Zone write plugs are allocated from a per-disk mempool and freed with
call_rcu(). Before destroying the mempool, which happens every time a
zoned disk is released, disk_destroy_zone_wplugs_hash_table() calls
rcu_barrier() so that no zone write plug is still waiting to be returned
to it.

rcu_barrier() waits for the RCU callbacks queued on every CPU by anyone,
which usually takes a grace period or more, even when the disk had no
zone write plug left to free. Removing many zoned disks, such as the SMR
drives of a storage node taken offline, pays this once per disk.

Count the zone write plugs of the disk that wait for their RCU callback,
and wait only for that count to drop to zero.

Removing 32 zoned null_blk or scsi_debug devices, base and patched
kernels alternating over 2 rounds of 3 runs, median of the 6 runs and
range in parentheses; "with plugs" leaves four partially written zones,
and so four zone write plugs, on each null_blk device:

  devices                      before (ms)      after (ms)   change
  null_blk                   820 (805-885)   438 (424-454)     -47%
  null_blk, with plugs       876 (852-883)   844 (805-877)      -4%
  scsi_debug, host-managed   958 (945-991)   642 (630-652)     -33%

Signed-off-by: Qiliang Yuan <qiliang.yuan@linux.dev>
---
 block/blk-zoned.c      | 14 ++++++++++----
 include/linux/blkdev.h |  1 +
 2 files changed, 11 insertions(+), 4 deletions(-)

diff --git a/block/blk-zoned.c b/block/blk-zoned.c
index 4c58892961912..d4e50657519f3 100644
--- a/block/blk-zoned.c
+++ b/block/blk-zoned.c
@@ -18,6 +18,7 @@
 #include <linux/mempool.h>
 #include <linux/kthread.h>
 #include <linux/freezer.h>
+#include <linux/wait_bit.h>
 
 #include <trace/events/block.h>
 
@@ -724,8 +725,11 @@ static void disk_free_zone_wplug_rcu(struct rcu_head *rcu_head)
 {
 	struct blk_zone_wplug *zwplug =
 		container_of(rcu_head, struct blk_zone_wplug, rcu_head);
+	struct gendisk *disk = zwplug->disk;
 
-	mempool_free(zwplug, zwplug->disk->zone_wplugs_pool);
+	mempool_free(zwplug, disk->zone_wplugs_pool);
+	if (atomic_dec_and_test(&disk->nr_zone_wplugs_freeing))
+		wake_up_var(&disk->nr_zone_wplugs_freeing);
 }
 
 static void disk_free_zone_wplug(struct blk_zone_wplug *zwplug)
@@ -745,6 +749,7 @@ static void disk_free_zone_wplug(struct blk_zone_wplug *zwplug)
 	atomic_dec(&disk->nr_zone_wplugs);
 	spin_unlock_irqrestore(&disk->zone_wplugs_hash_lock, flags);
 
+	atomic_inc(&disk->nr_zone_wplugs_freeing);
 	call_rcu(&zwplug->rcu_head, disk_free_zone_wplug_rcu);
 }
 
@@ -2146,10 +2151,11 @@ static void disk_destroy_zone_wplugs_hash_table(struct gendisk *disk)
 	disk->zone_wplugs_hash_bits = 0;
 
 	/*
-	 * Wait for the zone write plugs to be RCU-freed before destroying the
-	 * mempool.
+	 * Wait only for the RCU callbacks freeing the zone write plugs of this
+	 * disk before destroying the mempool.
 	 */
-	rcu_barrier();
+	wait_var_event(&disk->nr_zone_wplugs_freeing,
+		       !atomic_read_acquire(&disk->nr_zone_wplugs_freeing));
 	mempool_destroy(disk->zone_wplugs_pool);
 	disk->zone_wplugs_pool = NULL;
 }
diff --git a/include/linux/blkdev.h b/include/linux/blkdev.h
index 215753171cef0..b3b356f832267 100644
--- a/include/linux/blkdev.h
+++ b/include/linux/blkdev.h
@@ -204,6 +204,7 @@ struct gendisk {
 	u8 __rcu		*zones_state;
 	unsigned int		zone_wplugs_hash_bits;
 	atomic_t		nr_zone_wplugs;
+	atomic_t		nr_zone_wplugs_freeing;
 	spinlock_t		zone_wplugs_hash_lock;
 	struct mempool		*zone_wplugs_pool;
 	struct hlist_head	*zone_wplugs_hash;

---
base-commit: 5f22fb20497f4983094131f00a734362300d22d2
change-id: 20261120-feat-blk-zoned-rcu-barrier-cb9044e67ab3

Best regards,
-- 
Qiliang Yuan <qiliang.yuan@linux.dev>
```
