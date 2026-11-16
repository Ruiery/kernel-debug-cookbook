---
title: [PATCH RFC v3 22/44] sunrpc: use fc_init_pseudo() for rpc_pipefs
list: linux-block
message_id: 20261116-work-loop-pseudo-v3-22-8cbbea1cf34f@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-22-8cbbea1cf34f@kernel.org/
---

# [PATCH RFC v3 22/44] sunrpc: use fc_init_pseudo() for rpc_pipefs

来源：[https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-22-8cbbea1cf34f@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-22-8cbbea1cf34f@kernel.org/)

```
Initialize rpc_pipefs as a pseudo filesystem. This raises SB_I_PSEUDO and
also SB_I_NOEXEC and SB_I_NODEV. rpc_pipefs never holds executables or
device nodes.

Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Reviewed-by: Chris Down <chris@chrisdown.name>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 net/sunrpc/rpc_pipe.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/net/sunrpc/rpc_pipe.c b/net/sunrpc/rpc_pipe.c
index 9d349cfbc4831..37277a6d24156 100644
--- a/net/sunrpc/rpc_pipe.c
+++ b/net/sunrpc/rpc_pipe.c
@@ -15,6 +15,7 @@
 #include <linux/pagemap.h>
 #include <linux/mount.h>
 #include <linux/fs_context.h>
+#include <linux/pseudo_fs.h>
 #include <linux/namei.h>
 #include <linux/fsnotify.h>
 #include <linux/kernel.h>
@@ -1181,6 +1182,7 @@ static int rpc_init_fs_context(struct fs_context *fc)
 {
 	put_user_ns(fc->user_ns);
 	fc->user_ns = get_user_ns(fc->net_ns->user_ns);
+	fc_init_pseudo(fc);
 	fc->ops = &rpc_fs_context_ops;
 	return 0;
 }

-- 
2.53.0
```
