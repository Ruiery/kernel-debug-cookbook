---
title: [PATCH RFC v2 3/3] ext4: don't advertise atomic writes for DAX inodes
list: linux-block
message_id: 20261012-ext4-atomic-no-fallback-v2-3-c4b30c60e500@columbia.edu
link: https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-3-c4b30c60e500@columbia.edu/
---

# [PATCH RFC v2 3/3] ext4: don't advertise atomic writes for DAX inodes

来源：[https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-3-c4b30c60e500@columbia.edu/](https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-3-c4b30c60e500@columbia.edu/)

```
ext4_file_write_iter() hands DAX inodes to ext4_dax_write_iter() before
any of the atomic write handling, and the DAX path neither checks
IOCB_ATOMIC nor provides torn-write protection.
ext4_inode_can_atomic_write() doesn't exclude DAX inodes, so on a device
that supported both DAX and atomic writes, statx() would advertise
atomic writes for such an inode and the VFS would let an RWF_ATOMIC
write through to a plain DAX write.

No DAX-capable block device advertises atomic write limits today, so
this isn't reachable. When XFS gained its corresponding check, Ritesh
Harjani suggested excluding DAX inodes in ext4 anyway [1], so that what
is advertised matches what the write path can do. XFS does the same in
xfs_inode_can_hw_atomic_write() and xfs_inode_can_sw_atomic_write().

Link: https://lore.kernel.org/linux-ext4/87a54e4cdn.fsf@gmail.com/ [1]
Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 fs/ext4/ext4.h | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

diff --git a/fs/ext4/ext4.h b/fs/ext4/ext4.h
index 5115f067a9f5..1520baf581b6 100644
--- a/fs/ext4/ext4.h
+++ b/fs/ext4/ext4.h
@@ -4060,12 +4060,13 @@ static inline int ext4_buffer_uptodate(struct buffer_head *bh)
 /*
  * Atomic writes are only supported through direct I/O, so an inode that
  * can't do direct I/O at all (journaled data, inline data, verity) can't do
- * atomic writes either.
+ * atomic writes either. DAX inodes bypass the direct I/O path entirely.
  */
 static inline bool ext4_inode_can_atomic_write(struct inode *inode)
 {
 
 	return S_ISREG(inode->i_mode) &&
+		!IS_DAX(inode) &&
 		ext4_test_inode_flag(inode, EXT4_INODE_EXTENTS) &&
 		EXT4_SB(inode->i_sb)->s_awu_min > 0 &&
 		ext4_dio_alignment(inode) != 0;

-- 
2.39.5
```
