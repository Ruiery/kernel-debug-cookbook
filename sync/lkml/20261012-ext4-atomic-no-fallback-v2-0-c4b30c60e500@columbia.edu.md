---
title: [PATCH RFC v2 0/3] ext4: don't complete atomic writes through buffered I/O
list: linux-block
message_id: 20261012-ext4-atomic-no-fallback-v2-0-c4b30c60e500@columbia.edu
link: https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-0-c4b30c60e500@columbia.edu/
---

# [PATCH RFC v2 0/3] ext4: don't complete atomic writes through buffered I/O

来源：[https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-0-c4b30c60e500@columbia.edu/](https://lore.kernel.org/linux-block/20261012-ext4-atomic-no-fallback-v2-0-c4b30c60e500@columbia.edu/)

```
ext4_dio_write_iter() has two ways to finish a write through the page
cache: the fallback for inodes that can't do direct I/O at all, and the
completion of a short direct write. Neither provides torn-write
protection, and neither refuses IOCB_ATOMIC.

Patch 1 fixes a reachable bug: an atomic write to a data-journaled
inode is advertised by statx() and then silently done as a buffered
write. Patch 2 makes a short atomic direct write fail with -EIO instead
of falling back. That path should be unreachable today, so this is
defensive. Patch 3 closes the same kind of gap for DAX inodes,
which ext4_file_write_iter() hands to the DAX path before any atomic
write handling. No DAX-capable device advertises atomic write limits
today, so this one is defensive too, and matches XFS.

With a scsi_debug device, on a data=journal mount, and with chattr +j on
a nodelalloc mount, the unpatched kernel reports atomic write limits via
statx() and completes an O_DIRECT RWF_ATOMIC pwritev2() as a buffered
write. With the series, statx() reports awu_min=0 and the write fails
with -EOPNOTSUPP. Ordinary extent files still complete atomic writes,
and the WARN_ON_ONCE() in patch 2 did not fire under an fio atomic
direct write workload.

---
Changes in v2:
- Patch 1 (new): Reject atomic writes on inodes that can't do direct
  I/O at all, where the fallback to buffered I/O is reachable, per
  Sashiko.
- Patch 2: Fail a short atomic direct write with -EIO and keep the
  WARN_ON_ONCE(), instead of returning the short count.
- Patch 3 (new): don't advertise atomic writes for DAX inodes.
- Link to v1: https://patch.msgid.link/20260909-ext4-atomic-no-fallback-v1-1-5a6b9539c002@columbia.edu

---
Tal Zussman (3):
      ext4: reject atomic writes on inodes that can't do direct I/O
      ext4: never fall back to buffered I/O for atomic direct writes
      ext4: don't advertise atomic writes for DAX inodes

 fs/ext4/ext4.h |  9 ++++++++-
 fs/ext4/file.c | 17 +++++++++++++----
 2 files changed, 21 insertions(+), 5 deletions(-)
---
base-commit: df2908090cda368b01ff43709f51890076c56157
change-id: 20260909-ext4-atomic-no-fallback-b1550a7a3fcf

Best regards,
--  
Tal Zussman <tz2294@columbia.edu>
```
