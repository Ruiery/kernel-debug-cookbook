---
title: [PATCH 0/2] block: fail short atomic bounce bios in bio_iov_iter_bounce_write()
list: linux-block
message_id: 20261107-blkdev-atomic-bounce-v1-0-f66344262096@columbia.edu
link: https://lore.kernel.org/linux-block/20261107-blkdev-atomic-bounce-v1-0-f66344262096@columbia.edu/
---

# [PATCH 0/2] block: fail short atomic bounce bios in bio_iov_iter_bounce_write()

来源：[https://lore.kernel.org/linux-block/20261107-blkdev-atomic-bounce-v1-0-f66344262096@columbia.edu/](https://lore.kernel.org/linux-block/20261107-blkdev-atomic-bounce-v1-0-f66344262096@columbia.edu/)

```
bio_iov_iter_get_pages() fails a short REQ_ATOMIC bio. In contrast,
bio_iov_iter_bounce_write() doesn't, so a bounced atomic write that runs
into a folio allocation failure triggers a WARN_ON_ONCE() in
iomap_dio_bio_iter_one().

The first patch makes bio_iov_iter_bounce_write() also check that a
REQ_ATOMIC bio covers the whole iterator, and clean up and return
-EINVAL if it doesn't. With both paths covered the iomap check can't
trigger, so the second patch removes it, as suggested by John Garry.

---
Tal Zussman (2):
      block: fail a short atomic bounce in bio_iov_iter_bounce_write()
      iomap: remove the atomic write length check in iomap_dio_bio_iter_one()

 block/bio.c          | 10 ++++++++++
 fs/iomap/direct-io.c | 14 --------------
 2 files changed, 10 insertions(+), 14 deletions(-)
---
base-commit: 839203759f536e6ef1267c80309c3532a7d588cc
change-id: 20261014-blkdev-atomic-bounce-fc9c583083d7

Best regards,
--  
Tal Zussman <tz2294@columbia.edu>
```
