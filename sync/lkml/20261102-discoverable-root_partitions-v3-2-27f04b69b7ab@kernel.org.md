---
title: [PATCH v3 2/7] block: add DPS root partition type UUID definitions
list: linux-block
message_id: 20261102-discoverable-root_partitions-v3-2-27f04b69b7ab@kernel.org
link: https://lore.kernel.org/linux-block/20261102-discoverable-root_partitions-v3-2-27f04b69b7ab@kernel.org/
---

# [PATCH v3 2/7] block: add DPS root partition type UUID definitions

来源：[https://lore.kernel.org/linux-block/20261102-discoverable-root_partitions-v3-2-27f04b69b7ab@kernel.org/](https://lore.kernel.org/linux-block/20261102-discoverable-root_partitions-v3-2-27f04b69b7ab@kernel.org/)

```
DPS [1] assigns a native root partition type UUID to each supported
architecture. Add a hidden DPS_ROOT_PARTITION_TYPE_UUID string symbol
and populate it from the architecture selected in Kconfig. Only
architectures with EFI support in the kernel are added.

Gate the symbol on EFI and EFI_PARTITION because discovery needs block
devices, EFI runtime services and GPT partition parsing.

Derive the hidden DPS_ROOT_AUTO_DISCOVERY boolean from whether
DPS_ROOT_PARTITION_TYPE_UUID is nonempty.

[1] The Discoverable Partitions Specification (DPS)
Link: https://uapi-group.org/specifications/specs/discoverable_partitions_specification/

Signed-off-by: Vincent Mailhol <mailhol@kernel.org>
---
 block/Kconfig | 14 ++++++++++++++
 1 file changed, 14 insertions(+)

diff --git a/block/Kconfig b/block/Kconfig
index 70e4a66d941f..3b5d3ad42dde 100644
--- a/block/Kconfig
+++ b/block/Kconfig
@@ -211,6 +211,20 @@ config BLK_INLINE_ENCRYPTION_FALLBACK
 
 source "block/partitions/Kconfig"
 
+config DPS_ROOT_PARTITION_TYPE_UUID
+	depends on EFI && EFI_PARTITION
+	string
+	default "69dad710-2ce4-4e3c-b16c-21a1d49abed3" if ARM
+	default "b921b045-1df0-41c3-af44-4c6f280d3fae" if ARM64
+	default "77055800-792c-4f94-b39a-98c91b762bb6" if LOONGARCH && 64BIT
+	default "72ec70a6-cf74-40e6-bd49-4bda08e8f224" if RISCV && 64BIT
+	default "60d5a7fe-8e7d-435c-b714-3dd8162144e1" if RISCV
+	default "4f68bce3-e8cd-4db1-96e7-fbcaf984b709" if X86_64
+	default "44479540-f297-41b2-9af7-d131d5f0458a" if X86
+
+config DPS_ROOT_AUTO_DISCOVERY
+	def_bool DPS_ROOT_PARTITION_TYPE_UUID != ""
+
 config BLK_PM
 	def_bool PM
 

-- 
2.56.0
```
