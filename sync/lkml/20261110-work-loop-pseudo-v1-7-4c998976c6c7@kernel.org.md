---
title: [PATCH RFC 07/41] binfmt_misc: use fc_init_pseudo()
list: linux-block
message_id: 20261110-work-loop-pseudo-v1-7-4c998976c6c7@kernel.org
link: https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-7-4c998976c6c7@kernel.org/
---

# [PATCH RFC 07/41] binfmt_misc: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-7-4c998976c6c7@kernel.org/](https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-7-4c998976c6c7@kernel.org/)

```
Initialize binfmt_misc as a pseudo filesystem instead of raising
SB_I_NOEXEC and SB_I_NODEV by hand. This adds SB_I_PSEUDO.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/binfmt_misc.c | 5 +++--
 1 file changed, 3 insertions(+), 2 deletions(-)

diff --git a/fs/binfmt_misc.c b/fs/binfmt_misc.c
index d945b4f6e158..7dc233becd98 100644
--- a/fs/binfmt_misc.c
+++ b/fs/binfmt_misc.c
@@ -22,6 +22,7 @@
 #include <linux/file.h>
 #include <linux/fs.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/init.h>
 #include <linux/kstrtox.h>
 #include <linux/limits.h>
@@ -1575,8 +1576,7 @@ static int bm_fill_super(struct super_block *sb, struct fs_context *fc)
 	if (user_ns != current_user_ns())
 		return -EINVAL;
 
-	/* Never exec off this instance and never let anything stack on it. */
-	sb->s_iflags |= SB_I_NOEXEC | SB_I_NODEV;
+	/* Never let anything stack on this instance. */
 	sb->s_stack_depth = FILESYSTEM_MAX_STACK_DEPTH;
 
 	/*
@@ -1660,6 +1660,7 @@ static void bm_kill_sb(struct super_block *sb)
 
 static int bm_init_fs_context(struct fs_context *fc)
 {
+	fc_init_pseudo(fc);
 	fc->ops = &bm_context_ops;
 	return 0;
 }

-- 
2.53.0
```
