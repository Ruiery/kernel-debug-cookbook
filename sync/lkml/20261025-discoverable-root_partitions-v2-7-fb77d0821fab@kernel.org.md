---
title: [PATCH v2 7/7] docs: document discoverable root partitions
list: linux-block
message_id: 20261025-discoverable-root_partitions-v2-7-fb77d0821fab@kernel.org
link: https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-7-fb77d0821fab@kernel.org/
---

# [PATCH v2 7/7] docs: document discoverable root partitions

来源：[https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-7-fb77d0821fab@kernel.org/](https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-7-fb77d0821fab@kernel.org/)

```
Document the automatic root block device discovery feature.

Signed-off-by: Vincent Mailhol <mailhol@kernel.org>
---
Cc: Jonathan Corbet <corbet@lwn.net>
Cc: Shuah Khan <skhan@linuxfoundation.org>
Cc: Randy Dunlap <rdunlap@infradead.org>
Cc: linux-doc@vger.kernel.org
---
 Documentation/admin-guide/discoverable-root.rst | 40 +++++++++++++++++++++++++
 Documentation/admin-guide/index.rst             |  1 +
 Documentation/admin-guide/kernel-parameters.txt |  5 ++++
 3 files changed, 46 insertions(+)

diff --git a/Documentation/admin-guide/discoverable-root.rst b/Documentation/admin-guide/discoverable-root.rst
new file mode 100644
index 000000000000..f4f35cdb39fe
--- /dev/null
+++ b/Documentation/admin-guide/discoverable-root.rst
@@ -0,0 +1,40 @@
+.. SPDX-License-Identifier: GPL-2.0
+
+.. _discoverable_root:
+
+Discoverable root partitions
+============================
+
+On EFI systems, the kernel can discover the root block device from GPT partition
+type UUID metadata on the disk containing the active EFI System Partition.
+
+This follows the `Discoverable Partitions Specification`_ which defines a list
+of architecture-specific root partition type UUIDs.
+
+An initramfs providing an early userspace ``init``, a ``root=`` kernel
+command-line option, or a root device supplied through the boot protocol takes
+precedence over this automatic root partition discovery.
+
+Automatic discovery uses the Boot Loader Interface ``LoaderDevicePartUUID`` EFI
+variable to identify the partition whose disk is searched. This variable is
+provided by the boot loader or, when the kernel is booted directly by EFI
+firmware, by the Linux EFI stub.
+
+The kernel first searches for the native root partition type UUID. On
+architectures that can run compatible 32-bit user space, the matching 32-bit
+root partition type UUID may be used as a fallback if no partition with the
+native type UUID is found. If multiple partitions on that disk match the
+selected type UUID, the kernel selects the first match in block device
+enumeration order, but this may change. Systems should not expose multiple
+eligible root partitions.
+
+Partitions marked with the DPS ``no-auto`` GPT attribute are skipped. This
+allows a partition with an otherwise discoverable type UUID to opt out from
+automatic discovery.
+
+The DPS read-only attribute is not enforced by kernel root discovery. The
+root filesystem is mounted read-only by default unless ``rw`` is specified,
+and user space remains responsible for later remount policy.
+
+.. _Discoverable Partitions Specification:
+   https://uapi-group.org/specifications/specs/discoverable_partitions_specification/
diff --git a/Documentation/admin-guide/index.rst b/Documentation/admin-guide/index.rst
index cd28dfe91b06..0d9c2796ae09 100644
--- a/Documentation/admin-guide/index.rst
+++ b/Documentation/admin-guide/index.rst
@@ -50,6 +50,7 @@ Booting the kernel
 
    bootconfig
    kernel-parameters
+   discoverable-root
    efi-stub
    initrd
 
diff --git a/Documentation/admin-guide/kernel-parameters.txt b/Documentation/admin-guide/kernel-parameters.txt
index 03636d799837..75884ef72755 100644
--- a/Documentation/admin-guide/kernel-parameters.txt
+++ b/Documentation/admin-guide/kernel-parameters.txt
@@ -6732,6 +6732,11 @@ Kernel parameters
 			ramdisk, "nfs" and "cifs" for root on a network file
 			system, or "mtd" and "ubi" for mounting from raw flash.
 
+			If this option is omitted, the kernel may try to
+			discover the root block device from the GPT partition
+			type UUID metadata when additional requirements are met.
+			See Documentation/admin-guide/discoverable-root.rst.
+
 	rootdelay=	[KNL] Delay (in seconds) to pause before attempting to
 			mount the root filesystem
 

-- 
2.55.0
```
