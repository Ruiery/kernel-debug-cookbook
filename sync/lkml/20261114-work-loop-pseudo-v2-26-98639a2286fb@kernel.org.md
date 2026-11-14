---
title: [PATCH RFC v2 26/42] xenfs: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-26-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-26-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 26/42] xenfs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-26-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-26-98639a2286fb@kernel.org/)

```
Initialize xenfs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. xenfs never holds executables or
device nodes.

SB_I_NOEXEC also refuses PROT_EXEC mappings. xenfs maps the xenstore
page and guest memory through privcmd, both data.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/xen/xenfs/super.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/drivers/xen/xenfs/super.c b/drivers/xen/xenfs/super.c
index 37ea7c5c03469..aba7d038ed735 100644
--- a/drivers/xen/xenfs/super.c
+++ b/drivers/xen/xenfs/super.c
@@ -15,6 +15,7 @@
 #include <linux/module.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/magic.h>
 
 #include <xen/xen.h>
@@ -80,6 +81,7 @@ static const struct fs_context_operations xenfs_context_ops = {
 
 static int xenfs_init_fs_context(struct fs_context *fc)
 {
+	fc_init_pseudo(fc);
 	fc->ops = &xenfs_context_ops;
 	return 0;
 }

-- 
2.53.0
```
