---
title: [PATCH v13 2/2] block: implement NVMEM provider
list: linux-block
message_id: 20261123-block-as-nvmem-v13-2-96ffe1f59332@oss.qualcomm.com
link: https://lore.kernel.org/linux-block/20261123-block-as-nvmem-v13-2-96ffe1f59332@oss.qualcomm.com/
---

# [PATCH v13 2/2] block: implement NVMEM provider

来源：[https://lore.kernel.org/linux-block/20261123-block-as-nvmem-v13-2-96ffe1f59332@oss.qualcomm.com/](https://lore.kernel.org/linux-block/20261123-block-as-nvmem-v13-2-96ffe1f59332@oss.qualcomm.com/)

```
On embedded devices using an eMMC it is common that one or more partitions
on the eMMC are used to store MAC addresses and Wi-Fi calibration EEPROM
data. Allow referencing the partition in device tree for the kernel and
Wi-Fi drivers accessing it via the NVMEM layer.

NVMEM is registered for a block device whose OF node describes an NVMEM
layout, either via an "nvmem-layout" child or by being a "fixed-layout"
node itself (e.g. an eMMC boot partition associated through its mmc-card
node).

The NVMEM device is a read-only side channel onto a block device.
Each read opens the block device with BLK_OPEN_EXCL to keep other
exclusive openers away for the duration of the access.

Both the registration and the removal of the NVMEM device are deferred to
an ordered workqueue, because they may run from under disk->open_mutex
(add_partition(), drop_partition()) while:

 - nvmem_register() can read the device through ->reg_read() to let a
   layout driver populate its cells, and
 - nvmem_unregister() waits for the in-flight readers to drain.

As ->reg_read() opens the block device, and thus takes disk->open_mutex
itself, registering synchronously would self-deadlock, and unregistering
synchronously would deadlock against a reader blocked on disk->open_mutex
while holding the NVMEM SRCU read lock.

Keeping the queue ordered guarantees that, for a given block device, the
registration has completed before the removal starts, and that the removal
of a partition completes before the registration of its replacement, which
otherwise would clash on the NVMEM device name when a partition table is
re-read.

Consumers looking up a cell before the provider shows up get -EPROBE_DEFER
from the NVMEM core and retry later.

Reviewed-by: Bartosz Golaszewski <bartosz.golaszewski@oss.qualcomm.com>
Reviewed-by: Christoph Hellwig <hch@lst.de>
Signed-off-by: Loic Poulain <loic.poulain@oss.qualcomm.com>
---
 block/Kconfig             |  11 +++
 block/Makefile            |   1 +
 block/blk-nvmem.c         | 197 ++++++++++++++++++++++++++++++++++++++++++++++
 block/blk.h               |   8 ++
 block/genhd.c             |   4 +
 block/partitions/core.c   |   5 ++
 include/linux/blk_types.h |   4 +
 7 files changed, 230 insertions(+)

diff --git a/block/Kconfig b/block/Kconfig
index 70e4a66d941ff66ecb0ec34f4f7eff7fd1e4be40..4899ad572c71ffdbb62460d57623216254893ddc 100644
--- a/block/Kconfig
+++ b/block/Kconfig
@@ -209,6 +209,17 @@ config BLK_INLINE_ENCRYPTION_FALLBACK
 	  by falling back to the kernel crypto API when inline
 	  encryption hardware is not present.
 
+config BLK_NVMEM
+	bool "Block device NVMEM provider"
+	depends on OF
+	depends on NVMEM
+	help
+	  Allow block devices (or partitions) to act as NVMEM providers,
+	  exposing factory-provisioned data such as MAC addresses or Wi-Fi
+	  calibration blobs to the drivers that consume them. This is
+	  typically used on embedded devices where such data is stored in a
+	  dedicated area of an eMMC, instead of a separate EEPROM or OTP.
+
 source "block/partitions/Kconfig"
 
 config BLK_PM
diff --git a/block/Makefile b/block/Makefile
index e7bd320e3d6971a8abf584f5de42776bb54e8216..8200297fbcbab304beb4239d0c33da07011c3ed9 100644
--- a/block/Makefile
+++ b/block/Makefile
@@ -39,3 +39,4 @@ obj-$(CONFIG_BLK_INLINE_ENCRYPTION)	+= blk-crypto.o blk-crypto-profile.o \
 					   blk-crypto-sysfs.o
 obj-$(CONFIG_BLK_INLINE_ENCRYPTION_FALLBACK)	+= blk-crypto-fallback.o
 obj-$(CONFIG_BLOCK_HOLDER_DEPRECATED)	+= holder.o
+obj-$(CONFIG_BLK_NVMEM)                += blk-nvmem.o
diff --git a/block/blk-nvmem.c b/block/blk-nvmem.c
new file mode 100644
index 0000000000000000000000000000000000000000..628681f6b747b865100bcaec18ea650b08c6972f
--- /dev/null
+++ b/block/blk-nvmem.c
@@ -0,0 +1,197 @@
+// SPDX-License-Identifier: GPL-2.0-or-later
+/*
+ * block device NVMEM provider
+ *
+ * Copyright (c) 2024 Daniel Golle <daniel@makrotopia.org>
+ * Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
+ *
+ * Useful on devices using a whole disk or a partition (e.g. an eMMC boot
+ * partition) to store MAC addresses, Bluetooth addresses or Wi-Fi
+ * calibration EEPROM data.
+ *
+ * The NVMEM device is a side channel onto a block device that stays fully
+ * usable. This is somewhat mitigated by opening the device exclusively.
+ */
+
+#include <linux/device.h>
+#include <linux/file.h>
+#include <linux/fs.h>
+#include <linux/nvmem-provider.h>
+#include <linux/nvmem-consumer.h>
+#include <linux/of.h>
+#include <linux/property.h>
+#include <linux/slab.h>
+#include <linux/workqueue.h>
+
+#include "blk.h"
+
+/**
+ * struct blk_nvmem - NVMEM registration state of a block device
+ * @bdev: block device backing the NVMEM device
+ * @nvmem: registered NVMEM device, only accessed from the work items
+ * @size: size of @bdev in bytes, sampled when the registration is queued
+ * @add_work: work item registering @nvmem
+ * @del_work: work item unregistering @nvmem and freeing this structure
+ */
+struct blk_nvmem {
+	struct block_device	*bdev;
+	struct nvmem_device	*nvmem;
+	loff_t			size;
+	struct work_struct	add_work;
+	struct work_struct	del_work;
+};
+
+/*
+ * The queue must stay ordered: it is what guarantees that the removal of a
+ * block device completes before the registration of its replacement, which
+ * otherwise would clash on the NVMEM device name, e.g. when re-reading a
+ * partition table.
+ */
+static struct workqueue_struct *blk_nvmem_wq;
+
+static int blk_nvmem_reg_read(void *priv, unsigned int from,
+			      void *val, size_t bytes)
+{
+	struct block_device *bdev = priv;
+	struct file *bdev_file;
+	loff_t pos = from;
+	ssize_t ret;
+
+	/* open and prevent other exclusive openers */
+	bdev_file = bdev_file_open_by_dev(bdev->bd_dev,
+					  BLK_OPEN_READ | BLK_OPEN_EXCL,
+					  blk_nvmem_reg_read, NULL);
+	if (IS_ERR(bdev_file))
+		return PTR_ERR(bdev_file);
+
+	/* the minor may have been recycled since the NVMEM was registered */
+	if (file_bdev(bdev_file) != bdev) {
+		bdev_fput(bdev_file);
+		return -ENODEV;
+	}
+
+	ret = kernel_read(bdev_file, val, bytes, &pos);
+
+	/* yield the claim synchronously, the file release is deferred */
+	bdev_fput(bdev_file);
+
+	if (ret < 0)
+		return ret;
+	if (ret != bytes)
+		return -EIO;
+	return 0;
+}
+
+static void blk_nvmem_add_work(struct work_struct *work)
+{
+	struct blk_nvmem *bn = container_of(work, struct blk_nvmem, add_work);
+	struct block_device *bdev = bn->bdev;
+	struct device *dev = &bdev->bd_device;
+	struct nvmem_config config = {
+		.id		= NVMEM_DEVID_NONE,
+		.owner		= THIS_MODULE,
+		.word_size	= 1,
+		.stride		= 1,
+		.read_only	= true,
+		.root_only	= true,
+		.ignore_wp	= true,
+		.dev		= dev,
+		.name		= dev_name(dev),
+		.of_node	= dev_of_node(dev),
+		.priv		= bdev,
+		.reg_read	= blk_nvmem_reg_read,
+		.size		= bn->size,
+	};
+	struct nvmem_device *nvmem;
+
+	nvmem = nvmem_register(&config);
+	if (IS_ERR(nvmem)) {
+		dev_err_probe(dev, PTR_ERR(nvmem),
+			      "Failed to register NVMEM device\n");
+		return;
+	}
+
+	bn->nvmem = nvmem;
+}
+
+static void blk_nvmem_del_work(struct work_struct *work)
+{
+	struct blk_nvmem *bn = container_of(work, struct blk_nvmem, del_work);
+
+	nvmem_unregister(bn->nvmem);
+	put_device(&bn->bdev->bd_device);
+	kfree(bn);
+}
+
+void blk_nvmem_add(struct block_device *bdev)
+{
+	struct device *dev = &bdev->bd_device;
+	struct device_node *np = dev_of_node(dev);
+	struct blk_nvmem *bn;
+	struct device_node *child;
+	loff_t size;
+
+	/* skip devices which do not have a device tree node */
+	if (!np)
+		return;
+
+	/*
+	 * The layout is described either by an "nvmem-layout" child node or
+	 * by the device node itself being a "fixed-layout" container.
+	 */
+	child = of_get_child_by_name(np, "nvmem-layout");
+	if (child)
+		of_node_put(child);
+	else if (!of_device_is_compatible(np, "fixed-layout"))
+		return;
+
+	/*
+	 * Sample the size here so that the value validated against the
+	 * nvmem_config.size type is the one actually handed to the NVMEM c
```
