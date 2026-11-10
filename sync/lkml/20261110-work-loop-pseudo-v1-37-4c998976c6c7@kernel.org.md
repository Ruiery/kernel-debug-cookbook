---
title: [PATCH RFC 37/41] target: fileio: refuse files on pseudo filesystems as backing files
list: linux-block
message_id: 20261110-work-loop-pseudo-v1-37-4c998976c6c7@kernel.org
link: https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-37-4c998976c6c7@kernel.org/
---

# [PATCH RFC 37/41] target: fileio: refuse files on pseudo filesystems as backing files

来源：[https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-37-4c998976c6c7@kernel.org/](https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-37-4c998976c6c7@kernel.org/)

```
fd_dev_name can name any file including files on procfs or sysfs. The
initiator then gets to read and write kernel interfaces through the LUN
with kernel credentials. Refuse files on pseudo filesystems just like
loop does.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/target/target_core_file.c | 7 +++++++
 1 file changed, 7 insertions(+)

diff --git a/drivers/target/target_core_file.c b/drivers/target/target_core_file.c
index a5391e57e9aa..7a3cf63dc979 100644
--- a/drivers/target/target_core_file.c
+++ b/drivers/target/target_core_file.c
@@ -152,6 +152,13 @@ static int fd_configure_device(struct se_device *dev)
 		goto fail;
 	}
 
+	if (file_is_pseudo(file)) {
+		pr_err("FILEIO: %s is on a pseudo filesystem\n",
+		       fd_dev->fd_dev_name);
+		ret = -EINVAL;
+		goto fail;
+	}
+
 	/*
 	 * If using a block backend with this struct file, we extract
 	 * fd_dev->fd_[block,dev]_size from struct block_device.

-- 
2.53.0
```
