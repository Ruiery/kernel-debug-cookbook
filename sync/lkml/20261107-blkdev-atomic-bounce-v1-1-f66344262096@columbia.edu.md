---
title: [PATCH 1/2] block: fail a short atomic bounce in bio_iov_iter_bounce_write()
list: linux-block
message_id: 20261107-blkdev-atomic-bounce-v1-1-f66344262096@columbia.edu
link: https://lore.kernel.org/linux-block/20261107-blkdev-atomic-bounce-v1-1-f66344262096@columbia.edu/
---

# [PATCH 1/2] block: fail a short atomic bounce in bio_iov_iter_bounce_write()

来源：[https://lore.kernel.org/linux-block/20261107-blkdev-atomic-bounce-v1-1-f66344262096@columbia.edu/](https://lore.kernel.org/linux-block/20261107-blkdev-atomic-bounce-v1-1-f66344262096@columbia.edu/)

```
bio_iov_iter_get_pages() fails a REQ_ATOMIC bio that doesn't cover the
whole iterator, since an atomic write is submitted as a single bio, and
submitting only part of it would tear the write. In contrast,
bio_iov_iter_bounce_write() doesn't. If a folio allocation fails partway
through, it returns a short bio, which for an atomic write triggers a
WARN_ON_ONCE() in iomap_dio_bio_iter_one().

Make bio_iov_iter_bounce_write() also check that a REQ_ATOMIC bio covers
the whole iterator, and clean up and return -EINVAL if it doesn't.

Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 block/bio.c | 10 ++++++++++
 1 file changed, 10 insertions(+)

diff --git a/block/bio.c b/block/bio.c
index b0fcc69de653..61a3812520a2 100644
--- a/block/bio.c
+++ b/block/bio.c
@@ -1523,6 +1523,16 @@ int bio_iov_iter_bounce_write(struct bio *bio, struct iov_iter *iter,
 		}
 	}
 
+	/*
+	 * An atomic write is submitted as a single bio, so it has to cover
+	 * the whole iterator or it would be torn.
+	 */
+	if ((bio->bi_opf & REQ_ATOMIC) && iov_iter_count(iter)) {
+		iov_iter_revert(iter, total_copied);
+		bio_free_folios(bio);
+		return -EINVAL;
+	}
+
 	return 0;
 }
 EXPORT_SYMBOL_GPL(bio_iov_iter_bounce_write);

-- 
2.39.5
```
