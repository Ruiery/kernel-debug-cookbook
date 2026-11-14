---
title: [PATCH 01/12] fs: add kiocb_start_write_trylock()
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-1-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-1-f5ae61c898b1@kernel.org/
---

# [PATCH 01/12] fs: add kiocb_start_write_trylock()

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-1-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-1-f5ae61c898b1@kernel.org/)

```
kiocb_start_write() waits until a frozen filesystem is thawed. A
nonblocking submission can't use it. io_uring open-codes the trylock
variant for its IOCB_NOWAIT writes.

Add kiocb_start_write_trylock() next to kiocb_start_write() and use it
in io_uring. The nvme target's file backend is going to need it as
well.

No functional changes.

Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 include/linux/fs.h | 22 ++++++++++++++++++++++
 io_uring/rw.c      |  9 +--------
 2 files changed, 23 insertions(+), 8 deletions(-)

diff --git a/include/linux/fs.h b/include/linux/fs.h
index 99caef43ff3c4..eefc2c9d4af19 100644
--- a/include/linux/fs.h
+++ b/include/linux/fs.h
@@ -2801,6 +2801,28 @@ static inline void kiocb_start_write(struct kiocb *iocb)
 	__sb_writers_release(inode->i_sb, SB_FREEZE_WRITE);
 }
 
+/**
+ * kiocb_start_write_trylock - try to get write access to a superblock for
+ *			       async file io
+ * @iocb: the io context we want to submit the write with
+ *
+ * This is kiocb_start_write() for a submission that must not wait until a
+ * frozen filesystem is thawed. Should be matched with a call to
+ * kiocb_end_write() if it succeeds.
+ *
+ * Return: true if write access was acquired, false if it wasn't.
+ */
+static inline bool kiocb_start_write_trylock(struct kiocb *iocb)
+{
+	struct inode *inode = file_inode(iocb->ki_filp);
+
+	if (!sb_start_write_trylock(inode->i_sb))
+		return false;
+	/* Fool lockdep just like kiocb_start_write() does. */
+	__sb_writers_release(inode->i_sb, SB_FREEZE_WRITE);
+	return true;
+}
+
 /**
  * kiocb_end_write - drop write access to a superblock after async file io
  * @iocb: the io context we sumbitted the write with
diff --git a/io_uring/rw.c b/io_uring/rw.c
index 3a8559ff4dc66..a0a16fc521455 100644
--- a/io_uring/rw.c
+++ b/io_uring/rw.c
@@ -1095,9 +1095,6 @@ int io_read_mshot(struct io_kiocb *req, unsigned int issue_flags)
 
 static bool io_kiocb_start_write(struct io_kiocb *req, struct kiocb *kiocb)
 {
-	struct inode *inode;
-	bool ret;
-
 	if (!(req->flags & REQ_F_ISREG))
 		return true;
 	if (!(kiocb->ki_flags & IOCB_NOWAIT)) {
@@ -1105,11 +1102,7 @@ static bool io_kiocb_start_write(struct io_kiocb *req, struct kiocb *kiocb)
 		return true;
 	}
 
-	inode = file_inode(kiocb->ki_filp);
-	ret = sb_start_write_trylock(inode->i_sb);
-	if (ret)
-		__sb_writers_release(inode->i_sb, SB_FREEZE_WRITE);
-	return ret;
+	return kiocb_start_write_trylock(kiocb);
 }
 
 int io_write(struct io_kiocb *req, unsigned int issue_flags)

-- 
2.53.0
```
