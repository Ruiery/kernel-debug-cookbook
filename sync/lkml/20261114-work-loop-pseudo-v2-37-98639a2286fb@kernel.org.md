---
title: [PATCH RFC v2 37/42] target: fileio: refuse files on pseudo filesystems as backing files
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-37-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-37-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 37/42] target: fileio: refuse files on pseudo filesystems as backing files

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-37-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-37-98639a2286fb@kernel.org/)

```
fd_dev_name can name any file including files on procfs or sysfs. The
initiator then gets to read and write kernel interfaces through the LUN
with kernel credentials. Refuse files on pseudo filesystems just like
loop does by switching to file_check_backing().

Do the same for the protection file. With DIF protection enabled the
fileio backend keeps the protection information in a second file. It is
named like the backing file with ".protection" appended and
fd_init_prot() opens it by path. Whatever that path leads to was taken
without any checks.

Note that the helper only accepts regular files and block devices as
backing file and only regular files as protection file. So far the
backing file could be anything with ->read_iter() and ->write_iter()
including character devices and FIFOs.

Reported-by: Sashiko <sashiko-bot@kernel.org>
Closes: https://lore.kernel.org/all/sashiko-outbox-206765@kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/target/target_core_file.c | 10 ++++++++--
 1 file changed, 8 insertions(+), 2 deletions(-)

diff --git a/drivers/target/target_core_file.c b/drivers/target/target_core_file.c
index a5391e57e9aa5..c747cc4a647ff 100644
--- a/drivers/target/target_core_file.c
+++ b/drivers/target/target_core_file.c
@@ -145,8 +145,8 @@ static int fd_configure_device(struct se_device *dev)
 	}
 	fd_dev->fd_file = file;
 
-	if (!file->f_op->read_iter || !file->f_op->write_iter) {
-		pr_err("FILEIO: %s lacks ->read_iter or ->write_iter\n",
+	if (file_check_backing(file, FMODE_READ | FMODE_WRITE, S_IFBLK)) {
+		pr_err("FILEIO: %s can't be used as a backing file\n",
 		       fd_dev->fd_dev_name);
 		ret = -EINVAL;
 		goto fail;
@@ -861,6 +861,12 @@ static int fd_init_prot(struct se_device *dev)
 		ret = PTR_ERR(prot_file);
 		return ret;
 	}
+
+	if (file_check_backing(prot_file, FMODE_READ | FMODE_WRITE, 0)) {
+		pr_err("FILEIO: %s can't be used as a protection file\n", buf);
+		filp_close(prot_file, NULL);
+		return -EINVAL;
+	}
 	fd_dev->fd_prot_file = prot_file;
 
 	return 0;

-- 
2.53.0
```
