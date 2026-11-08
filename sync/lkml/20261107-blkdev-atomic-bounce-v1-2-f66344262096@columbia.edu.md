---
title: [PATCH 2/2] iomap: remove the atomic write length check in iomap_dio_bio_iter_one()
list: linux-block
message_id: 20261107-blkdev-atomic-bounce-v1-2-f66344262096@columbia.edu
link: https://lore.kernel.org/linux-block/20261107-blkdev-atomic-bounce-v1-2-f66344262096@columbia.edu/
---

# [PATCH 2/2] iomap: remove the atomic write length check in iomap_dio_bio_iter_one()

来源：[https://lore.kernel.org/linux-block/20261107-blkdev-atomic-bounce-v1-2-f66344262096@columbia.edu/](https://lore.kernel.org/linux-block/20261107-blkdev-atomic-bounce-v1-2-f66344262096@columbia.edu/)

```
bio_iov_iter_get_pages() and bio_iov_iter_bounce_write() now fail a
REQ_ATOMIC bio that doesn't cover the whole iterator, so the bio here
always covers iomap_length() and the check can't trigger. Remove the
check.

Suggested-by: John Garry <john.garry@linux.dev>
Link: https://lore.kernel.org/all/82978d5c-3e08-48e9-bf0a-7913e1cd0507@linux.dev/
Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 fs/iomap/direct-io.c | 14 --------------
 1 file changed, 14 deletions(-)

diff --git a/fs/iomap/direct-io.c b/fs/iomap/direct-io.c
index ad041ac3252a..aca7cbaea4af 100644
--- a/fs/iomap/direct-io.c
+++ b/fs/iomap/direct-io.c
@@ -370,15 +370,6 @@ static ssize_t iomap_dio_bio_iter_one(struct iomap_iter *iter,
 		goto out_put_bio;
 	ret = bio->bi_iter.bi_size;
 
-	/*
-	 * An atomic write bio must cover the complete length.  If it doesn't,
-	 * error out.
-	 */
-	if ((op & REQ_ATOMIC) && WARN_ON_ONCE(ret != iomap_length(iter))) {
-		ret = -EINVAL;
-		goto out_bio_release_pages;
-	}
-
 	if (dio->flags & IOMAP_DIO_WRITE)
 		task_io_account_write(ret);
 	else if ((dio->flags & IOMAP_DIO_USER_BACKED) &&
@@ -393,11 +384,6 @@ static ssize_t iomap_dio_bio_iter_one(struct iomap_iter *iter,
 	iomap_dio_submit_bio(iter, dio, bio, pos);
 	return ret;
 
-out_bio_release_pages:
-	if (dio->flags & IOMAP_DIO_BOUNCE)
-		bio_free_folios(bio);
-	else
-		bio_release_pages(bio, false);
 out_put_bio:
 	bio_put(bio);
 	return ret;

-- 
2.39.5
```
