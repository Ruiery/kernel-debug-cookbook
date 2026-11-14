---
title: [PATCH RFC v2 29/42] s390/hypfs: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-29-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-29-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 29/42] s390/hypfs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-29-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-29-98639a2286fb@kernel.org/)

```
Initialize hypfs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. hypfs never holds executables or
device nodes.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 arch/s390/hypfs/inode.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/arch/s390/hypfs/inode.c b/arch/s390/hypfs/inode.c
index 559b011e68800..8662169de477a 100644
--- a/arch/s390/hypfs/inode.c
+++ b/arch/s390/hypfs/inode.c
@@ -12,6 +12,7 @@
 #include <linux/errno.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/fs_parser.h>
 #include <linux/namei.h>
 #include <linux/vfs.h>
@@ -301,6 +302,7 @@ static int hypfs_init_fs_context(struct fs_context *fc)
 	sbi->gid = current_gid();
 
 	fc->s_fs_info = sbi;
+	fc_init_pseudo(fc);
 	fc->ops = &hypfs_context_ops;
 	return 0;
 }

-- 
2.53.0
```
