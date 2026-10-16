---
title: [PATCH blktests v3 0/4] blktests: tests for the direct I/O fallback, splice, bio trimming, and atomic write fixes
list: linux-block
message_id: 20261015-blkdev-fixes-tests-v3-0-b6ffa6410514@columbia.edu
link: https://lore.kernel.org/linux-block/20261015-blkdev-fixes-tests-v3-0-b6ffa6410514@columbia.edu/
---

# [PATCH blktests v3 0/4] blktests: tests for the direct I/O fallback, splice, bio trimming, and atomic write fixes

来源：[https://lore.kernel.org/linux-block/20261015-blkdev-fixes-tests-v3-0-b6ffa6410514@columbia.edu/](https://lore.kernel.org/linux-block/20261015-blkdev-fixes-tests-v3-0-b6ffa6410514@columbia.edu/)

```
Four regression tests for block device fixes under review [1],
following block/048 for the first patch of that series.

block/050 races partial O_DIRECT writes, which finish through the
direct I/O write fallback, against BLKBSZSET. block/051 does the same
with splice(). Both need CONFIG_DEBUG_VM to report the folio order
mismatch, and skip on kernels without a 64K block size or with 64K
pages.

block/052 issues trimmed O_DIRECT writes from a hugetlb mapping to a
device with a 64K logical block size and checks that no huge pages
leak, covering both the dropped and the shrunk bvec.

block/053 issues a RWF_ATOMIC write from a buffer whose last page
cannot be pinned to a scsi_debug device with atomic_wr=1 and checks
that the device holds all of the new data or none of it.

[1] https://lore.kernel.org/linux-block/20261009-blkdev-fixes-v6-0-307939c387df@columbia.edu/

---
Changes in v3:
- Rebase on current master, and renumber the tests to block/050 to
  block/053 after the new block/049.
- block/050: release the mapping and the file descriptor on the helper's
  error paths, and the buffer and file descriptor of each writer and
  reader thread when it exits.
- block/050: fail on a write that returns less than its direct part.
- block/052: release the mapping and the file descriptor on the helper's
  error paths.
- block/053: check that the device supports atomic writes with statx()
  instead of reading the atomic write unit max from sysfs, per John
  Garry.
- block/053: always write two pages, and raise the scsi_debug atomic
  write unit max to 128K so that they fit for any page size, instead of
  skipping the test when they do not, per John Garry.
- block/053: check that the atomic write fails with EINVAL, and report a
  write that went through separately from a torn one, per John Garry.
- block/053: read the old contents back before the atomic write, per
  John Garry.
- block/053: reuse the write buffer for the readback, per John Garry.
- block/053: release the file descriptor and the mapping on error paths,
  per John Garry.
- block/053: report a missing scsi_debug module once.
- block/053: specify that it is hardware atomic writes that are
  submitted as a single bio, per John Garry.
- Link to v2: https://patch.msgid.link/20261009-blkdev-fixes-tests-v2-0-fcb3599e47f7@columbia.edu

Changes in v2:
- Rebase on current master.
- New block/052: test that a partially pinned RWF_ATOMIC write is not
  torn, as requested by John Garry.
- Change the kernel patch links to v6 of the series.
- Link to v1: https://patch.msgid.link/20260909-blkdev-fixes-tests-v1-0-1f8af8665d16@columbia.edu

---
Tal Zussman (4):
      block/050: add a direct I/O write fallback race test for block devices
      block/051: add a splice read race test for block devices
      block/052: add a pinned page leak test for trimmed direct writes
      block/053: add a torn atomic write test for block devices

 src/.gitignore          |   4 +
 src/Makefile            |  10 +-
 src/atomic-write-torn.c | 233 ++++++++++++++++++++++++++++++++++++++++++++
 src/bio-trim-pin-leak.c | 200 ++++++++++++++++++++++++++++++++++++++
 src/dio-fallback-race.c | 251 ++++++++++++++++++++++++++++++++++++++++++++++++
 src/splice-race.c       | 171 +++++++++++++++++++++++++++++++++
 tests/block/050         |  57 +++++++++++
 tests/block/050.out     |   2 +
 tests/block/051         |  54 +++++++++++
 tests/block/051.out     |   2 +
 tests/block/052         |  64 ++++++++++++
 tests/block/052.out     |   2 +
 tests/block/053         |  60 ++++++++++++
 tests/block/053.out     |   2 +
 14 files changed, 1111 insertions(+), 1 deletion(-)
---
base-commit: d418e94a3d590640bbc0012bdec1c3e74ce8be11
change-id: 20260909-blkdev-fixes-tests-670f566f5f85

Best regards,
--  
Tal Zussman <tz2294@columbia.edu>
```
