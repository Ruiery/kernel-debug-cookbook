---
title: [PATCH RFC 2/2] nvme: enable multiple atomicity mode
list: linux-block
message_id: 20260929-nvme-mam-v1-2-48dcbe79cece@samsung.com
link: https://lore.kernel.org/linux-block/20260929-nvme-mam-v1-2-48dcbe79cece@samsung.com/
---

# [PATCH RFC 2/2] nvme: enable multiple atomicity mode

来源：[https://lore.kernel.org/linux-block/20260929-nvme-mam-v1-2-48dcbe79cece@samsung.com/](https://lore.kernel.org/linux-block/20260929-nvme-mam-v1-2-48dcbe79cece@samsung.com/)

```
From: Daniel Gomez <da.gomez@samsung.com>

Add support for Multiple Atomicity Mode (MAM), a superset of Single
Atomicity Mode (SAM) where the controller divides a write command that
crosses the atomic boundaries into per-window atomic writes. Honoring
the mode lets contiguous atomic writes merge past the atomic unit
limits.

Set BLK_FEAT_ATOMIC_WRITE_MULTI when the namespace reports MAM and its
atomic parameters are compliant; otherwise fall back to SAM. Re-derive
the flag on every rescan, and skip the single-write unit_max and
boundary checks because a merged atomic carrier can exceed both.

Assisted-by: LLM
Signed-off-by: Daniel Gomez <da.gomez@samsung.com>
---
 drivers/nvme/host/core.c | 23 +++++++++++++++++++++++
 include/linux/nvme.h     |  1 +
 2 files changed, 24 insertions(+)

diff --git a/drivers/nvme/host/core.c b/drivers/nvme/host/core.c
index 9bcab3dc4c118..69a565ac0da97 100644
--- a/drivers/nvme/host/core.c
+++ b/drivers/nvme/host/core.c
@@ -993,6 +993,9 @@ static bool nvme_valid_atomic_write(struct request *req)
 	struct request_queue *q = req->q;
 	u32 boundary_bytes = queue_atomic_write_boundary_bytes(q);
 
+	if (q->limits.features & BLK_FEAT_ATOMIC_WRITE_MULTI)
+		return true;
+
 	if (blk_rq_bytes(req) > queue_atomic_write_unit_max_bytes(q))
 		return false;
 
@@ -2038,12 +2041,24 @@ static void nvme_configure_metadata(struct nvme_ctrl *ctrl,
 	}
 }
 
+static bool nvme_mam_compliant(struct nvme_id_ns *id)
+{
+	if (id->nabspf != id->nawupf)
+		return false;
+	if (id->nabsn && id->nabsn != id->nabspf)
+		return false;
+	if (id->nawun && id->nawun != id->nawupf)
+		return false;
+	return true;
+}
 
 static u32 nvme_configure_atomic_write(struct nvme_ns *ns,
 		struct nvme_id_ns *id, struct queue_limits *lim, u32 bs)
 {
 	u32 atomic_bs, boundary = 0;
 
+	lim->features &= ~BLK_FEAT_ATOMIC_WRITE_MULTI;
+
 	/*
 	 * We do not support an offset for the atomic boundaries.
 	 */
@@ -2057,6 +2072,14 @@ static u32 nvme_configure_atomic_write(struct nvme_ns *ns,
 		atomic_bs = (1 + le16_to_cpu(id->nawupf)) * bs;
 		if (id->nabspf)
 			boundary = (le16_to_cpu(id->nabspf) + 1) * bs;
+
+		if (id->nsfeat & NVME_NS_FEAT_MAM) {
+			if (nvme_mam_compliant(id))
+				lim->features |= BLK_FEAT_ATOMIC_WRITE_MULTI;
+			else
+				dev_warn_once(ns->ctrl->device,
+					"Inconsistent MAM parameters, ignoring\n");
+		}
 	} else {
 		if (ns->ctrl->awupf)
 			dev_info_once(ns->ctrl->device,
diff --git a/include/linux/nvme.h b/include/linux/nvme.h
index 91ce434a7e8d9..8fdc4b91cf906 100644
--- a/include/linux/nvme.h
+++ b/include/linux/nvme.h
@@ -602,6 +602,7 @@ enum {
 	NVME_NS_FEAT_OPTPERF_MASK = 0x1,
 	/* Since version 2.1, OPTPERF is bits 4 and 5 of NSFEAT */
 	NVME_NS_FEAT_OPTPERF_MASK_2_1 = 0x3,
+	NVME_NS_FEAT_MAM	= 1 << 6,
 	NVME_NS_ATTR_RO		= 1 << 0,
 	NVME_NS_FLBAS_LBA_MASK	= 0xf,
 	NVME_NS_FLBAS_LBA_UMASK	= 0x60,

-- 
2.55.0
```
