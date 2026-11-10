---
title: [PATCH RFC 33/41] fs: add file_is_pseudo()
list: linux-block
message_id: 20261110-work-loop-pseudo-v1-33-4c998976c6c7@kernel.org
link: https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-33-4c998976c6c7@kernel.org/
---

# [PATCH RFC 33/41] fs: add file_is_pseudo()

来源：[https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-33-4c998976c6c7@kernel.org/](https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-33-4c998976c6c7@kernel.org/)

```
Add a helper to check whether a file is a regular file on a pseudo
filesystem. Only regular files count. Device nodes on pseudo filesystems
such as devpts, binderfs or the block devices on bdevfs are what they
are.

Look at the inode that actually provides the data via d_real_inode().
overlayfs accepts sysfs, cgroup2, debugfs, tracefs, configfs and
securityfs as lower layers and reads of such an overlayfs file are
served by the file on the pseudo filesystem. Checking the overlayfs
inode would miss that.

No functional changes.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 include/linux/fs.h | 12 ++++++++++++
 1 file changed, 12 insertions(+)

diff --git a/include/linux/fs.h b/include/linux/fs.h
index 99caef43ff3c..407ffb6342ec 100644
--- a/include/linux/fs.h
+++ b/include/linux/fs.h
@@ -2553,6 +2553,18 @@ static inline const struct inode *file_user_inode(const struct file *f)
 	return file_inode(f);
 }
 
+/*
+ * Regular files on pseudo filesystems are kernel interfaces and must not be
+ * used as storage. Look through stacking filesystems at the inode that
+ * provides the data.
+ */
+static inline bool file_is_pseudo(const struct file *file)
+{
+	const struct inode *inode = d_real_inode(file->f_path.dentry);
+
+	return S_ISREG(inode->i_mode) && (inode->i_sb->s_iflags & SB_I_PSEUDO);
+}
+
 static inline struct file *file_clone_open(struct file *file)
 {
 	return dentry_open(&file->f_path, file->f_flags, file->f_cred);

-- 
2.53.0
```
