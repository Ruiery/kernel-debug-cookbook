---
title: [PATCH v5 6/9] block: don't fall back to buffered I/O for atomic writes
list: linux-block
message_id: 20260923-blkdev-fixes-v5-6-89e60d66eb38@columbia.edu
link: https://lore.kernel.org/linux-block/20260923-blkdev-fixes-v5-6-89e60d66eb38@columbia.edu/
---

# [PATCH v5 6/9] block: don't fall back to buffered I/O for atomic writes

来源：[https://lore.kernel.org/linux-block/20260923-blkdev-fixes-v5-6-89e60d66eb38@columbia.edu/](https://lore.kernel.org/linux-block/20260923-blkdev-fixes-v5-6-89e60d66eb38@columbia.edu/)

```
blkdev_direct_write() turns an -EBUSY from page cache invalidation into
a 0 return, so an IOCB_ATOMIC write is retried in full through
blkdev_buffered_write(), with no atomicity guarantee.

Skip the buffered fallback in blkdev_write_iter() for IOCB_ATOMIC, as
it already does for IOCB_NOWAIT, so the -EBUSY case returns -EAGAIN and
the caller retries, matching __iomap_dio_rw().

ext4 has the same fallback and only warns in it. For block devices the
fallback can be skipped before any I/O is submitted, so fail early
instead.

Fixes: caf336f81b3a ("block: Add fops atomic write support")
Reported-by: Sashiko <sashiko-bot@kernel.org>
Link: https://sashiko.dev/#/patchset/20260802-blkdev-fixes-v1-0-a82fc549fd74%40columbia.edu?part=2
Assisted-by: Claude:claude-fable-5
Reviewed-by: Hannes Reinecke <hare@kernel.org>
Reviewed-by: John Garry <john.garry@linux.dev>
Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 block/fops.c | 5 +++--
 1 file changed, 3 insertions(+), 2 deletions(-)

diff --git a/block/fops.c b/block/fops.c
index d143a664c770..59af4e808204 100644
--- a/block/fops.c
+++ b/block/fops.c
@@ -771,10 +771,11 @@ static ssize_t blkdev_write_iter(struct kiocb *iocb, struct iov_iter *from)
 	if (iocb->ki_flags & IOCB_DIRECT) {
 		ret = blkdev_direct_write(iocb, from);
 		if (ret >= 0 && iov_iter_count(from)) {
-			if (iocb->ki_flags & IOCB_NOWAIT) {
+			if (iocb->ki_flags & (IOCB_NOWAIT | IOCB_ATOMIC)) {
 				/*
 				 * The buffered fallback blocks on i_rwsem and
-				 * on writeback of the data it copied: return
+				 * on writeback of the data it copied, and
+				 * can't provide torn-write protection: return
 				 * the short direct write instead and let the
 				 * caller retry.
 				 */

-- 
2.39.5
```
