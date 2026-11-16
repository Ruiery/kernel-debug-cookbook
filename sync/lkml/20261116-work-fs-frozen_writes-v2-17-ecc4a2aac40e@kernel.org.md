---
title: [PATCH v2 17/17] backing-file: use kiocb_end_write_iter()
list: linux-block
message_id: 20261116-work-fs-frozen_writes-v2-17-ecc4a2aac40e@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-17-ecc4a2aac40e@kernel.org/
---

# [PATCH v2 17/17] backing-file: use kiocb_end_write_iter()

来源：[https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-17-ecc4a2aac40e@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-17-ecc4a2aac40e@kernel.org/)

```
vfs_iocb_iter_write() marks the kiocb with IOCB_WRITE now. Drop freeze
protection with kiocb_end_write_iter() in the completion callback and
get rid of aio->is_write.

No functional changes.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/backing-file.c | 8 ++------
 1 file changed, 2 insertions(+), 6 deletions(-)

diff --git a/fs/backing-file.c b/fs/backing-file.c
index 5780f60662d07..e86f5685758eb 100644
--- a/fs/backing-file.c
+++ b/fs/backing-file.c
@@ -106,8 +106,6 @@ struct backing_aio {
 	struct kiocb iocb;
 	refcount_t ref;
 	struct kiocb *orig_iocb;
-	/* used for aio completion */
-	bool is_write;
 	void (*end_write)(struct kiocb *iocb, ssize_t);
 	struct work_struct work;
 	long res;
@@ -148,9 +146,8 @@ static void backing_aio_rw_complete(struct kiocb *iocb, long res)
 	struct backing_aio *aio = container_of(iocb, struct backing_aio, iocb);
 	struct kiocb *orig_iocb = aio->orig_iocb;
 
-	/* Pairs with kiocb_start_write() in vfs_iocb_iter_write() */
-	if (aio->is_write)
-		kiocb_end_write(iocb);
+	/* Pairs with kiocb_write_iter() in vfs_iocb_iter_write() */
+	kiocb_end_write_iter(iocb);
 
 	backing_aio_cleanup(aio, res);
 	orig_iocb->ki_complete(orig_iocb, res);
@@ -264,7 +261,6 @@ static int do_backing_file_write_iter(struct file *file, struct iov_iter *iter,
 		return -ENOMEM;
 
 	aio->orig_iocb = iocb;
-	aio->is_write = true;
 	aio->end_write = end_write;
 	kiocb_clone(&aio->iocb, iocb, get_file(file));
 	aio->iocb.ki_flags = flags;

-- 
2.53.0
```
