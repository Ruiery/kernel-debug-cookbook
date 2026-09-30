---
title: [PATCH RFC 1/2] block: add BLK_FEAT_ATOMIC_WRITE_MULTI
list: linux-block
message_id: 20260929-nvme-mam-v1-1-48dcbe79cece@samsung.com
link: https://lore.kernel.org/linux-block/20260929-nvme-mam-v1-1-48dcbe79cece@samsung.com/
---

# [PATCH RFC 1/2] block: add BLK_FEAT_ATOMIC_WRITE_MULTI

来源：[https://lore.kernel.org/linux-block/20260929-nvme-mam-v1-1-48dcbe79cece@samsung.com/](https://lore.kernel.org/linux-block/20260929-nvme-mam-v1-1-48dcbe79cece@samsung.com/)

```
From: Daniel Gomez <da.gomez@samsung.com>

Add a feature flag that allows the block layer to merge atomic write
commands into larger ones that are not atomic as a whole but are later
divided by the device at the atomic write boundaries, with each subrange
treated as atomic. NVMe calls this Multiple Atomicity Mode (MAM).

When the flag is set, stop limiting merged atomic writes at
the atomic write boundary and cap them at max(max_sectors,
atomic_write_max_sectors). Each individual atomic write still fits one
boundary window and every window is written atomically by the device, so
each merged write stays untorn.

The feature flag can only be enabled when an atomic write boundary
is set.

No consumer yet, so no behavior changes.

Assisted-by: LLM
Signed-off-by: Daniel Gomez <da.gomez@samsung.com>
---
 block/blk-merge.c      | 9 ++++++++-
 block/blk-settings.c   | 5 +++++
 block/blk.h            | 6 +++++-
 include/linux/blkdev.h | 3 +++
 4 files changed, 21 insertions(+), 2 deletions(-)

diff --git a/block/blk-merge.c b/block/blk-merge.c
index 258a726071d12..e3c6aae2b3125 100644
--- a/block/blk-merge.c
+++ b/block/blk-merge.c
@@ -523,7 +523,14 @@ static inline unsigned int blk_rq_get_max_sectors(struct request *rq,
 	struct request_queue *q = rq->q;
 	struct queue_limits *lim = &q->limits;
 	unsigned int max_sectors, boundary_sectors;
-	bool is_atomic = rq->cmd_flags & REQ_ATOMIC;
+	/*
+	 * The merged command is itself one atomic write and must not cross the
+	 * atomic write boundary. But in the BLK_FEAT_ATOMIC_WRITE_MULTI case,
+	 * the device writes each boundary window atomically, so its merged
+	 * commands are not atomic as a whole and may cross the boundary.
+	 */
+	bool is_atomic = (rq->cmd_flags & REQ_ATOMIC) &&
+			 !(lim->features & BLK_FEAT_ATOMIC_WRITE_MULTI);
 
 	if (blk_rq_is_passthrough(rq))
 		return q->limits.max_hw_sectors;
diff --git a/block/blk-settings.c b/block/blk-settings.c
index 1f5ee2453269f..f0488dedb0b80 100644
--- a/block/blk-settings.c
+++ b/block/blk-settings.c
@@ -309,6 +309,10 @@ static void blk_validate_atomic_write_limits(struct queue_limits *lim)
 
 	boundary_sectors = lim->atomic_write_hw_boundary >> SECTOR_SHIFT;
 
+	if (WARN_ON_ONCE((lim->features & BLK_FEAT_ATOMIC_WRITE_MULTI) &&
+			 !boundary_sectors))
+		lim->features &= ~BLK_FEAT_ATOMIC_WRITE_MULTI;
+
 	if (boundary_sectors) {
 		if (WARN_ON_ONCE(lim->atomic_write_hw_max >
 				 lim->atomic_write_hw_boundary))
@@ -333,6 +337,7 @@ static void blk_validate_atomic_write_limits(struct queue_limits *lim)
 	return;
 
 unsupported:
+	lim->features &= ~BLK_FEAT_ATOMIC_WRITE_MULTI;
 	lim->atomic_write_max_sectors = 0;
 	lim->atomic_write_boundary_sectors = 0;
 	lim->atomic_write_unit_min = 0;
diff --git a/block/blk.h b/block/blk.h
index 2cc03aa54c532..8d902f41d93c0 100644
--- a/block/blk.h
+++ b/block/blk.h
@@ -241,8 +241,12 @@ static inline unsigned int blk_queue_get_max_sectors(struct request *rq)
 	if (unlikely(op == REQ_OP_WRITE_ZEROES))
 		return q->limits.max_write_zeroes_sectors;
 
-	if (rq->cmd_flags & REQ_ATOMIC)
+	if (rq->cmd_flags & REQ_ATOMIC) {
+		if (q->limits.features & BLK_FEAT_ATOMIC_WRITE_MULTI)
+			return max(q->limits.max_sectors,
+				   q->limits.atomic_write_max_sectors);
 		return q->limits.atomic_write_max_sectors;
+	}
 
 	return q->limits.max_sectors;
 }
diff --git a/include/linux/blkdev.h b/include/linux/blkdev.h
index d003a9d2d1f6c..92efd4ff67f26 100644
--- a/include/linux/blkdev.h
+++ b/include/linux/blkdev.h
@@ -360,6 +360,9 @@ typedef unsigned int __bitwise blk_features_t;
 #define BLK_FEAT_RAID_PARTIAL_STRIPES_EXPENSIVE \
 	((__force blk_features_t)(1u << 15))
 
+/* device writes each atomic write boundary window of a command atomically */
+#define BLK_FEAT_ATOMIC_WRITE_MULTI	((__force blk_features_t)(1u << 16))
+
 /*
  * Flags automatically inherited when stacking limits.
  */

-- 
2.55.0
```
