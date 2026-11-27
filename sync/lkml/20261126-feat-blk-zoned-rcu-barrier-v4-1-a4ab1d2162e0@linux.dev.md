---
title: [PATCH v4 1/2] block: don't wait for all RCU callbacks when freeing zone write plugs
list: linux-block
message_id: 20261126-feat-blk-zoned-rcu-barrier-v4-1-a4ab1d2162e0@linux.dev
link: https://lore.kernel.org/linux-block/20261126-feat-blk-zoned-rcu-barrier-v4-1-a4ab1d2162e0@linux.dev/
---

# [PATCH v4 1/2] block: don't wait for all RCU callbacks when freeing zone write plugs

来源：[https://lore.kernel.org/linux-block/20261126-feat-blk-zoned-rcu-barrier-v4-1-a4ab1d2162e0@linux.dev/](https://lore.kernel.org/linux-block/20261126-feat-blk-zoned-rcu-barrier-v4-1-a4ab1d2162e0@linux.dev/)

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
and call rcu_barrier() only when that count is not zero. Use
rcu_barrier() rather than waiting for the count to drop, so that lazily
queued callbacks (CONFIG_RCU_LAZY) are still flushed.

Removing 32 zoned null_blk or scsi_debug devices, base and patched
kernels alternating over 4 rounds of 5 runs, median of the 20 runs and
interquartile range in parentheses; "with plugs" leaves four partially
written zones, and so four zone write plugs, on each null_blk device:

  devices                        before (ms)      after (ms)   change
  null_blk                     848 (828-862)   424 (410-430)     -50%
  null_blk, with plugs         865 (854-876)   876 (866-886)      +1%
  scsi_debug, host-managed  1057 (1024-1092)   740 (722-779)     -30%

Signed-off-by: Qiliang Yuan <qiliang.yuan@linux.dev>
---
 block/blk-zoned.c      | 14 ++++++++++++--
 include/linux/blkdev.h |  1 +
 2 files changed, 13 insertions(+), 2 deletions(-)

diff --git a/block/blk-zoned.c b/block/blk-zoned.c
index 4c58892961912..e181ddb1b41b2 100644
--- a/block/blk-zoned.c
+++ b/block/blk-zoned.c
@@ -724,8 +724,15 @@ static void disk_free_zone_wplug_rcu(struct rcu_head *rcu_head)
 {
 	struct blk_zone_wplug *zwplug =
 		container_of(rcu_head, struct blk_zone_wplug, rcu_head);
+	struct gendisk *disk = zwplug->disk;
 
-	mempool_free(zwplug, zwplug->disk->zone_wplugs_pool);
+	mempool_free(zwplug, disk->zone_wplugs_pool);
+	/*
+	 * Pairs with atomic_read_acquire() in
+	 * disk_destroy_zone_wplugs_hash_table().
+	 */
+	smp_mb__before_atomic();
+	atomic_dec(&disk->nr_zone_wplugs_freeing);
 }
 
 static void disk_free_zone_wplug(struct blk_zone_wplug *zwplug)
@@ -745,6 +752,7 @@ static void disk_free_zone_wplug(struct blk_zone_wplug *zwplug)
 	atomic_dec(&disk->nr_zone_wplugs);
 	spin_unlock_irqrestore(&disk->zone_wplugs_hash_lock, flags);
 
+	atomic_inc(&disk->nr_zone_wplugs_freeing);
 	call_rcu(&zwplug->rcu_head, disk_free_zone_wplug_rcu);
 }
 
@@ -2022,6 +2030,7 @@ void disk_init_zone_resources(struct gendisk *disk)
 {
 	mutex_init(&disk->zone_revalidate_mutex);
 	atomic_set(&disk->nr_zone_wplugs, 0);
+	atomic_set(&disk->nr_zone_wplugs_freeing, 0);
 	spin_lock_init(&disk->zone_wplugs_hash_lock);
 	spin_lock_init(&disk->zone_wplugs_list_lock);
 	INIT_LIST_HEAD(&disk->zone_wplugs_list);
@@ -2149,7 +2158,8 @@ static void disk_destroy_zone_wplugs_hash_table(struct gendisk *disk)
 	 * Wait for the zone write plugs to be RCU-freed before destroying the
 	 * mempool.
 	 */
-	rcu_barrier();
+	if (atomic_read_acquire(&disk->nr_zone_wplugs_freeing))
+		rcu_barrier();
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

-- 
2.43.0
```
