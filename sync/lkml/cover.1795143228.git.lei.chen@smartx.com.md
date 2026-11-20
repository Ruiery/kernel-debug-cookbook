---
title: [PATCH v2 0/5] Expose blk-mq tag sets through debugfs
list: linux-block
message_id: cover.1795143228.git.lei.chen@smartx.com
link: https://lore.kernel.org/linux-block/cover.1795143228.git.lei.chen@smartx.com/
---

# [PATCH v2 0/5] Expose blk-mq tag sets through debugfs

来源：[https://lore.kernel.org/linux-block/cover.1795143228.git.lei.chen@smartx.com/](https://lore.kernel.org/linux-block/cover.1795143228.git.lei.chen@smartx.com/)

```
The block debugfs hierarchy currently exposes request queues and hardware
contexts, but not the tag sets they share. This series adds a tag-set view
for configuration, CPU mappings and driver tags, links request queues to
their tag set, and links SCSI tag sets to their controller debugfs data.

Compared with v1:
  - Reworked tag allocation and reclamation so the debugfs objects have a
    safe lifetime across queue initialization and hardware queue updates.
  - Added controller links for megaraid_sas and mpt3sas, including helpers
    that build relative debugfs targets and serialize link updates.
  - Folded the stale CPU mapping comment cleanup into the tag-set changes.

The series is based on Linux v7.3-rc2. The tag-set debugfs implementation
was exercised with concurrent queue resizing, shared tag sets, device
teardown and old file descriptors, allocation fault injection, and KASAN
and lockdep enabled. No KASAN or lockdep reports were observed.

Lei Chen (5):
  block: expose blk-mq tag sets through debugfs
  block: link request queue debugfs directories to tag sets
  block: add helpers to link tag set debugfs to controllers
  scsi: megaraid_sas: Link tag set debugfs to the controller
  scsi: mpt3sas: Link tag set debugfs to the controller

 block/blk-mq-debugfs.c                       | 378 +++++++++++++++++++
 block/blk-mq-debugfs.h                       |  22 ++
 block/blk-mq.c                               |   8 +
 drivers/scsi/megaraid/megaraid_sas_debugfs.c |   3 +
 drivers/scsi/mpt3sas/mpt3sas_debugfs.c       |   4 +-
 include/linux/blk-mq.h                       |  24 ++
 6 files changed, 438 insertions(+), 1 deletion(-)

-- 
2.43.0
```
