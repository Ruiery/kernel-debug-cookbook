---
title: [PATCH RFC v3 17/44] securityfs: use fc_init_pseudo()
list: linux-block
message_id: 20261116-work-loop-pseudo-v3-17-8cbbea1cf34f@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-17-8cbbea1cf34f@kernel.org/
---

# [PATCH RFC v3 17/44] securityfs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-17-8cbbea1cf34f@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-17-8cbbea1cf34f@kernel.org/)

```
Initialize securityfs as a pseudo filesystem. This raises SB_I_PSEUDO
and SB_I_NOEXEC. securityfs never holds executables.

But securityfs needs device nodes. AppArmor puts a .null device node
into securityfs. On exec it replaces file descriptors the new profile
isn't allowed to use with that node and opens it via dentry_open() which
doesn't care about SB_I_NODEV. Such a file descriptor can still be
reopened through /proc/<pid>/fd/<nr> though and that's what opening
/dev/stderr does. The node itself can also be opened by path as
/sys/kernel/security/apparmor/.null. Both go through may_open_dev()
which refuses device nodes with SB_I_NODEV raised. So clear SB_I_NODEV
again in securityfs_fill_super().

Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Reviewed-by: Chris Down <chris@chrisdown.name>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 security/inode.c | 4 ++++
 1 file changed, 4 insertions(+)

diff --git a/security/inode.c b/security/inode.c
index 0804023676741..edaebf0f1972d 100644
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
@@ -49,6 +50,8 @@ static int securityfs_fill_super(struct super_block *sb, struct fs_context *fc)
 		return error;
 
 	sb->s_op = &securityfs_super_operations;
+	/* Userspace may open AppArmor's .null device node by path. */
+	sb->s_iflags &= ~SB_I_NODEV;
 
 	return 0;
 }
@@ -64,6 +67,7 @@ static const struct fs_context_operations securityfs_context_ops = {
 
 static int securityfs_init_fs_context(struct fs_context *fc)
 {
+	fc_init_pseudo(fc);
 	fc->ops = &securityfs_context_ops;
 	return 0;
 }

-- 
2.53.0
```
