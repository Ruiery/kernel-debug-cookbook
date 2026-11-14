---
title: [PATCH RFC v2 13/42] devpts: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-13-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-13-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 13/42] devpts: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-13-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-13-98639a2286fb@kernel.org/)

```
Initialize devpts as a pseudo filesystem. This raises SB_I_PSEUDO and
SB_I_NOEXEC. devpts never holds executables. devpts_fill_super() keeps
clearing SB_I_NODEV for the pty device nodes.

Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/devpts/inode.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/fs/devpts/inode.c b/fs/devpts/inode.c
index bd1e8eb26edb7..47ef12241d92d 100644
--- a/fs/devpts/inode.c
+++ b/fs/devpts/inode.c
@@ -13,6 +13,7 @@
 #include <linux/init.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/fs_parser.h>
 #include <linux/sched.h>
 #include <linux/namei.h>
@@ -438,6 +439,7 @@ static int devpts_init_fs_context(struct fs_context *fc)
 		fsi->mount_opts.reserve = true;
 
 	fc->s_fs_info = fsi;
+	fc_init_pseudo(fc);
 	fc->ops = &devpts_context_ops;
 	return 0;
 }

-- 
2.53.0
```
