---
title: [PATCH RFC 0/2] Support for Multiple Atomicity Mode
list: linux-block
message_id: 20260929-nvme-mam-v1-0-48dcbe79cece@samsung.com
link: https://lore.kernel.org/linux-block/20260929-nvme-mam-v1-0-48dcbe79cece@samsung.com/
---

# [PATCH RFC 0/2] Support for Multiple Atomicity Mode

来源：[https://lore.kernel.org/linux-block/20260929-nvme-mam-v1-0-48dcbe79cece@samsung.com/](https://lore.kernel.org/linux-block/20260929-nvme-mam-v1-0-48dcbe79cece@samsung.com/)

```
NVMe has 2 atomic modes: Single Atomicity Mode (SAM) and Multiple
Atomicity Mode (MAM). In SAM mode, as per spec, commands that cross
the atomic boundaries may or may not be guaranteed to be atomic. In MAM
mode, commands that cross the atomic boundaries will be guaranteed to
be atomic at the LBA subrange atomic boundaries, resulting in multiple
atomic operations.

This series adds a new block layer feature BLK_FEAT_ATOMIC_WRITE_MULTI
that gets enabled when an NVMe controller exposes MAM guarantees. In
this case, and when the block IO requests are SAM compliant, allow the
block layer to merge atomic command requests that are contiguous in the
LBA ranges, leveraging block plug-merge infra, and effectively
increasing the size of the command up to the maximum hardware
capabilities. The merged command is not atomic as a whole, so it becomes
a carrier of multiple atomic commands. This is possible because the
RWF_ATOMIC that the user has requested is honored at the LBA subrange
later at the controller side when the carrier command is split at the
atomic boundaries.

MAM QEMU NVMe series [1] covers emulation functionality for testing.

While I think this small feature is worth having (hence this RFC)
for users sending atomic write commands that are contiguous, the
question I'd also like to discuss really is how to also expose clear
MAM semantics to userspace for users who can send larger commands,
so they avoid syscall overhead [2] and splitting, and still get the
atomic guarantees in the LBA subranges. RWF_ATOMIC currently exposes
SAM semantics, but I think MAM may be confusing for users, as it's not
simply a larger atomic write but an atomic carrier. Thoughts? What can
work best to leverage MAM from userspace without conflicting with SAM?

Command line logs covering functionality with nvme-cli, fio and
blktrace:

nvme id-ns -H /dev/nvme0n1
NVME Identify Namespace 1:
{..}
nsfeat  : 0x76
  [7:7] : 0     NPRG, NPRA and NORS are Not Supported
  [6:6] : 0x1   Multiple Atomicity Mode applies to write operations
  [5:4] : 0x3   NPWG, NPWA, NPDG, NPDGL, NPDA, and NOWS are Supported
{..}

Sequential atomic write workflows can benefit from the block layer
plug-merge as the following fio atomic write workload:

fio --name=atomic-merge --filename=/dev/nvme0n1 \
  --rw=write --bs=16k --size=64k \
  --ioengine=io_uring \
  --iodepth=4 --iodepth_batch_submit=4 \
  --atomic=1 --direct=1

The output below from btrace confirms the merging results into one
single command:

btrace /dev/nvme0n1
259,2    3        1     0.000000000  2725  Q  WS 0 + 32 [fio]
259,2    3        2     0.000003450  2725  G  WS 0 + 32 [fio]
259,2    3        3     0.000004250  2725  P   N [fio]
259,2    3        4     0.000005440  2725  Q  WS 32 + 32 [fio]
259,2    3        5     0.000006400  2725  M  WS 32 + 32 [fio]
259,2    3        6     0.000007360  2725  Q  WS 64 + 32 [fio]
259,2    3        7     0.000007490  2725  M  WS 64 + 32 [fio]
259,2    3        8     0.000008340  2725  Q  WS 96 + 32 [fio]
259,2    3        9     0.000008460  2725  M  WS 96 + 32 [fio]
259,2    3       10     0.000009270  2725  U   N [fio] 1
259,2    3       11     0.000013460  2725  D  WS 0 + 128 [fio]
259,2    3       12     0.000239642     0  C  WS 0 + 128 [0]

Link: https://lore.kernel.org/all/20260825-nvme-mam-v1-0-afc38ac713ef@samsung.com/ [1]
Link: https://kernel-recipes.org/en/2026/postgres-on-vs-with-linux/ [2]

Signed-off-by: Daniel Gomez <da.gomez@samsung.com>
---
Daniel Gomez (2):
      block: add BLK_FEAT_ATOMIC_WRITE_MULTI
      nvme: enable multiple atomicity mode

 block/blk-merge.c        |  9 ++++++++-
 block/blk-settings.c     |  5 +++++
 block/blk.h              |  6 +++++-
 drivers/nvme/host/core.c | 23 +++++++++++++++++++++++
 include/linux/blkdev.h   |  3 +++
 include/linux/nvme.h     |  1 +
 6 files changed, 45 insertions(+), 2 deletions(-)
---
base-commit: e680312dd3990197297b485e27b53c33d371c279
change-id: 20260929-nvme-mam-073f2ed13bdc

Best regards,
--  
Daniel Gomez <da.gomez@samsung.com>
```
