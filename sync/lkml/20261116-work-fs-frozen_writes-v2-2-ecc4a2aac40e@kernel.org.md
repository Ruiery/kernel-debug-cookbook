---
title: [PATCH v2 02/17] fs: add kiocb_write_iter() and kiocb_end_write_iter()
list: linux-block
message_id: 20261116-work-fs-frozen_writes-v2-2-ecc4a2aac40e@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-2-ecc4a2aac40e@kernel.org/
---

# [PATCH v2 02/17] fs: add kiocb_write_iter() and kiocb_end_write_iter()

来源：[https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-2-ecc4a2aac40e@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-2-ecc4a2aac40e@kernel.org/)

```
Calling ->write_iter() with a kiocb of your own means taking freeze
protection, calling ->write_iter() and dropping freeze protection again
unless the write was queued. The completion callback then has to know
whether it completes a write that still holds freeze protection. loop
open-codes this and keys the completion on the request op. zloop, the
nvme target and target fileio need the same. Christoph pointed out that
open-coding this everywhere is fragile (cf. [1]).

Add kiocb_write_iter(). It takes freeze protection, marks the kiocb
with IOCB_WRITE like aio, io_uring and cachefiles do and calls
->write_iter(). If the write wasn't queued freeze protection is dropped
right away. With IOCB_NOWAIT it only tries to get freeze protection and
fails with -EAGAIN instead of waiting for the thaw.

kiocb_end_write_iter() drops freeze protection if the kiocb still holds
it and clears IOCB_WRITE. So a completion callback can call it for any
I/O. That matters for drivers that complete I/O that wasn't queued
through the same callback and for drivers that reuse their kiocbs.

[1]: https://lore.kernel.org/r/20261116064654.GA2964@lst.de

Suggested-by: Christoph Hellwig <hch@lst.de>
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 include/linux/fs.h | 48 ++++++++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 48 insertions(+)

diff --git a/include/linux/fs.h b/include/linux/fs.h
index eefc2c9d4af19..0b66a09fb686a 100644
--- a/include/linux/fs.h
+++ b/include/linux/fs.h
@@ -2840,6 +2840,54 @@ static inline void kiocb_end_write(struct kiocb *iocb)
 	sb_end_write(inode->i_sb);
 }
 
+/**
+ * kiocb_end_write_iter - drop write access after kiocb_write_iter()
+ * @iocb: the io context the write was submitted with
+ *
+ * Drop write access if @iocb still holds it and clear IOCB_WRITE. This
+ * does nothing for reads and for writes kiocb_write_iter() already
+ * finished. So the completion callback can call it for any I/O.
+ */
+static inline void kiocb_end_write_iter(struct kiocb *iocb)
+{
+	if (!(iocb->ki_flags & IOCB_WRITE))
+		return;
+	iocb->ki_flags &= ~IOCB_WRITE;
+	kiocb_end_write(iocb);
+}
+
+/**
+ * kiocb_write_iter - submit a write with write access to the superblock
+ * @iocb: the io context to submit the write with
+ * @iter: the data to write
+ *
+ * Get write access, mark @iocb with IOCB_WRITE and call ->write_iter().
+ * A write that wasn't queued drops write access before this returns. A
+ * queued write keeps it until the completion callback calls
+ * kiocb_end_write_iter(). With IOCB_NOWAIT this fails with -EAGAIN
+ * instead of waiting for a frozen filesystem.
+ *
+ * Return: On success the number of bytes written or -EIOCBQUEUED is
+ *         returned. On failure a negative error code is returned.
+ */
+static inline ssize_t kiocb_write_iter(struct kiocb *iocb,
+				       struct iov_iter *iter)
+{
+	ssize_t ret;
+
+	if (iocb->ki_flags & IOCB_NOWAIT) {
+		if (!kiocb_start_write_trylock(iocb))
+			return -EAGAIN;
+	} else {
+		kiocb_start_write(iocb);
+	}
+	iocb->ki_flags |= IOCB_WRITE;
+	ret = iocb->ki_filp->f_op->write_iter(iocb, iter);
+	if (ret != -EIOCBQUEUED)
+		kiocb_end_write_iter(iocb);
+	return ret;
+}
+
 /*
  * This is used for regular files where some users -- especially the
  * currently executed binary in a process, previously handled via

-- 
2.53.0
```
