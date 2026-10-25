---
title: [PATCH v2 3/7] init: factor out root device lookup into lookup_root_device()
list: linux-block
message_id: 20261025-discoverable-root_partitions-v2-3-fb77d0821fab@kernel.org
link: https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-3-fb77d0821fab@kernel.org/
---

# [PATCH v2 3/7] init: factor out root device lookup into lookup_root_device()

来源：[https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-3-fb77d0821fab@kernel.org/](https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-3-fb77d0821fab@kernel.org/)

```
DPS root detection will also need to work if root_wait is set, meaning
that wait_for_root() needs to handle the DPS logic.

Move the early_lookup_bdev() calls and the rootwait error handling into
the new lookup_root_device() so later changes can extend the lookup
policy without duplicating the rootwait retry logic.

While at it, reword the error message to add the "VFS: " prefix.

Signed-off-by: Vincent Mailhol <mailhol@kernel.org>
---
 init/do_mounts.c | 23 +++++++++++++++--------
 1 file changed, 15 insertions(+), 8 deletions(-)

diff --git a/init/do_mounts.c b/init/do_mounts.c
index 95e0b3a0f711..b9814d0cc5a6 100644
--- a/init/do_mounts.c
+++ b/init/do_mounts.c
@@ -402,6 +402,18 @@ void __init mount_root(char *root_device_name)
 	}
 }
 
+static int __init lookup_root_device(const char *root_device_name, dev_t *dev)
+{
+	int err;
+
+	err = early_lookup_bdev(root_device_name, dev);
+	if (err == -EINVAL && root_wait) {
+		pr_err("VFS: root= is invalid; disabling rootwait.\n");
+		root_wait = 0;
+	}
+	return err;
+}
+
 /* wait for any asynchronous scanning to complete */
 static void __init wait_for_root(char *root_device_name)
 {
@@ -415,7 +427,7 @@ static void __init wait_for_root(char *root_device_name)
 	end = ktime_add_ms(ktime_get_raw(), root_wait);
 
 	while (!driver_probe_done() ||
-	       early_lookup_bdev(root_device_name, &ROOT_DEV) < 0) {
+	       lookup_root_device(root_device_name, &ROOT_DEV) < 0) {
 		msleep(5);
 		if (root_wait > 0 && ktime_after(ktime_get_raw(), end))
 			break;
@@ -440,14 +452,9 @@ static dev_t __init parse_root_device(char *root_device_name)
 	if (strcmp(root_device_name, "/dev/ram") == 0)
 		return Root_RAM0;
 
-	error = early_lookup_bdev(root_device_name, &dev);
-	if (error) {
-		if (error == -EINVAL && root_wait) {
-			pr_err("Disabling rootwait; root= is invalid.\n");
-			root_wait = 0;
-		}
+	error = lookup_root_device(root_device_name, &dev);
+	if (error)
 		return 0;
-	}
 	return dev;
 }
 

-- 
2.55.0
```
