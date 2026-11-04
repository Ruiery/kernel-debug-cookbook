---
title: [PATCH blktests v2 0/6] nvme: tests for fabrics queue mapping and isolated or offline CPUs
list: linux-block
message_id: 20261104-nvme-isolcpu-v2-0-2d59f622a2c8@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-0-2d59f622a2c8@suse.de/
---

# [PATCH blktests v2 0/6] nvme: tests for fabrics queue mapping and isolated or offline CPUs

来源：[https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-0-2d59f622a2c8@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-0-2d59f622a2c8@suse.de/)

```
Connecting an NVMe over Fabrics controller fails or crashes the kernel
in several cases in current upstream. These tests reproduce each case
and verify the fix.

Queue mapping bugs, fixed in mainline:

  nvme/076  More write and poll queues than online CPUs requested. A
            queue type got more hardware contexts than online CPUs, a
            hardware context without CPU failed its Connect command with
            -EXDEV. Fixed by 99fd0cbae849 ("nvme-fabrics: limit each
            queue type to the number of online CPUs").
  nvme/077  No queues left for polling. The poll map kept the default
            mapping, the queue claimed poll support and polled I/O went
            to a queue which isn't a poll queue. Fixed by 36ede1aa85d5
            ("nvme-fabrics: clear the poll map if no poll queues are
            mapped").
  nvme/078  Reconnect with fewer I/O queues. Stale io_queues entries
            mapped the poll queues beyond the hardware contexts and
            blk_mq_map_swqueue crashed. Fixed by 9588769af5fc
            ("nvme-fabrics: reset io_queues before computing the queue
            mapping") and 36ede1aa85d5.

Hardware contexts without online CPU, fixed by the blk-mq patch "blk-mq:
allow passthrough requests on hctxs without online CPUs" (posted as v3,
the tests reference it as XXX). blk_mq_alloc_request_hctx fails with
-EXDEV if a hardware context has no online CPU in its mask, so the
Connect command for its I/O queue fails:

  nvme/079  Connect with an isolated CPU (cpuset isolated partition).
            Isolated CPUs are not part of hctx->cpumask since kernel
            commit a46c27026da1.
  nvme/080  Connect with offline CPUs. Offline CPUs are mapped to the
            hardware contexts since kernel commit 20e4d8139319.

Both check that the I/O of the isolated or onlined CPU goes through the
queue the connect failed on. Patch 4 adds the helpers to tests/nvme/rc
which trace the queue the commands are sent on.

nvme/076-078 need write and poll queues and only run for tcp and rdma.
nvme/080 needs CPU hotplug. Without the kernel fixes all five fail and
nvme/078 crashes the kernel, with the fixes they pass. Tested with loop
and tcp. nvme/076, nvme/079 and nvme/080 also pass against nvmet on
another machine with the nvme-target-control series, nvme/077 and
nvme/078 skip there because they change the local nvmet configfs.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
Changes in v2:
- Rebase on master and renumber the tests to nvme/076-080, the tests for
  the merged fixes first.
- Drop the common/nvme patch, master has the same fix (64cce9a).
- Reference the merged kernel commits in nvme/076-078.
- Add nvme/080 for connects with offline CPUs.
- Move the queue tracing of nvme/079 into tests/nvme/rc, nvme/080 uses
  it too.
- Fail instead of passing when the controller isn't ready after connect.
- Link to v1: https://patch.msgid.link/20261014-nvme-isolcpu-v1-0-2fd175a8ef00@kernel.org

---
Daniel Wagner (6):
      nvme/076: test I/O queue limits per queue type
      nvme/077: test poll support without poll queues
      nvme/078: test reconnect with fewer I/O queues
      nvme/rc: add helpers to count the commands on a queue
      nvme/079: test connect with an isolated CPU
      nvme/080: test connect with offline CPUs

 tests/nvme/076     | 106 ++++++++++++++++++++++++++++++++
 tests/nvme/076.out |   2 +
 tests/nvme/077     |  87 ++++++++++++++++++++++++++
 tests/nvme/077.out |   2 +
 tests/nvme/078     | 119 ++++++++++++++++++++++++++++++++++++
 tests/nvme/078.out |   2 +
 tests/nvme/079     | 176 +++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/nvme/079.out |   2 +
 tests/nvme/080     | 142 ++++++++++++++++++++++++++++++++++++++++++
 tests/nvme/080.out |   2 +
 tests/nvme/rc      |  33 ++++++++++
 11 files changed, 673 insertions(+)
---
base-commit: a65cf6bdca19cf98e80ba379bffbf3a67f86fba3
change-id: 20261014-nvme-isolcpu-9f061e6a96ff

Best regards,
--  
Daniel Wagner <dwagner@suse.de>
```
