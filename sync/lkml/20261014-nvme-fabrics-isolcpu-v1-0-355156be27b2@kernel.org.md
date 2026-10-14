---
title: [PATCH 0/5] nvme-fabrics: fix connects with isolated CPUs and queue mapping bugs
list: linux-block
message_id: 20261014-nvme-fabrics-isolcpu-v1-0-355156be27b2@kernel.org
link: https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-0-355156be27b2@kernel.org/
---

# [PATCH 0/5] nvme-fabrics: fix connects with isolated CPUs and queue mapping bugs

来源：[https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-0-355156be27b2@kernel.org/](https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-0-355156be27b2@kernel.org/)

```
Connecting a fabrics controller fails when all CPUs of a hardware
context are isolated with isolcpus=domain or an isolated cpuset
partition. Since commit a46c27026da1 ("blk-mq: don't schedule block
kworker on isolated CPUs") the CPU mask of such a hardware context is
empty and blk_mq_alloc_request_hctx() fails the Connect command with
-EXDEV. Patch 2 lets passthrough requests use the software context of a
housekeeping CPU instead.

Patches 3-5 fix the fabrics queue mapping:

  - Stale io_queues[] entries after a reconnect with fewer queues crash
    blk_mq_map_swqueue().
  - A queue type can get more queues than online CPUs, so connecting
    fails with -EXDEV.
  - Without queues left for polling, the queue claims poll support and
    polled I/O ends up on a non-poll queue.

Patch 1 fixes a regression in nvme-7.4 found while testing: since commit
61b0ed3be81b ("nvme-tcp: parallelize I/O queue allocation and startup")
nvme_tcp_init_request takes a mutex before it is initialized, which
disables lock debugging on the first connect.

I found the fabrics queue setup problems while working on the isolcpus
series for the block layer, which Aaron Tomlin has since taken over and
which has not been merged yet. Maurizio Lombardi reported customer bugs
with isolcpus and nvme fabrics. This series doesn't depend on the block
layer work.

The bugs fixed by patches 3-5 predate commit a249d3066de6
("nvme-fabrics: add queue setup helpers"), which moved the tcp and rdma
code into fabrics.c, so kernels before v6.5 need manual backports.

Testing, QEMU with 8 CPUs, nvme-tcp and nvme-loop against nvmet:

  - isolcpus=managed_irq,domain,2-3: without the series, connecting
    with nr_io_queues=8, with and without nr_write_queues=8
    nr_poll_queues=8, fails on I/O queue 2, whose hardware context only
    has CPU 3. With the series connect and I/O work.
  - New blktests, posted separately:
      nvme/070  connect with an isolated CPU             -> patch 2
      nvme/071  more write and poll queues than CPUs     -> patch 4
      nvme/072  no queues left for polling               -> patch 5
      nvme/073  reconnect with fewer queues              -> patches 3, 5
    Without the series all fail, nvme/073 crashes the kernel. With the
    series all pass.
  - blktests block and nvme (loop, tcp): no regressions.

Reconnecting after all CPUs of a hardware context went offline still
fails, with and without this series: blk-mq marks the hardware context
inactive, but tcp, rdma and loop connect the I/O queues before updating
the CPU mapping. I'll fix this separately, together with moving the
fabrics reconnect sequence into common code.

Signed-off-by: Daniel Wagner <wagi@kernel.org>
---
Daniel Wagner (5):
      nvme-tcp: initialize pf_cache_lock when allocating the controller
      blk-mq: use a housekeeping CPU for passthrough requests on isolated hctxs
      nvme-fabrics: reset io_queues before computing the queue mapping
      nvme-fabrics: limit each queue type to the number of online CPUs
      nvme-fabrics: clear the poll map if no poll queues are mapped

 block/blk-mq.c              | 37 +++++++++++++++++++++++++++++++++++--
 drivers/nvme/host/fabrics.c | 30 ++++++++++++++++++++++++------
 drivers/nvme/host/tcp.c     | 13 +++++++++----
 3 files changed, 68 insertions(+), 12 deletions(-)
---
base-commit: 31b8a6af19b73e6167c4b655cd5e86681bac1c41
change-id: 20261013-nvme-fabrics-isolcpu-5b4948362f88

Best regards,
--  
Daniel Wagner <wagi@kernel.org>
```
