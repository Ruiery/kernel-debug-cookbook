---
title: [PATCH v2 16/17] fs: use kiocb_write_iter() in vfs_iocb_iter_write()
list: linux-block
message_id: 20261116-work-fs-frozen_writes-v2-16-ecc4a2aac40e@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-16-ecc4a2aac40e@kernel.org/
---

# [PATCH v2 16/17] fs: use kiocb_write_iter() in vfs_iocb_iter_write()

来源：[https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-16-ecc4a2aac40e@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-16-ecc4a2aac40e@kernel.org/)

```
vfs_iocb_iter_write() open-codes what kiocb_write_iter() does. Use it.
The kiocb is marked with IOCB_WRITE now so the caller can drop freeze
protection with kiocb_end_write_iter().

This also means that an IOCB_NOWAIT write fails with -EAGAIN instead of
waiting for a frozen filesystem. No caller passes IOCB_NOWAIT today.
overlayfs and fuse passthrough don't set FMODE_NOWAIT and cachefiles
and nfsd don't ask for it.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/read_write.c | 7 ++-----
 1 file changed, 2 insertions(+), 5 deletions(-)

diff --git a/fs/read_write.c b/fs/read_write.c
index 6767283108991..eca0aa73e5a4d 100644
--- a/fs/read_write.c
+++ b/fs/read_write.c
@@ -923,7 +923,7 @@ ssize_t vfs_iter_read(struct file *file, struct iov_iter *iter, loff_t *ppos,
 EXPORT_SYMBOL(vfs_iter_read);
 
 /*
- * Caller is responsible for calling kiocb_end_write() on completion
+ * Caller is responsible for calling kiocb_end_write_iter() on completion
  * if async iocb was queued.
  */
 ssize_t vfs_iocb_iter_write(struct file *file, struct kiocb *iocb,
@@ -946,10 +946,7 @@ ssize_t vfs_iocb_iter_write(struct file *file, struct kiocb *iocb,
 	if (ret < 0)
 		return ret;
 
-	kiocb_start_write(iocb);
-	ret = file->f_op->write_iter(iocb, iter);
-	if (ret != -EIOCBQUEUED)
-		kiocb_end_write(iocb);
+	ret = kiocb_write_iter(iocb, iter);
 	if (ret > 0)
 		fsnotify_modify(file);
 

-- 
2.53.0
```
