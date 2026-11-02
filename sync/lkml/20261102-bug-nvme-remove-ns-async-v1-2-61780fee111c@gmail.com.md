---
title: [PATCH 2/2] block: set QUEUE_FLAG_NO_ELV_SWITCH under the read lock in del_gendisk()
list: linux-block
message_id: 20261102-bug-nvme-remove-ns-async-v1-2-61780fee111c@gmail.com
link: https://lore.kernel.org/linux-block/20261102-bug-nvme-remove-ns-async-v1-2-61780fee111c@gmail.com/
---

# [PATCH 2/2] block: set QUEUE_FLAG_NO_ELV_SWITCH under the read lock in del_gendisk()

来源：[https://lore.kernel.org/linux-block/20261102-bug-nvme-remove-ns-async-v1-2-61780fee111c@gmail.com/](https://lore.kernel.org/linux-block/20261102-bug-nvme-remove-ns-async-v1-2-61780fee111c@gmail.com/)

```
del_gendisk() takes the tag set's update_nr_hwq_lock for write to set
QUEUE_FLAG_NO_ELV_SWITCH, then for read around __del_gendisk(). The
write lock was there to wait for elevator switches from sysfs, which
held the lock for read when the flag was added.

When several disks of one tag set are deleted at once, as nvme does for
the namespaces of a controller, each write lock waits for the other
disks to get through __del_gendisk() under the read lock, and the
deletions run one after another.

Elevator switches from sysfs have taken update_nr_hwq_lock for write
since commit 4ff58d6bc9dd4 ("block: serialize elevator changes for the
same queue using a writer lock"), as updates of nr_hw_queues do. Set the
flag under the read lock instead, which still waits for both and keeps
them out.

Disconnect time of an nvme controller that removes its namespaces in
parallel, from a target on the same host, over tcp to 127.0.0.1 and
over nvme-loop, with 4 I/O queues, median of 3 runs on each of two
boots per kernel:

  namespaces  transport  before              after
           8  tcp          85 /   91 ms        51 /   47 ms
          32  tcp         294 /  293 ms        75 /   70 ms
          64  tcp         533 /  550 ms       115 /  124 ms
          64  loop       1283 / 1200 ms       185 /  204 ms

Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
 block/genhd.c | 17 +++++------------
 1 file changed, 5 insertions(+), 12 deletions(-)

diff --git a/block/genhd.c b/block/genhd.c
index 10ca8b4d6eea7..5afc60bf139e6 100644
--- a/block/genhd.c
+++ b/block/genhd.c
@@ -781,16 +781,6 @@ static void __del_gendisk(struct gendisk *disk)
 		blk_unfreeze_release_lock(q);
 }
 
-static void disable_elv_switch(struct request_queue *q)
-{
-	struct blk_mq_tag_set *set = q->tag_set;
-	WARN_ON_ONCE(!queue_is_mq(q));
-
-	down_write(&set->update_nr_hwq_lock);
-	blk_queue_flag_set(QUEUE_FLAG_NO_ELV_SWITCH, q);
-	up_write(&set->update_nr_hwq_lock);
-}
-
 /**
  * del_gendisk - remove the gendisk
  * @disk: the struct gendisk to remove
@@ -820,10 +810,13 @@ void del_gendisk(struct gendisk *disk)
 	} else {
 		set = disk->queue->tag_set;
 
-		disable_elv_switch(disk->queue);
-
 		memflags = memalloc_noio_save();
 		down_read(&set->update_nr_hwq_lock);
+		/*
+		 * Set the flag under the read lock, as elevator switches take
+		 * update_nr_hwq_lock for write.
+		 */
+		blk_queue_flag_set(QUEUE_FLAG_NO_ELV_SWITCH, disk->queue);
 		__del_gendisk(disk);
 		up_read(&set->update_nr_hwq_lock);
 		memalloc_noio_restore(memflags);

-- 
2.43.0
```
