---
title: [PATCH RFC v2 16/42] configfs: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-16-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-16-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 16/42] configfs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-16-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-16-98639a2286fb@kernel.org/)

```
Initialize configfs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. configfs never holds executables or
device nodes.

Reviewed-by: Jan Kara <jack@suse.cz>
Acked-by: Breno Leitao <leitao@debian.org>
Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/configfs/mount.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/fs/configfs/mount.c b/fs/configfs/mount.c
index d8cac1cbf3bd5..60ba24e7ae2b9 100644
--- a/fs/configfs/mount.c
+++ b/fs/configfs/mount.c
@@ -13,6 +13,7 @@
 #include <linux/module.h>
 #include <linux/mount.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/pagemap.h>
 #include <linux/init.h>
 #include <linux/slab.h>
@@ -106,6 +107,7 @@ static const struct fs_context_operations configfs_context_ops = {
 
 static int configfs_init_fs_context(struct fs_context *fc)
 {
+	fc_init_pseudo(fc);
 	fc->ops = &configfs_context_ops;
 	return 0;
 }

-- 
2.53.0
```
