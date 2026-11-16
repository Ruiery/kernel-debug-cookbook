---
title: [PATCH RFC v3 40/44] fuse: refuse files on pseudo filesystems as passthrough backing files
list: linux-block
message_id: 20261116-work-loop-pseudo-v3-40-8cbbea1cf34f@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-40-8cbbea1cf34f@kernel.org/
---

# [PATCH RFC v3 40/44] fuse: refuse files on pseudo filesystems as passthrough backing files

来源：[https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-40-8cbbea1cf34f@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-40-8cbbea1cf34f@kernel.org/)

```
The fuse server can register any regular file as a backing file. procfs
and binfmt_misc files are already refused by the stacking depth check as
both set s_stack_depth to FILESYSTEM_MAX_STACK_DEPTH. sysfs and the
other pseudo filesystems aren't. Reads and writes of the fuse file would
then be done on the pseudo file with the fuse server's credentials.
Refuse files on pseudo filesystems just like loop does.

Note that the backing file is only registered here and opened again for
every fuse file that uses it. Only its path is used and O_PATH file
descriptors are allowed since commit efad7153bf93 ("fuse: allow O_PATH
fd for FUSE_DEV_IOC_BACKING_OPEN"). So pass FMODE_PATH to
file_check_backing() to keep them working.

The file that reads and writes are actually done on is opened in
fuse_passthrough_open() with the flags of the fuse file. So check that
file as well and pass the mode the fuse file was opened with. It has
the same path as the registered file so files on pseudo filesystems are
already refused. But this also makes sure that the backing file
implements ->read_iter() if the fuse file is opened for reading and
->write_iter() if it is opened for writing. Like the other failures to
set up passthrough this fails the open with EIO.

Reviewed-by: Amir Goldstein <amir73il@gmail.com>
Suggested-by: Amir Goldstein <amir73il@gmail.com>
Link: https://lore.kernel.org/all/CAOQ4uxhGxpBtMZ5kfuzR1tQAewiecoX7UjXQRo91QjJHH9T_Yw@mail.gmail.com
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/fuse/backing.c     | 4 ++++
 fs/fuse/passthrough.c | 7 +++++++
 2 files changed, 11 insertions(+)

diff --git a/fs/fuse/backing.c b/fs/fuse/backing.c
index 8c21a8a74efb9..7527f3ecb90dc 100644
--- a/fs/fuse/backing.c
+++ b/fs/fuse/backing.c
@@ -147,6 +147,10 @@ static int fuse_backing_open_file(struct fuse_conn *fc, struct fuse_backing *fb,
 		if (inode->i_sb->s_stack_depth >= fc->max_stack_depth)
 			return -ELOOP;
 
+		err = file_check_backing(file, FMODE_PATH, 0);
+		if (err)
+			return err;
+
 		fb->type = FUSE_BACKING_PATH;
 		fb->path = file->f_path;
 		path_get(&fb->path);
diff --git a/fs/fuse/passthrough.c b/fs/fuse/passthrough.c
index 0ed964c479d96..fc8979ac96a21 100644
--- a/fs/fuse/passthrough.c
+++ b/fs/fuse/passthrough.c
@@ -183,6 +183,7 @@ int fuse_passthrough_open(struct file *file, struct fuse_backing *fb)
 {
 	struct fuse_file *ff = file->private_data;
 	struct file *backing_file;
+	int err;
 
 	if (fb->type == FUSE_BACKING_EXTMAP) {
 		if (fuse_backing_is_dax(fb) != !!IS_DAX(file_inode(file)))
@@ -201,6 +202,12 @@ int fuse_passthrough_open(struct file *file, struct fuse_backing *fb)
 	if (IS_ERR(backing_file))
 		return fuse_EIO("failed to open backing file (%ld)", PTR_ERR(backing_file));
 
+	err = file_check_backing(backing_file, file->f_mode & (FMODE_READ | FMODE_WRITE), 0);
+	if (err) {
+		fput(backing_file);
+		return fuse_EIO("invalid backing file (%d)", err);
+	}
+
 	ff->passthrough = backing_file;
 	ff->cred = get_cred(fb->cred);
 

-- 
2.53.0
```
