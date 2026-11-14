---
title: [PATCH RFC v2 17/42] securityfs: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-17-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-17-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 17/42] securityfs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-17-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-17-98639a2286fb@kernel.org/)

```
Initialize securityfs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. securityfs never holds executables or
device nodes.

AppArmor puts a .null device node into securityfs but only ever opens
it via dentry_open() which doesn't care about SB_I_NODEV.

Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 security/inode.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/security/inode.c b/security/inode.c
index 0804023676741..93997a9f16fcb 100644
--- a/security/inode.c
+++ b/security/inode.c
@@ -14,6 +14,7 @@
 #include <linux/kobject.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/mount.h>
 #include <linux/pagemap.h>
 #include <linux/init.h>
@@ -64,6 +65,7 @@ static const struct fs_context_operations securityfs_context_ops = {
 
 static int securityfs_init_fs_context(struct fs_context *fc)
 {
+	fc_init_pseudo(fc);
 	fc->ops = &securityfs_context_ops;
 	return 0;
 }

-- 
2.53.0
```
