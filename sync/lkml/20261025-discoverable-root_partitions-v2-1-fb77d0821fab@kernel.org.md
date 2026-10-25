---
title: [PATCH v2 1/7] block: store GPT partition type UUID
list: linux-block
message_id: 20261025-discoverable-root_partitions-v2-1-fb77d0821fab@kernel.org
link: https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-1-fb77d0821fab@kernel.org/
---

# [PATCH v2 1/7] block: store GPT partition type UUID

来源：[https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-1-fb77d0821fab@kernel.org/](https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-1-fb77d0821fab@kernel.org/)

```
DPS [1] identifies OS partitions by GPT partition type UUID.

Keep that UUID in struct partition_meta_info and populate it while
scanning GPT partition tables so early root discovery can use it.

[1] The Discoverable Partitions Specification (DPS)
Link: https://uapi-group.org/specifications/specs/discoverable_partitions_specification/

Signed-off-by: Vincent Mailhol <mailhol@kernel.org>
---
 block/partitions/efi.c | 1 +
 include/linux/blkdev.h | 1 +
 2 files changed, 2 insertions(+)

diff --git a/block/partitions/efi.c b/block/partitions/efi.c
index 9865d59093fa..4a3835ed9561 100644
--- a/block/partitions/efi.c
+++ b/block/partitions/efi.c
@@ -742,6 +742,7 @@ int efi_partition(struct parsed_partitions *state)
 
 		info = &state->parts[i + 1].info;
 		efi_guid_to_str(&ptes[i].unique_partition_guid, info->uuid);
+		efi_guid_to_str(&ptes[i].partition_type_guid, info->type_uuid);
 
 		/* Naively convert UTF16-LE to 7 bits. */
 		label_max = min(ARRAY_SIZE(info->volname) - 1,
diff --git a/include/linux/blkdev.h b/include/linux/blkdev.h
index d003a9d2d1f6..b99a59cd1120 100644
--- a/include/linux/blkdev.h
+++ b/include/linux/blkdev.h
@@ -67,6 +67,7 @@ extern const struct class block_class;
 
 struct partition_meta_info {
 	char uuid[PARTITION_META_INFO_UUIDLTH];
+	char type_uuid[PARTITION_META_INFO_UUIDLTH];
 	u8 volname[PARTITION_META_INFO_VOLNAMELTH];
 };
 

-- 
2.55.0
```
