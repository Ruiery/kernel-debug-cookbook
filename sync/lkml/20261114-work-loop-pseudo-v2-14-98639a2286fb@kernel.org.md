---
title: [PATCH RFC v2 14/42] debugfs: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-14-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-14-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 14/42] debugfs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-14-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-14-98639a2286fb@kernel.org/)

```
Initialize debugfs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. debugfs never holds executables or
device nodes.

SB_I_NOEXEC also refuses PROT_EXEC mappings. The debugfs files that
can be mapped, kcov, relay channels and powernv's memtrace, map data.

Reviewed-by: Jan Kara <jack@suse.cz>
Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/debugfs/inode.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/fs/debugfs/inode.c b/fs/debugfs/inode.c
index b4915551ad315..f163f0bc5703a 100644
--- a/fs/debugfs/inode.c
+++ b/fs/debugfs/inode.c
@@ -15,6 +15,7 @@
 #include <linux/module.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/fs_parser.h>
 #include <linux/pagemap.h>
 #include <linux/init.h>
@@ -317,6 +318,7 @@ static int debugfs_init_fs_context(struct fs_context *fc)
 	fsi->mode = DEBUGFS_DEFAULT_MODE;
 
 	fc->s_fs_info = fsi;
+	fc_init_pseudo(fc);
 	fc->ops = &debugfs_context_ops;
 	return 0;
 }

-- 
2.53.0
```
