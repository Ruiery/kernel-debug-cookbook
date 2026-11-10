---
title: [PATCH RFC 24/41] efivarfs: use fc_init_pseudo()
list: linux-block
message_id: 20261110-work-loop-pseudo-v1-24-4c998976c6c7@kernel.org
link: https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-24-4c998976c6c7@kernel.org/
---

# [PATCH RFC 24/41] efivarfs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-24-4c998976c6c7@kernel.org/](https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-24-4c998976c6c7@kernel.org/)

```
Initialize efivarfs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. efivarfs never holds executables or
device nodes.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/efivarfs/super.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/fs/efivarfs/super.c b/fs/efivarfs/super.c
index 12746ced6dc6..e598d42c5f42 100644
--- a/fs/efivarfs/super.c
+++ b/fs/efivarfs/super.c
@@ -8,6 +8,7 @@
 #include <linux/efi.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/fs_parser.h>
 #include <linux/module.h>
 #include <linux/pagemap.h>
@@ -554,6 +555,7 @@ static int efivarfs_init_fs_context(struct fs_context *fc)
 	}
 
 	fc->s_fs_info = sfi;
+	fc_init_pseudo(fc);
 	fc->ops = &efivarfs_context_ops;
 
 	return 0;

-- 
2.53.0
```
