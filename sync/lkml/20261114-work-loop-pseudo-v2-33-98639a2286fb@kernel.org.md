---
title: [PATCH RFC v2 33/42] fs: add file_check_backing()
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-33-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-33-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 33/42] fs: add file_check_backing()

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-33-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-33-98639a2286fb@kernel.org/)

```
Loop, zloop, the nvme target, the scsi target, fuse passthrough, the usb
mass storage gadget, erofs and acct all take a file from userspace and
use it as storage. Currently, each of them has its own idea of what to
check before using a file like that:

- loop and the gadget check for a regular file or a block device, the
  nvme target, the scsi target and zloop take any file type
- loop checks the open mode, the gadget checks FMODE_CAN_READ, the nvme
  target, the scsi target and zloop only check for ->read_iter() and
  ->write_iter()
- apart from acct which refuses procfs and sysfs files none of them
  cares whether the file is a kernel interface

Add a helper that does all of it in one place. It only accepts regular
files and, if the caller passes S_IFBLK, block devices. It refuses files
on pseudo filesystems. And it checks that the file is open for what the
caller is going to do with it and implements ->read_iter() for reading
and ->write_iter() for writing.

O_PATH files are refused unless the caller passes FMODE_PATH. That is
for callers that only need the path of the file. fuse passthrough is
one of them and has accepted O_PATH file descriptors since commit
efad7153bf93 ("fuse: allow O_PATH fd for FUSE_DEV_IOC_BACKING_OPEN").

Block devices are fine even though bdevfs is a pseudo filesystem. A
block device that userspace hands in is a device node on devtmpfs or
some other filesystem. Files on bdevfs only come from
bdev_file_open_by_*() and never end up here.

The pseudo filesystem check looks at the inode that actually provides
the data via d_real_inode(). overlayfs accepts sysfs, cgroup2, debugfs,
tracefs, configfs and securityfs as lower layers and reads of such an
overlayfs file are served by the file on the pseudo filesystem. Checking
the overlayfs inode would miss that.

Note that the file type is taken from the inode of the file and not from
the host of ->f_mapping like loop and the gadget do it. A driver can
point ->f_mapping somewhere else in ->open(). It makes no difference for
block devices as both inodes are block devices.

No functional changes. Nothing calls the helper yet.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/read_write.c    | 48 ++++++++++++++++++++++++++++++++++++++++++++++++
 include/linux/fs.h |  2 ++
 2 files changed, 50 insertions(+)

diff --git a/fs/read_write.c b/fs/read_write.c
index 6767283108991..cedbe654add65 100644
--- a/fs/read_write.c
+++ b/fs/read_write.c
@@ -866,6 +866,54 @@ static ssize_t do_loop_readv_writev(struct file *filp, struct iov_iter *iter,
 	return ret;
 }
 
+/**
+ * file_check_backing - check that the kernel can use a file as storage
+ * @file: file that userspace handed in
+ * @mode: FMODE_READ and/or FMODE_WRITE the kernel will do I/O with, or
+ *        FMODE_PATH if only the path of @file is used
+ * @type: S_IFBLK if a block device is fine as well, 0 otherwise
+ *
+ * Call this where a file from userspace is taken as a backing file. Only
+ * regular files and, if @type is S_IFBLK, block devices are storage. Files
+ * on pseudo filesystems are kernel interfaces and are refused. The file
+ * must be open for @mode and implement ->read_iter() for reading and
+ * ->write_iter() for writing. O_PATH files are only fine with FMODE_PATH.
+ *
+ * Return: 0 on success, -EBADF if @file isn't open for @mode, -EINVAL if it
+ * can't be used as storage.
+ */
+int file_check_backing(const struct file *file, fmode_t mode, umode_t type)
+{
+	fmode_t io = mode & (FMODE_READ | FMODE_WRITE);
+	/* Drivers may point ->f_mapping at something else. */
+	umode_t fmt = file_inode(file)->i_mode & S_IFMT;
+
+	/* O_PATH files are only fine for callers that just use the path. */
+	if ((file->f_mode & FMODE_PATH) && !(mode & FMODE_PATH))
+		return -EBADF;
+
+	if ((file->f_mode & io) != io)
+		return -EBADF;
+
+	if (fmt != S_IFREG && !(type == S_IFBLK && fmt == S_IFBLK))
+		return -EINVAL;
+
+	/* Look through stacking filesystems at the inode with the data. */
+	if (d_real_inode(file->f_path.dentry)->i_sb->s_iflags & SB_I_PSEUDO)
+		return -EINVAL;
+
+	if ((mode & FMODE_READ) &&
+	    (!(file->f_mode & FMODE_CAN_READ) || !file->f_op->read_iter))
+		return -EINVAL;
+
+	if ((mode & FMODE_WRITE) &&
+	    (!(file->f_mode & FMODE_CAN_WRITE) || !file->f_op->write_iter))
+		return -EINVAL;
+
+	return 0;
+}
+EXPORT_SYMBOL_GPL(file_check_backing);
+
 ssize_t vfs_iocb_iter_read(struct file *file, struct kiocb *iocb,
 			   struct iov_iter *iter)
 {
diff --git a/include/linux/fs.h b/include/linux/fs.h
index 99caef43ff3c4..b1c7ebafbadbe 100644
--- a/include/linux/fs.h
+++ b/include/linux/fs.h
@@ -2553,6 +2553,8 @@ static inline const struct inode *file_user_inode(const struct file *f)
 	return file_inode(f);
 }
 
+int file_check_backing(const struct file *file, fmode_t mode, umode_t type);
+
 static inline struct file *file_clone_open(struct file *file)
 {
 	return dentry_open(&file->f_path, file->f_flags, file->f_cred);

-- 
2.53.0
```
