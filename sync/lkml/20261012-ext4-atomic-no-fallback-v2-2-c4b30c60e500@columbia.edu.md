---
title: [PATCH RFC v2 2/3] ext4: never fall back to buffered I/O for atomic direct writes
list: linux-block
message_id: 20261012-ext4-atomic-no-fallback-v2-2-c4b30c60e500@columbia.edu
link: https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-2-c4b30c60e500@columbia.edu/
---

# [PATCH RFC v2 2/3] ext4: never fall back to buffered I/O for atomic direct writes

来源：[https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-2-c4b30c60e500@columbia.edu/](https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-2-c4b30c60e500@columbia.edu/)

```
ext4_dio_write_iter() finishes a short direct write through the page
cache. ext4_buffered_write_iter() now rejects IOCB_ATOMIC, so a short
atomic write would warn and then fail with -EOPNOTSUPP, as if atomic
writes were unsupported on the inode.

This came out of a block device fix [1], where an IOCB_ATOMIC direct
write could complete short when only part of the buffer could be
pinned, with the rest going through the buffered fallback. Christoph
Hellwig noted that ext4 has the same fallback and only warns in it [2],
and John Garry agreed it should reject the write instead [3].

In contrast to the block device, nothing reaches the branch on ext4
today: iomap requires the mapping to cover the whole atomic write, a
buffer that can't be pinned in full fails in iomap before the bio is
submitted, and a failed page cache invalidation returns -EAGAIN rather
than reaching the buffered fallback. A short atomic write is therefore
a bug, and neither a short count nor -EOPNOTSUPP is a valid result for
one. Fail the write with -EIO before the fallback, keeping the WARN()
so any future bug is visible.

Link: https://lore.kernel.org/linux-block/20260828-blkdev-fixes-v2-0-32f3f40cebed@columbia.edu/ [1]
Link: https://lore.kernel.org/linux-block/20260907071217.GD934@lst.de/ [2]
Link: https://lore.kernel.org/linux-block/a7752d1e-8ec1-44d1-a266-c287c315e8ab@oracle.com/ [3]
Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 fs/ext4/file.c | 9 +++++----
 1 file changed, 5 insertions(+), 4 deletions(-)

diff --git a/fs/ext4/file.c b/fs/ext4/file.c
index 19a8843ac420..11e375bd4ed1 100644
--- a/fs/ext4/file.c
+++ b/fs/ext4/file.c
@@ -679,11 +679,12 @@ static ssize_t ext4_dio_write_iter(struct kiocb *iocb, struct iov_iter *from)
 		loff_t endbyte;
 
 		/*
-		 * There is no support for atomic writes on buffered-io yet,
-		 * we should never fallback to buffered-io for DIO atomic
-		 * writes.
+		 * Buffered I/O provides no torn-write protection, so never
+		 * finish an atomic write through the page cache. iomap must
+		 * not return a short atomic write, so treat one as a bug.
 		 */
-		WARN_ON_ONCE(iocb->ki_flags & IOCB_ATOMIC);
+		if (WARN_ON_ONCE(iocb->ki_flags & IOCB_ATOMIC))
+			return -EIO;
 
 		offset = iocb->ki_pos;
 		err = ext4_buffered_write_iter(iocb, from);

-- 
2.39.5
```
