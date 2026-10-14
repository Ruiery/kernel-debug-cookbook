---
title: [PATCH blktests 0/5] nvme: tests for isolated CPUs and fabrics queue mapping
list: linux-block
message_id: 20261014-nvme-isolcpu-v1-0-2fd175a8ef00@kernel.org
link: https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-0-2fd175a8ef00@kernel.org/
---

# [PATCH blktests 0/5] nvme: tests for isolated CPUs and fabrics queue mapping

来源：[https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-0-2fd175a8ef00@kernel.org/](https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-0-2fd175a8ef00@kernel.org/)

```
New tests for the bugs fixed by the kernel series "nvme-fabrics: fix
connects with isolated CPUs and queue mapping bugs":

https://lore.kernel.org/linux-nvme/20261014-nvme-fabrics-isolcpu-v1-0-355156be27b2@kernel.org/

  nvme/070  connect with an isolated CPU (cpuset partition), verified
            I/O from a housekeeping and from the isolated CPU, traced on
            the queue of the isolated CPU
  nvme/071  more write and poll queues than online CPUs
  nvme/072  no queues left for polling
  nvme/073  reconnect with fewer I/O queues

nvme/071-073 need write and poll queues and only run for tcp and rdma.
Without the kernel series all four fail and nvme/073 crashes the kernel,
with the series they pass. Tested with loop and tcp.

Patch 1 stops _nvme_disconnect_ctrl() and _nvme_disconnect_subsys() from
truncating $FULL, which dropped everything logged before the disconnect,
e.g. the fio command lines.

Signed-off-by: Daniel Wagner <wagi@kernel.org>
---
Daniel Wagner (5):
      common/nvme: don't truncate the full log when disconnecting
      nvme/070: test connect with an isolated CPU
      nvme/071: test I/O queue limits per queue type
      nvme/072: test poll support without poll queues
      nvme/073: test reconnect with fewer I/O queues

 common/nvme        |   4 +-
 tests/nvme/070     | 196 +++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/nvme/070.out |   2 +
 tests/nvme/071     | 104 ++++++++++++++++++++++++++++
 tests/nvme/071.out |   2 +
 tests/nvme/072     |  85 +++++++++++++++++++++++
 tests/nvme/072.out |   2 +
 tests/nvme/073     | 117 ++++++++++++++++++++++++++++++++
 tests/nvme/073.out |   2 +
 9 files changed, 512 insertions(+), 2 deletions(-)
---
base-commit: 6f5a1dcb4551fe45c35e1fb1cdfa8343909f834a
change-id: 20261014-nvme-isolcpu-9f061e6a96ff

Best regards,
--  
Daniel Wagner <wagi@kernel.org>
```
