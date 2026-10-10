---
title: [PATCH v6 7/9] iomap: reject atomic writes in iomap_file_buffered_write()
list: linux-block
message_id: 20261009-blkdev-fixes-v6-7-307939c387df@columbia.edu
link: https://lore.kernel.org/linux-block/20261009-blkdev-fixes-v6-7-307939c387df@columbia.edu/
---

# [PATCH v6 7/9] iomap: reject atomic writes in iomap_file_buffered_write()

来源：[https://lore.kernel.org/linux-block/20261009-blkdev-fixes-v6-7-307939c387df@columbia.edu/](https://lore.kernel.org/linux-block/20261009-blkdev-fixes-v6-7-307939c387df@columbia.edu/)

```
Buffered atomic writes are not currently supported. The page cache
writes folios back independently, so it cannot guarantee that a range is
written atomically. iomap_file_buffered_write() does not check for
IOCB_ATOMIC, so a direct write that falls back to it would complete an
atomic write without atomicity. While no such case currently exists,
fail IOCB_ATOMIC writes with -EOPNOTSUPP, so that a future fallback
cannot complete an atomic write non-atomically.

Suggested-by: John Garry <john.garry@linux.dev>
Reviewed-by: John Garry <john.garry@linux.dev>
Reviewed-by: Hannes Reinecke <hare@kernel.org>
Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 fs/iomap/buffered-io.c | 4 ++++
 1 file changed, 4 insertions(+)

diff --git a/fs/iomap/buffered-io.c b/fs/iomap/buffered-io.c
index 0a5ebfda90f1..e6654cfe1cbf 100644
--- a/fs/iomap/buffered-io.c
+++ b/fs/iomap/buffered-io.c
@@ -1304,6 +1304,10 @@ iomap_file_buffered_write(struct kiocb *iocb, struct iov_iter *i,
 	};
 	ssize_t ret;
 
+	/* Buffered atomic writes are not supported */
+	if (iocb->ki_flags & IOCB_ATOMIC)
+		return -EOPNOTSUPP;
+
 	if (iocb->ki_flags & IOCB_NOWAIT)
 		iter.flags |= IOMAP_NOWAIT;
 	if (iocb->ki_flags & IOCB_DONTCACHE)

-- 
2.39.5
```
