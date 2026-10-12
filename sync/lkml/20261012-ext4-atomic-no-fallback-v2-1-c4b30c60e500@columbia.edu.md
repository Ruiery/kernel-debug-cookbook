---
title: [PATCH RFC v2 1/3] ext4: reject atomic writes on inodes that can't do direct I/O
list: linux-block
message_id: 20261012-ext4-atomic-no-fallback-v2-1-c4b30c60e500@columbia.edu
link: https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-1-c4b30c60e500@columbia.edu/
---

# [PATCH RFC v2 1/3] ext4: reject atomic writes on inodes that can't do direct I/O

来源：[https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-1-c4b30c60e500@columbia.edu/](https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-1-c4b30c60e500@columbia.edu/)

```
ext4_dio_write_iter() falls back to buffered I/O when the inode can't do
direct I/O at all, i.e. journaled data, inline data or verity. That
fallback runs before any atomic write handling, and
ext4_buffered_write_iter() doesn't look at IOCB_ATOMIC, so an atomic
write to such an inode is silently done as a plain buffered write with
no torn-write protection.

ext4_inode_can_atomic_write() makes it worse for journaled data by
advertising atomic writes for those inodes: statx() reports atomic write
limits and the file gets FMODE_CAN_ATOMIC_WRITE, so the write passes the
VFS checks and reaches the fallback. This is reachable with
data=journal, or with chattr +j on a nodelalloc mount. Inline data
inodes don't have the extents flag and verity files can't be opened for
writing, so those are refused before ext4 sees the write, but the
fallback would still accept them.

Reject IOCB_ATOMIC in ext4_buffered_write_iter(), next to the existing
IOCB_NOWAIT rejection, so neither fallback into it can complete an
atomic write non-atomically. Also require ext4_dio_alignment() to be
nonzero in ext4_inode_can_atomic_write(), so statx() stops advertising
atomic writes for these inodes and VFS refuses RWF_ATOMIC early. The
runtime check is still needed, as the journal data flag can be changed
on an open file.

Fixes: b7987a7d69a4 ("ext4: Support setting FMODE_CAN_ATOMIC_WRITE")
Reported-by: Sashiko <sashiko-bot@kernel.org>
Link: https://sashiko.dev/#/patchset/20260909-ext4-atomic-no-fallback-v1-1-5a6b9539c002%40columbia.edu
Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 fs/ext4/ext4.h | 8 +++++++-
 fs/ext4/file.c | 8 ++++++++
 2 files changed, 15 insertions(+), 1 deletion(-)

diff --git a/fs/ext4/ext4.h b/fs/ext4/ext4.h
index 724a27e8be61..5115f067a9f5 100644
--- a/fs/ext4/ext4.h
+++ b/fs/ext4/ext4.h
@@ -4057,12 +4057,18 @@ static inline int ext4_buffer_uptodate(struct buffer_head *bh)
 	return buffer_uptodate(bh);
 }
 
+/*
+ * Atomic writes are only supported through direct I/O, so an inode that
+ * can't do direct I/O at all (journaled data, inline data, verity) can't do
+ * atomic writes either.
+ */
 static inline bool ext4_inode_can_atomic_write(struct inode *inode)
 {
 
 	return S_ISREG(inode->i_mode) &&
 		ext4_test_inode_flag(inode, EXT4_INODE_EXTENTS) &&
-		EXT4_SB(inode->i_sb)->s_awu_min > 0;
+		EXT4_SB(inode->i_sb)->s_awu_min > 0 &&
+		ext4_dio_alignment(inode) != 0;
 }
 
 extern int ext4_block_write_begin(handle_t *handle, struct folio *folio,
diff --git a/fs/ext4/file.c b/fs/ext4/file.c
index 374b4bc25bd5..19a8843ac420 100644
--- a/fs/ext4/file.c
+++ b/fs/ext4/file.c
@@ -339,6 +339,14 @@ static ssize_t ext4_buffered_write_iter(struct kiocb *iocb,
 	if (iocb->ki_flags & IOCB_NOWAIT)
 		return -EOPNOTSUPP;
 
+	/*
+	 * Buffered I/O provides no torn-write protection. The direct I/O path
+	 * falls back here for inodes that can't do direct I/O at all, so an
+	 * atomic write must be rejected rather than silently done non-atomically.
+	 */
+	if (iocb->ki_flags & IOCB_ATOMIC)
+		return -EOPNOTSUPP;
+
 	inode_lock(inode);
 
 	/*

-- 
2.39.5
```
