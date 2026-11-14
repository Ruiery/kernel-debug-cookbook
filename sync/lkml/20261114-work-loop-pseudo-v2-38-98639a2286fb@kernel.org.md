---
title: [PATCH RFC v2 38/42] fuse: refuse files on pseudo filesystems as passthrough backing files
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-38-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-38-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 38/42] fuse: refuse files on pseudo filesystems as passthrough backing files

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-38-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-38-98639a2286fb@kernel.org/)

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

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/fuse/backing.c | 4 ++++
 1 file changed, 4 insertions(+)

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

-- 
2.53.0
```
