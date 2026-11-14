---
title: [PATCH RFC v2 28/42] ocfs2: use fc_init_pseudo() for dlmfs
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-28-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-28-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 28/42] ocfs2: use fc_init_pseudo() for dlmfs

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-28-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-28-98639a2286fb@kernel.org/)

```
Initialize dlmfs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. dlmfs never holds executables or
device nodes.

Reviewed-by: Jan Kara <jack@suse.cz>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/ocfs2/dlmfs/dlmfs.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/fs/ocfs2/dlmfs/dlmfs.c b/fs/ocfs2/dlmfs/dlmfs.c
index d3bfcada3e3bf..1789ec96dc130 100644
--- a/fs/ocfs2/dlmfs/dlmfs.c
+++ b/fs/ocfs2/dlmfs/dlmfs.c
@@ -21,6 +21,7 @@
 #include <linux/module.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/pagemap.h>
 #include <linux/types.h>
 #include <linux/slab.h>
@@ -563,6 +564,7 @@ static const struct fs_context_operations dlmfs_context_ops = {
 
 static int dlmfs_init_fs_context(struct fs_context *fc)
 {
+	fc_init_pseudo(fc);
 	fc->ops = &dlmfs_context_ops;
 
 	return 0;

-- 
2.53.0
```
