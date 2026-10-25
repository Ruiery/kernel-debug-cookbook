---
title: [PATCH v2 4/7] init: discover root by DPS partition type UUID
list: linux-block
message_id: 20261025-discoverable-root_partitions-v2-4-fb77d0821fab@kernel.org
link: https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-4-fb77d0821fab@kernel.org/
---

# [PATCH v2 4/7] init: discover root by DPS partition type UUID

来源：[https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-4-fb77d0821fab@kernel.org/](https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-4-fb77d0821fab@kernel.org/)

```
When root= and ROOT_DEV are not set, discover the root block device
using the architecture's DPS root partition type UUID. Preserve explicit
root selection and an existing ROOT_DEV supplied by the boot protocol.

DPS [1] restricts discovery to the disk containing the active EFI System
Partition. Read LoaderDevicePartUUID from the Boot Loader Interface to
identify that disk and cache the UUID for subsequent lookup attempts.

Add early_lookup_bdev_by_type_uuid() to select the first matching
partition. The EFI System Partition may become visible before the root
partition has been registered. Hold the disk's open_mutex during lookup
so partition scanning finishes before returning -ENODEV.

Add early_lookup_dps_root() and have lookup_root_device() call it when
root= is absent. early_lookup_bdev() is kept unchanged so other callers
cannot trigger root discovery inadvertently. Return -EINVAL if the EFI
variable cannot be read or does not contain a valid UUID, so
lookup_root_device() disables rootwait. Return -EAGAIN if the EFI
partition is not available yet so rootwait can retry. Return -ENODEV if
its disk has no matching root partition. In that case, have
lookup_root_device() disable rootwait, clear the device number and
return zero to stop retries.

[1] The Discoverable Partitions Specification (DPS)
Link: https://uapi-group.org/specifications/specs/discoverable_partitions_specification/

Signed-off-by: Vincent Mailhol <mailhol@kernel.org>
---
 block/early-lookup.c   | 115 +++++++++++++++++++++++++++++++++++++++++++++++--
 include/linux/blkdev.h |  10 +++++
 init/do_mounts.c       |  25 +++++++++--
 3 files changed, 143 insertions(+), 7 deletions(-)

diff --git a/block/early-lookup.c b/block/early-lookup.c
index 3fb57f7d2b12..a1cb67eab4a0 100644
--- a/block/early-lookup.c
+++ b/block/early-lookup.c
@@ -5,10 +5,14 @@
  */
 #include <linux/blkdev.h>
 #include <linux/ctype.h>
+#include <linux/efi.h>
+#include <linux/ucs2_string.h>
+#include <linux/uuid.h>
 
 struct uuidcmp {
 	const char *uuid;
 	int len;
+	struct gendisk *disk;
 };
 
 /**
@@ -45,13 +49,11 @@ static int __init match_dev_by_uuid(struct device *dev, const void *data)
  */
 static int __init devt_from_partuuid(const char *uuid_str, dev_t *devt)
 {
-	struct uuidcmp cmp;
+	struct uuidcmp cmp = { .uuid = uuid_str };
 	struct device *dev = NULL;
 	int offset = 0;
 	char *slash;
 
-	cmp.uuid = uuid_str;
-
 	slash = strchr(uuid_str, '/');
 	/* Check for optional partition number offset attributes. */
 	if (slash) {
@@ -252,6 +254,113 @@ int __init early_lookup_bdev(const char *name, dev_t *devt)
 	return devt_from_devnum(name, devt);
 }
 
+#ifdef CONFIG_DPS_ROOT_AUTO_DISCOVERY
+static int __init match_dev_by_type_uuid(struct device *dev, const void *data)
+{
+	struct block_device *bdev = dev_to_bdev(dev);
+	const struct uuidcmp *cmp = data;
+
+	return bdev->bd_disk == cmp->disk && bdev->bd_meta_info &&
+		!strcasecmp(cmp->uuid, bdev->bd_meta_info->type_uuid);
+}
+
+/*
+ * Search the ESP's disk for an eligible partition of the requested type.
+ * Return -EAGAIN until the ESP is available, or -ENODEV if no match exists.
+ */
+static int __init early_lookup_bdev_by_type_uuid(const char *type_uuid,
+						 const char *esp_partuuid,
+						 dev_t *devt)
+{
+	struct uuidcmp esp_cmp = {
+		.uuid = esp_partuuid,
+		.len = UUID_STRING_LEN,
+	};
+	struct uuidcmp type_cmp = {
+		.uuid = type_uuid,
+	};
+	struct device *esp_dev;
+	struct device *type_dev;
+
+	esp_dev = class_find_device(&block_class, NULL, &esp_cmp,
+				    &match_dev_by_uuid);
+	if (!esp_dev)
+		return -EAGAIN;
+
+	type_cmp.disk = dev_to_disk(esp_dev);
+	scoped_guard(mutex, &type_cmp.disk->open_mutex)
+		type_dev = class_find_device(&block_class, NULL, &type_cmp,
+					     &match_dev_by_type_uuid);
+	put_device(esp_dev);
+	if (!type_dev)
+		return -ENODEV;
+
+	*devt = type_dev->devt;
+	pr_info("VFS: Discovered root partition /dev/%pg with GPT type UUID %s\n",
+		dev_to_bdev(type_dev), type_uuid);
+	put_device(type_dev);
+	return 0;
+}
+
+static int __init efi_get_esp_partuuid(char *partuuid, size_t size)
+{
+	static efi_guid_t loader_guid __initdata = LINUX_EFI_LOADER_ENTRY_GUID;
+	efi_char16_t partuuid_ucs2[UUID_STRING_LEN + 1] = {};
+	unsigned long partuuid_ucs2_size = sizeof(partuuid_ucs2);
+	efi_status_t status;
+
+	if (!efi_rt_services_supported(EFI_RT_SUPPORTED_GET_VARIABLE))
+		return -EOPNOTSUPP;
+
+	status = efi.get_variable(L"LoaderDevicePartUUID", &loader_guid, NULL,
+				  &partuuid_ucs2_size, partuuid_ucs2);
+	if (status != EFI_SUCCESS)
+		return efi_status_to_err(status);
+
+	if (ucs2_as_utf8((u8 *)partuuid, partuuid_ucs2, size) != UUID_STRING_LEN ||
+	    !uuid_is_valid(partuuid))
+		return -EINVAL;
+
+	return 0;
+}
+
+/**
+ * early_lookup_dps_root - discover the root device by DPS partition type UUID
+ * @dev: receives the discovered device number
+ *
+ * Return: 0 on success, -EINVAL if the ESP partition UUID cannot be read or
+ * is invalid, -EAGAIN if the EFI partition is not yet available, or -ENODEV
+ * if no matching root exists.
+ * With DPS disabled, return 0 and set @dev to zero.
+ */
+int __init early_lookup_dps_root(dev_t *dev)
+{
+	static const char root_type_uuids[][UUID_STRING_LEN + 1] __initconst = {
+		CONFIG_DPS_ROOT_PARTITION_TYPE_UUID,
+	};
+	static char esp_partuuid[UUID_STRING_LEN + 1] __initdata;
+	int err;
+
+	if (!esp_partuuid[0]) {
+		err = efi_get_esp_partuuid(esp_partuuid, sizeof(esp_partuuid));
+		if (err) {
+			pr_err("VFS: Unable to get EFI partition UUID: %pe, skipping root partition discovery\n",
+				ERR_PTR(err));
+			return -EINVAL;
+		}
+	}
+
+	for (int i = 0; i < ARRAY_SIZE(root_type_uuids); i++) {
+		err = early_lookup_bdev_by_type_uuid(root_type_uuids[i],
+						     esp_partuuid, dev);
+		if (err != -ENODEV)
+			return err;
+	}
+
+	return -ENODEV;
+}
+#endif /* CONFIG_DPS_ROOT_AUTO_DISCOVERY */
+
 static char __init *bdevt_str(dev_t devt, char *buf)
 {
 	if (MAJOR(devt) <= 0xff && MINOR(devt) <= 0xff) {
diff --git a/include/linux/blkdev.h b/include/linux/blkdev.h
index b99a59cd1120..52bd5683da77 100644
--- a/include/linux/blkdev.h
+++ b/include/linux/blkdev.h
@@ -1746,6 +1746,16 @@ static inline int early_lookup_bdev(const char *pathname, dev_t *dev)
 }
 #endif /* CONFIG_BLOCK */
 
+#ifdef CONFIG_DPS_ROOT_AUTO_DISCOVERY
+int __init early_lookup_dps_root(dev_t *dev);
+#else
+static inline int early_lookup_dps_root(dev_t *dev)
+{
+	*dev = 0;
+	return 0;
+}
+#endif
+
 int bdev_freeze(struct block_device *bdev);
 int bdev_thaw(struct block_device *bdev);
 int bdev_deny_freeze(struct block_device *bdev);
diff --git a/init/do_mounts.c b/init/do_mounts.c
index b9814d0cc5a6..0dd9d2a6c00b 100644
--- a/init/do_mounts.c
+++ b/init/do_mounts.c
@@ -406,10 +406,24 @@ static int __init lookup_root_device(const char *root_device_name, dev_t *dev)
 {
 	int err;
 
-	err = early_lookup_bdev(root_device_name, dev);
+	if (root_device_name[0]) {
+		err = early_lookup_bdev(root_device_name, dev);
+		if (err == -EINVAL && root_wait) {
+			pr_err("VFS: root= is invalid; disabling rootwait.\n");
+			root_wait = 0;
+		}
+		return err;
+	}
+
+	err = early_lookup_dps_root(dev);
 	if (err == -EINVAL && root_wait) {
-		pr_err("VFS: root= is invalid; disabling rootwait.\n");
+		pr_err("VFS: Root discovery is unavailable; disabling rootwait.\n");
 		root_wait = 0;
+	} else if (err == -ENODEV) {
+		pr_err("VFS: No discoverable root partition found; aborting.\n");
+		root_wait = 0;
+		*dev = 0;
+		return 0;
 	}
 	return err;
 }
@@ -422,7 +436,10 @@ static void __init wait_for_root(char *root_device_name)
 	if (ROOT_DEV != 0)
 		return;
 
-	pr_info("Waiting for root device %s...\n", root_device_name);
+	if (root_device_name[0])
+		pr_info("Waiting for root device %s...\n", root_device_name);
+	else if (IS_ENABLED(CONFIG_DPS_ROOT_AUTO_DISCOVERY))
+		pr_info("Waiting for discoverable root partition...\n");
 
 	end = ktime_add_ms(ktime_get_raw(), root_wait);
 
@@ -480,7 +497,7 @@ void __init prepare_namespace(void)
 
 	md_r
```
