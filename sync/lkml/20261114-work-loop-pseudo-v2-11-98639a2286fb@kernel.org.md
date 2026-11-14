---
title: [PATCH RFC v2 11/42] failfs: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-11-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-11-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 11/42] failfs: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-11-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-11-98639a2286fb@kernel.org/)

```
Initialize failfs as a pseudo filesystem instead of raising
SB_I_NOEXEC and SB_I_NODEV by hand. This adds SB_I_PSEUDO.

Reviewed-by: Jan Kara <jack@suse.cz>
Reviewed-by: Christoph Hellwig <hch@lst.de>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/failfs.c | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

diff --git a/fs/failfs.c b/fs/failfs.c
index 437cdc981c2de..f03334f361c0e 100644
--- a/fs/failfs.c
+++ b/fs/failfs.c
@@ -3,6 +3,7 @@
 #include <linux/fs.h>
 #include <linux/fs/super_types.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/fs_struct.h>
 #include <linux/magic.h>
 #include <linux/mount.h>
@@ -132,7 +133,7 @@ static int failfs_init_fs_context(struct fs_context *fc)
 	fc->ops		= &failfs_context_ops;
 	fc->global	= true;
 	fc->sb_flags	|= SB_NOUSER;
-	fc->s_iflags	|= SB_I_NOEXEC | SB_I_NODEV;
+	fc_init_pseudo(fc);
 	return 0;
 }
 

-- 
2.53.0
```
