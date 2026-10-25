---
title: [PATCH v2 5/7] block: skip partitions with DPS no-auto GPT attribute
list: linux-block
message_id: 20261025-discoverable-root_partitions-v2-5-fb77d0821fab@kernel.org
link: https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-5-fb77d0821fab@kernel.org/
---

# [PATCH v2 5/7] block: skip partitions with DPS no-auto GPT attribute

来源：[https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-5-fb77d0821fab@kernel.org/](https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-5-fb77d0821fab@kernel.org/)

```
DPS [1] defines GPT attribute bit 63 as no-auto. Partitions with this
bit set must not be used by automatic discovery.

Store the GPT attributes in partition_meta_info and check
GPT_ATTR_NO_AUTO_DISCOVERY when matching a root partition by type UUID.

[1] The Discoverable Partitions Specification (DPS)
Link: https://uapi-group.org/specifications/specs/discoverable_partitions_specification/

Signed-off-by: Vincent Mailhol <mailhol@kernel.org>
---
 block/early-lookup.c   | 1 +
 block/partitions/efi.c | 1 +
 include/linux/blkdev.h | 4 ++++
 3 files changed, 6 insertions(+)

diff --git a/block/early-lookup.c b/block/early-lookup.c
index a1cb67eab4a0..6c9664eeeb1b 100644
--- a/block/early-lookup.c
+++ b/block/early-lookup.c
@@ -261,6 +261,7 @@ static int __init match_dev_by_type_uuid(struct device *dev, const void *data)
 	const struct uuidcmp *cmp = data;
 
 	return bdev->bd_disk == cmp->disk && bdev->bd_meta_info &&
+		!(bdev->bd_meta_info->gpt_attr & GPT_ATTR_NO_AUTO_DISCOVERY) &&
 		!strcasecmp(cmp->uuid, bdev->bd_meta_info->type_uuid);
 }
 
diff --git a/block/partitions/efi.c b/block/partitions/efi.c
index 4a3835ed9561..ed5e2f21ad85 100644
--- a/block/partitions/efi.c
+++ b/block/partitions/efi.c
@@ -741,6 +741,7 @@ int efi_partition(struct parsed_partitions *state)
 			state->parts[i + 1].flags = ADDPART_FLAG_RAID;
 
 		info = &state->parts[i + 1].info;
+		info->gpt_attr = le64_to_cpu(ptes[i].attributes);
 		efi_guid_to_str(&ptes[i].unique_partition_guid, info->uuid);
 		efi_guid_to_str(&ptes[i].partition_type_guid, info->type_uuid);
 
diff --git a/include/linux/blkdev.h b/include/linux/blkdev.h
index 52bd5683da77..629ddf1b8b7a 100644
--- a/include/linux/blkdev.h
+++ b/include/linux/blkdev.h
@@ -5,6 +5,7 @@
 #ifndef _LINUX_BLKDEV_H
 #define _LINUX_BLKDEV_H
 
+#include <linux/bits.h>
 #include <linux/types.h>
 #include <linux/blk_types.h>
 #include <linux/blk_plug.h>
@@ -65,10 +66,13 @@ extern const struct class block_class;
  */
 #define PARTITION_META_INFO_UUIDLTH	(UUID_STRING_LEN + 1)
 
+#define GPT_ATTR_NO_AUTO_DISCOVERY	BIT_U64(63)
+
 struct partition_meta_info {
 	char uuid[PARTITION_META_INFO_UUIDLTH];
 	char type_uuid[PARTITION_META_INFO_UUIDLTH];
 	u8 volname[PARTITION_META_INFO_VOLNAMELTH];
+	u64 gpt_attr;
 };
 
 /**

-- 
2.55.0
```
