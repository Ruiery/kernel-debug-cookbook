---
title: [PATCH 0/5] skip tests when a program they need is missing
list: linux-block
message_id: 20261118-skip-missing-deps-v1-0-a9b4a5a7cc94@suse.de
link: https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-0-a9b4a5a7cc94@suse.de/
---

# [PATCH 0/5] skip tests when a program they need is missing

来源：[https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-0-a9b4a5a7cc94@suse.de/](https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-0-a9b4a5a7cc94@suse.de/)

```
Hi all,

a few tests run programs they don't check for, so they fail instead of
being skipped on a host without them. Worse, check leaves the modules
loaded when a test with a fallback device is skipped, which makes the
following tests skip too: a missing xfs_io for scsi/009 took out six
scsi and zbd tests.

The first patch fixes check, the others add the missing requirements.

On a Debian 13 VM with a 7.3 kernel and without these tools, all tests
that fail are kernel bugs except nvme/068. With the tools installed, a
run of all groups but meta goes from 81 to 120 passing tests. The
remaining failures are block/052, block/053, nvme/073, nvme/074,
nvme/076 and zbd/009, which hits a btrfs warning in
btrfs_schedule_zone_finish_bg().

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
Daniel Wagner (5):
      check: unload modules when a test with a fallback device is skipped
      nvme/053, nvme/068: skip if fio or xfs_io is missing
      nbd/003: skip if mkfs.ext4 is missing
      block/009, block/012: skip if hexdump is missing
      zbd/008: skip if fio or hexdump is missing

 check           | 3 +++
 tests/block/009 | 1 +
 tests/block/012 | 1 +
 tests/nbd/003   | 1 +
 tests/nvme/053  | 4 ++++
 tests/nvme/068  | 1 +
 tests/zbd/008   | 2 ++
 7 files changed, 13 insertions(+)
---
base-commit: 79c32fb31b7bca6a4383b749030128683cf6b6b4
change-id: 20261117-skip-missing-deps-30b4084698c4

Best regards,
--  
Daniel Wagner <dwagner@suse.de>
```
