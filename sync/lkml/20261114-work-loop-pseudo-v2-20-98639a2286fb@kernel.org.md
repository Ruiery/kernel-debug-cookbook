---
title: [PATCH RFC v2 20/42] apparmor: use fc_init_pseudo() for apparmorfs
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-20-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-20-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 20/42] apparmor: use fc_init_pseudo() for apparmorfs

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-20-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-20-98639a2286fb@kernel.org/)

```
Initialize apparmorfs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. apparmorfs never holds executables or
device nodes.

Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 security/apparmor/apparmorfs.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/security/apparmor/apparmorfs.c b/security/apparmor/apparmorfs.c
index a993664672173..351ea3a7120e3 100644
--- a/security/apparmor/apparmorfs.c
+++ b/security/apparmor/apparmorfs.c
@@ -21,6 +21,7 @@
 #include <linux/rcupdate.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/poll.h>
 #include <linux/zstd.h>
 #include <linux/string.h>
@@ -263,6 +264,7 @@ static const struct fs_context_operations apparmorfs_context_ops = {
 
 static int apparmorfs_init_fs_context(struct fs_context *fc)
 {
+	fc_init_pseudo(fc);
 	fc->ops = &apparmorfs_context_ops;
 	return 0;
 }

-- 
2.53.0
```
