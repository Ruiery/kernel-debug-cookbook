---
title: [PATCH RFC v2 25/42] pstore: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-25-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-25-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 25/42] pstore: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-25-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-25-98639a2286fb@kernel.org/)

```
Initialize pstore as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. pstore never holds executables or
device nodes.

Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/pstore/inode.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/fs/pstore/inode.c b/fs/pstore/inode.c
index cf499ba727026..4658561cf90b7 100644
--- a/fs/pstore/inode.c
+++ b/fs/pstore/inode.c
@@ -18,6 +18,7 @@
 #include <linux/ramfs.h>
 #include <linux/fs_parser.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/sched.h>
 #include <linux/magic.h>
 #include <linux/pstore.h>
@@ -491,6 +492,7 @@ static int pstore_init_fs_context(struct fs_context *fc)
 	ctx->kmsg_bytes = kmsg_bytes;
 
 	fc->fs_private = ctx;
+	fc_init_pseudo(fc);
 	fc->ops = &pstore_context_ops;
 
 	return 0;

-- 
2.53.0
```
