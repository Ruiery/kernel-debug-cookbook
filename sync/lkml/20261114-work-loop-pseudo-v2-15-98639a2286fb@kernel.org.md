---
title: [PATCH RFC v2 15/42] tracefs: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-15-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-15-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 15/42] tracefs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-15-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-15-98639a2286fb@kernel.org/)

```
Initialize tracefs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. tracefs never holds executables or
device nodes.

SB_I_NOEXEC also refuses PROT_EXEC mappings. The only tracefs files
that can be mapped are the ring buffers and __rb_map_vma() refuses
VM_EXEC already.

Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/tracefs/inode.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/fs/tracefs/inode.c b/fs/tracefs/inode.c
index 5020365ca7048..e04febd868eb4 100644
--- a/fs/tracefs/inode.c
+++ b/fs/tracefs/inode.c
@@ -12,6 +12,7 @@
 #include <linux/module.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/fs_parser.h>
 #include <linux/kobject.h>
 #include <linux/namei.h>
@@ -510,6 +511,7 @@ static int tracefs_init_fs_context(struct fs_context *fc)
 	fsi->mode = TRACEFS_DEFAULT_MODE;
 
 	fc->s_fs_info = fsi;
+	fc_init_pseudo(fc);
 	fc->ops = &tracefs_context_ops;
 	return 0;
 }

-- 
2.53.0
```
