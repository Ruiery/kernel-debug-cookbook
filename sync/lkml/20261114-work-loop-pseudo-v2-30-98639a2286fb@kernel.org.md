---
title: [PATCH RFC v2 30/42] powerpc/spufs: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-30-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-30-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 30/42] powerpc/spufs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-30-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-30-98639a2286fb@kernel.org/)

```
Initialize spufs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. spufs never holds executables or
device nodes.

SB_I_NOEXEC also refuses PROT_EXEC mappings. The spufs files that can
be mapped expose local store and problem state areas of the SPU,
nothing the PPU executes.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 arch/powerpc/platforms/cell/spufs/inode.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/arch/powerpc/platforms/cell/spufs/inode.c b/arch/powerpc/platforms/cell/spufs/inode.c
index f066d9c7344d3..54b45932aecd2 100644
--- a/arch/powerpc/platforms/cell/spufs/inode.c
+++ b/arch/powerpc/platforms/cell/spufs/inode.c
@@ -11,6 +11,7 @@
 #include <linux/file.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/fs_parser.h>
 #include <linux/fsnotify.h>
 #include <linux/backing-dev.h>
@@ -741,6 +742,7 @@ static int spufs_init_fs_context(struct fs_context *fc)
 
 	fc->fs_private = ctx;
 	fc->s_fs_info = sbi;
+	fc_init_pseudo(fc);
 	fc->ops = &spufs_context_ops;
 	return 0;
 

-- 
2.53.0
```
