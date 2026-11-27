---
title: [PATCH v4 2/2] block: free remaining zone write plugs directly on disk release
list: linux-block
message_id: 20261126-feat-blk-zoned-rcu-barrier-v4-2-a4ab1d2162e0@linux.dev
link: https://lore.kernel.org/linux-block/20261126-feat-blk-zoned-rcu-barrier-v4-2-a4ab1d2162e0@linux.dev/
---

# [PATCH v4 2/2] block: free remaining zone write plugs directly on disk release

来源：[https://lore.kernel.org/linux-block/20261126-feat-blk-zoned-rcu-barrier-v4-2-a4ab1d2162e0@linux.dev/](https://lore.kernel.org/linux-block/20261126-feat-blk-zoned-rcu-barrier-v4-2-a4ab1d2162e0@linux.dev/)

```
disk_destroy_zone_wplugs_hash_table() runs from disk_release() and frees
the zone write plugs still in the hash table by marking them dead, which
drops their last reference and queues them for RCU freeing. Nothing can
look up a plug at that point: the function already walks the hash table
without zone_wplugs_hash_lock and frees the table itself with kfree().

Zoned drives taken offline usually have partially written zones, so
their plugs are still in the hash table when the disk is released. Each
such disk then queues RCU callbacks and waits for them in rcu_barrier()
before destroying the mempool.

Unhash these plugs and return them to the mempool directly, keeping the
checks of disk_free_zone_wplug(). The zones state array that freeing
them would update is freed right after by disk_release_zone_resources().

Removing 32 zoned null_blk or scsi_debug devices, kernels with and
without this patch alternating over 4 rounds of 5 runs, in the same
rounds as the previous patch, median of the 20 runs and interquartile
range in parentheses; "with plugs" leaves four partially written zones,
and so four zone write plugs, on each null_blk device, and the
scsi_debug devices have no plugs left at release:

  devices                     before (ms)      after (ms)   change
  null_blk                  424 (410-430)   428 (414-438)      +1%
  null_blk, with plugs      876 (866-886)   433 (426-438)     -51%
  scsi_debug, host-managed  740 (722-779)   742 (722-767)       0%

Suggested-by: Bart Van Assche <bvanassche@acm.org>
Signed-off-by: Qiliang Yuan <qiliang.yuan@linux.dev>
---
 block/blk-zoned.c | 15 +++++++++++----
 1 file changed, 11 insertions(+), 4 deletions(-)

diff --git a/block/blk-zoned.c b/block/blk-zoned.c
index e181ddb1b41b2..bb8e614bf1bb3 100644
--- a/block/blk-zoned.c
+++ b/block/blk-zoned.c
@@ -2138,14 +2138,21 @@ static void disk_destroy_zone_wplugs_hash_table(struct gendisk *disk)
 	if (!disk->zone_wplugs_hash)
 		return;
 
-	/* Free all the zone write plugs we have. */
+	/*
+	 * Free all the zone write plugs we have. The disk is being released, so
+	 * no one can look them up anymore and there is no need to wait for an
+	 * RCU grace period. The zones state array is freed right after this.
+	 */
 	for (i = 0; i < disk_zone_wplugs_hash_size(disk); i++) {
 		while (!hlist_empty(&disk->zone_wplugs_hash[i])) {
 			zwplug = hlist_entry(disk->zone_wplugs_hash[i].first,
 					     struct blk_zone_wplug, node);
-			spin_lock_irq(&zwplug->lock);
-			disk_mark_zone_wplug_dead(zwplug);
-			spin_unlock_irq(&zwplug->lock);
+			WARN_ON_ONCE(refcount_read(&zwplug->ref) != 1);
+			WARN_ON_ONCE(zwplug->flags & BLK_ZONE_WPLUG_PLUGGED);
+			WARN_ON_ONCE(!bio_list_empty(&zwplug->bio_list));
+			hlist_del(&zwplug->node);
+			atomic_dec(&disk->nr_zone_wplugs);
+			mempool_free(zwplug, disk->zone_wplugs_pool);
 		}
 	}
 

-- 
2.43.0
```
