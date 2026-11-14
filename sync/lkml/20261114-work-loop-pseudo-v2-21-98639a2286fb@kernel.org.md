---
title: [PATCH RFC v2 21/42] nfsd: use fc_init_pseudo()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-21-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-21-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 21/42] nfsd: use fc_init_pseudo()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-21-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-21-98639a2286fb@kernel.org/)

```
Initialize the nfsd filesystem as a pseudo filesystem. This raises
SB_I_PSEUDO and also SB_I_NOEXEC and SB_I_NODEV. It never holds
executables or device nodes.

Acked-by: Chuck Lever <cel@kernel.org>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/nfsd/nfsctl.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/fs/nfsd/nfsctl.c b/fs/nfsd/nfsctl.c
index f32311f2d7cf9..ce2666deddbd9 100644
--- a/fs/nfsd/nfsctl.c
+++ b/fs/nfsd/nfsctl.c
@@ -9,6 +9,7 @@
 #include <linux/namei.h>
 #include <linux/ctype.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 
 #include <linux/sunrpc/cache.h>
 #include <linux/sunrpc/svcsock.h>
@@ -1375,6 +1376,7 @@ static int nfsd_init_fs_context(struct fs_context *fc)
 {
 	put_user_ns(fc->user_ns);
 	fc->user_ns = get_user_ns(fc->net_ns->user_ns);
+	fc_init_pseudo(fc);
 	fc->ops = &nfsd_fs_context_ops;
 	return 0;
 }

-- 
2.53.0
```
