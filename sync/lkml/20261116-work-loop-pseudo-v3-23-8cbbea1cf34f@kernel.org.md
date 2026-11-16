---
title: [PATCH RFC v3 23/44] fuse: use fc_init_pseudo() for fusectl
list: linux-block
message_id: 20261116-work-loop-pseudo-v3-23-8cbbea1cf34f@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-23-8cbbea1cf34f@kernel.org/
---

# [PATCH RFC v3 23/44] fuse: use fc_init_pseudo() for fusectl

来源：[https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-23-8cbbea1cf34f@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-23-8cbbea1cf34f@kernel.org/)

```
Initialize fusectl as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. fusectl never holds executables or
device nodes.

Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Reviewed-by: Chris Down <chris@chrisdown.name>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/fuse/control.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/fs/fuse/control.c b/fs/fuse/control.c
index 21ffde596d611..4497362e7df06 100644
--- a/fs/fuse/control.c
+++ b/fs/fuse/control.c
@@ -10,6 +10,7 @@
 #include <linux/init.h>
 #include <linux/module.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/namei.h>
 
 #define FUSE_CTL_SUPER_MAGIC 0x65735543
@@ -334,6 +335,7 @@ static const struct fs_context_operations fuse_ctl_context_ops = {
 
 static int fuse_ctl_init_fs_context(struct fs_context *fsc)
 {
+	fc_init_pseudo(fsc);
 	fsc->ops = &fuse_ctl_context_ops;
 	return 0;
 }

-- 
2.53.0
```
