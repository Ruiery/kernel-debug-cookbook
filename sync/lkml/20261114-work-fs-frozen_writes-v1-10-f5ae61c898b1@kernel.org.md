---
title: [PATCH 10/12] ovl: take freeze protection when storing the uuid
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-10-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-10-f5ae61c898b1@kernel.org/
---

# [PATCH 10/12] ovl: take freeze protection when storing the uuid

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-10-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-10-f5ae61c898b1@kernel.org/)

```
ovl_init_uuid_xattr() stores the persistent uuid in an xattr on the
upper root. That happens after ovl_make_workdir() dropped its write
access to the upper mount and before ovl_get_indexdir() takes it
again. So a freeze of the upper filesystem that lands in between lets
the mount modify a frozen filesystem.

Take write access to the upper mount around the xattr update.

Fixes: d9544c1b0d9e ("ovl: store persistent uuid/fsid with uuid=on")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/overlayfs/util.c | 8 ++++++--
 1 file changed, 6 insertions(+), 2 deletions(-)

diff --git a/fs/overlayfs/util.c b/fs/overlayfs/util.c
index 521717209b2e4..67aa7b71e9c83 100644
--- a/fs/overlayfs/util.c
+++ b/fs/overlayfs/util.c
@@ -829,8 +829,12 @@ bool ovl_init_uuid_xattr(struct super_block *sb, struct ovl_fs *ofs,
 
 	/* Try to store persistent uuid */
 	set = true;
-	res = ovl_setxattr(ofs, upperpath->dentry, OVL_XATTR_UUID, uuid.b,
-			   UUID_SIZE);
+	res = mnt_want_write(ovl_upper_mnt(ofs));
+	if (!res) {
+		res = ovl_setxattr(ofs, upperpath->dentry, OVL_XATTR_UUID,
+				   uuid.b, UUID_SIZE);
+		mnt_drop_write(ovl_upper_mnt(ofs));
+	}
 	if (res)
 		goto fail;
 

-- 
2.53.0
```
