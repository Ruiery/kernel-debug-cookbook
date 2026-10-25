---
title: [PATCH v2 6/7] init: add secondary DPS root partition type UUID
list: linux-block
message_id: 20261025-discoverable-root_partitions-v2-6-fb77d0821fab@kernel.org
link: https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-6-fb77d0821fab@kernel.org/
---

# [PATCH v2 6/7] init: add secondary DPS root partition type UUID

来源：[https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-6-fb77d0821fab@kernel.org/](https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-6-fb77d0821fab@kernel.org/)

```
Some 64-bit architectures can run 32-bit user space. For those
configurations, also allow DPS root discovery to use the compatible
32-bit root partition type UUID as a fallback.

Add a secondary root partition type UUID Kconfig symbol and include it
in the DPS root lookup when it is defined.

Try the secondary UUID only when the native lookup returns -ENODEV.

Suggested-by: Dave Hansen <dave.hansen@intel.com>
Link: https://lore.kernel.org/r/03be57ae-0e41-4b8a-adc5-bdd85ccce951@intel.com
Signed-off-by: Vincent Mailhol <mailhol@kernel.org>
---
 block/early-lookup.c | 3 +++
 init/Kconfig         | 7 +++++++
 2 files changed, 10 insertions(+)

diff --git a/block/early-lookup.c b/block/early-lookup.c
index 6c9664eeeb1b..b37daa105619 100644
--- a/block/early-lookup.c
+++ b/block/early-lookup.c
@@ -338,6 +338,9 @@ int __init early_lookup_dps_root(dev_t *dev)
 {
 	static const char root_type_uuids[][UUID_STRING_LEN + 1] __initconst = {
 		CONFIG_DPS_ROOT_PARTITION_TYPE_UUID,
+#ifdef CONFIG_DPS_ROOT_PARTITION_TYPE_UUID_SECONDARY
+		CONFIG_DPS_ROOT_PARTITION_TYPE_UUID_SECONDARY,
+#endif
 	};
 	static char esp_partuuid[UUID_STRING_LEN + 1] __initdata;
 	int err;
diff --git a/init/Kconfig b/init/Kconfig
index 133854355697..b605e2e1f94c 100644
--- a/init/Kconfig
+++ b/init/Kconfig
@@ -2177,6 +2177,13 @@ config DPS_ROOT_PARTITION_TYPE_UUID
 	default "4f68bce3-e8cd-4db1-96e7-fbcaf984b709" if X86_64
 	default "44479540-f297-41b2-9af7-d131d5f0458a" if X86
 
+config DPS_ROOT_PARTITION_TYPE_UUID_SECONDARY
+	depends on DPS_ROOT_PARTITION_TYPE_UUID != "" && COMPAT
+	string
+	default "69dad710-2ce4-4e3c-b16c-21a1d49abed3" if ARM64
+	default "60d5a7fe-8e7d-435c-b714-3dd8162144e1" if RISCV
+	default "44479540-f297-41b2-9af7-d131d5f0458a" if X86_64 && IA32_EMULATION
+
 config DPS_ROOT_AUTO_DISCOVERY
 	def_bool DPS_ROOT_PARTITION_TYPE_UUID != ""
 

-- 
2.55.0
```
