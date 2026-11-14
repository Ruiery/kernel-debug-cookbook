---
title: [PATCH RFC v2 04/42] fs: add SB_I_PSEUDO
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-4-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-4-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 04/42] fs: add SB_I_PSEUDO

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-4-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-4-98639a2286fb@kernel.org/)

```
Currently, there's no way to tell whether the files of a filesystem
store data or whether they are kernel interfaces. Files on pseudo
filesystems such as procfs or sysfs generate their contents when they're
read and writes to them are commands to the kernel.

But a few places in the kernel take an arbitrary file and use it as
storage: loop, zloop, the nvme target's file backend, the scsi target's
fileio backend, fuse passthrough, the usb mass storage gadget and erofs
file-backed mounts. At most they check the file type and whether the
file implements ->read_iter() and ->write_iter(). That's not enough.
kernfs provides both for every sysfs attribute for example.

Add SB_I_PSEUDO so a filesystem can state that its regular files are
kernel interfaces and must not be used as storage.

Pseudo filesystems also never hold executables or device nodes. But
currently each of them decides on its own whether to raise SB_I_NOEXEC
and SB_I_NODEV. Some do, most don't. Add fc_init_pseudo() as the common
initialization point for all pseudo filesystems that raises all three
flags and switch init_pseudo() over to it. The following patches
convert the mountable pseudo filesystems.

Nothing checks SB_I_PSEUDO yet so no functional changes.

Reviewed-by: Jan Kara <jack@suse.cz>
Reviewed-by: Christoph Hellwig <hch@lst.de>
Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/libfs.c                     |  2 +-
 include/linux/fs/super_types.h |  1 +
 include/linux/pseudo_fs.h      | 11 +++++++++++
 3 files changed, 13 insertions(+), 1 deletion(-)

diff --git a/fs/libfs.c b/fs/libfs.c
index 96a6e9b1535fb..8c8789489fdf9 100644
--- a/fs/libfs.c
+++ b/fs/libfs.c
@@ -735,7 +735,7 @@ struct pseudo_fs_context *init_pseudo(struct fs_context *fc,
 		fc->fs_private = ctx;
 		fc->ops = &pseudo_fs_context_ops;
 		fc->sb_flags |= SB_NOUSER;
-		fc->s_iflags |= SB_I_NOEXEC | SB_I_NODEV;
+		fc_init_pseudo(fc);
 		fc->global = true;
 	}
 	return ctx;
diff --git a/include/linux/fs/super_types.h b/include/linux/fs/super_types.h
index 72f4288e16c52..472200bdf081a 100644
--- a/include/linux/fs/super_types.h
+++ b/include/linux/fs/super_types.h
@@ -359,5 +359,6 @@ struct super_block {
 #define SB_I_NOIDMAP	0x00002000	/* No idmapped mounts on this superblock */
 #define SB_I_ALLOW_HSM	0x00004000	/* Allow HSM events on this superblock */
 #define SB_I_NO_DATA_INTEGRITY	0x00008000 /* fs cannot guarantee data persistence on sync */
+#define SB_I_PSEUDO	0x00010000	/* regular files are kernel interfaces, not storage */
 
 #endif /* _LINUX_FS_SUPER_TYPES_H */
diff --git a/include/linux/pseudo_fs.h b/include/linux/pseudo_fs.h
index a651e60d94107..0ca408aa60aff 100644
--- a/include/linux/pseudo_fs.h
+++ b/include/linux/pseudo_fs.h
@@ -2,6 +2,7 @@
 #define __LINUX_PSEUDO_FS__
 
 #include <linux/fs_context.h>
+#include <linux/fs/super_types.h>
 
 struct pseudo_fs_context {
 	const struct super_operations *ops;
@@ -15,4 +16,14 @@ struct pseudo_fs_context {
 struct pseudo_fs_context *init_pseudo(struct fs_context *fc,
 				      unsigned long magic);
 
+/*
+ * Common initialization for all pseudo filesystems, mountable or not. Their
+ * regular files are kernel interfaces. They don't store data and pseudo
+ * filesystems never hold executables or device nodes.
+ */
+static inline void fc_init_pseudo(struct fs_context *fc)
+{
+	fc->s_iflags |= SB_I_PSEUDO | SB_I_NOEXEC | SB_I_NODEV;
+}
+
 #endif

-- 
2.53.0
```
