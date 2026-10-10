---
title: [PATCH blktests v2 0/4] blktests: tests for the direct I/O fallback, splice, bio trimming, and atomic write fixes
list: linux-block
message_id: 20261009-blkdev-fixes-tests-v2-0-fcb3599e47f7@columbia.edu
link: https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-0-fcb3599e47f7@columbia.edu/
---

# [PATCH blktests v2 0/4] blktests: tests for the direct I/O fallback, splice, bio trimming, and atomic write fixes

来源：[https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-0-fcb3599e47f7@columbia.edu/](https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-0-fcb3599e47f7@columbia.edu/)

```
Four regression tests for block device fixes under review [1],
following block/048 for the first patch of that series.

block/049 races partial O_DIRECT writes, which finish through the
direct I/O write fallback, against BLKBSZSET. block/050 does the same
with splice(). Both need CONFIG_DEBUG_VM to report the folio order
mismatch, and skip on kernels without a 64K block size or with 64K
pages.

block/051 issues trimmed O_DIRECT writes from a hugetlb mapping to a
device with a 64K logical block size and checks that no huge pages
leak, covering both the dropped and the shrunk bvec.

block/052 issues a RWF_ATOMIC write from a buffer whose last page
cannot be pinned to a scsi_debug device with atomic_wr=1 and checks
that the device holds all of the new data or none of it.

[1] https://lore.kernel.org/linux-block/20261009-blkdev-fixes-v6-0-307939c387df@columbia.edu/

---
Changes in v2:
- Rebase on current master.
- New block/052: test that a partially pinned RWF_ATOMIC write is not
  torn, as requested by John Garry.
- Change the kernel patch links to v6 of the series.
- Link to v1: https://patch.msgid.link/20260909-blkdev-fixes-tests-v1-0-1f8af8665d16@columbia.edu

---
Tal Zussman (4):
      block/049: add a direct I/O write fallback race test for block devices
      block/050: add a splice read race test for block devices
      block/051: add a pinned page leak test for trimmed direct writes
      block/052: add a torn atomic write test for block devices

 src/.gitignore          |   4 +
 src/Makefile            |  10 ++-
 src/atomic-write-torn.c | 131 +++++++++++++++++++++++++++
 src/bio-trim-pin-leak.c | 191 ++++++++++++++++++++++++++++++++++++++++
 src/dio-fallback-race.c | 229 ++++++++++++++++++++++++++++++++++++++++++++++++
 src/splice-race.c       | 171 ++++++++++++++++++++++++++++++++++++
 tests/block/049         |  57 ++++++++++++
 tests/block/049.out     |   2 +
 tests/block/050         |  54 ++++++++++++
 tests/block/050.out     |   2 +
 tests/block/051         |  64 ++++++++++++++
 tests/block/051.out     |   2 +
 tests/block/052         |  70 +++++++++++++++
 tests/block/052.out     |   2 +
 14 files changed, 988 insertions(+), 1 deletion(-)
---
base-commit: 87eb7c2c006101090609a2994df272c9395fd058
change-id: 20260909-blkdev-fixes-tests-670f566f5f85

Best regards,
--  
Tal Zussman <tz2294@columbia.edu>
```
