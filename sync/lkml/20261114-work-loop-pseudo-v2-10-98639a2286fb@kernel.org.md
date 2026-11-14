---
title: [PATCH RFC v2 10/42] nullfs: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-10-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-10-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 10/42] nullfs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-10-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-10-98639a2286fb@kernel.org/)

```
Initialize nullfs as a pseudo filesystem instead of raising
SB_I_NOEXEC and SB_I_NODEV by hand. This adds SB_I_PSEUDO.

Reviewed-by: Jan Kara <jack@suse.cz>
Reviewed-by: Christoph Hellwig <hch@lst.de>
Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/nullfs.c | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

diff --git a/fs/nullfs.c b/fs/nullfs.c
index 319c2f5c5a671..2fe24cb97160e 100644
--- a/fs/nullfs.c
+++ b/fs/nullfs.c
@@ -2,6 +2,7 @@
 /* Copyright (c) 2026 Christian Brauner <brauner@kernel.org> */
 #include <linux/fs/super_types.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/magic.h>
 #include <linux/splice.h>
 #include <linux/uio.h>
@@ -174,7 +175,7 @@ static int nullfs_init_fs_context(struct fs_context *fc)
 {
 	fc->ops		= &nullfs_fs_context_ops;
 	fc->sb_flags	|= SB_NOUSER;
-	fc->s_iflags	|= SB_I_NOEXEC | SB_I_NODEV;
+	fc_init_pseudo(fc);
 	return 0;
 }
 

-- 
2.53.0
```
