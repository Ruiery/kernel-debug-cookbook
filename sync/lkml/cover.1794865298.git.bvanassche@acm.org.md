---
title: [PATCH 0/8] nbd: Defer request transmission to a workqueue
list: linux-block
message_id: cover.1794865298.git.bvanassche@acm.org
link: https://lore.kernel.org/linux-block/cover.1794865298.git.bvanassche@acm.org/
---

# [PATCH 0/8] nbd: Defer request transmission to a workqueue

来源：[https://lore.kernel.org/linux-block/cover.1794865298.git.bvanassche@acm.org/](https://lore.kernel.org/linux-block/cover.1794865298.git.bvanassche@acm.org/)

```
Hi Jens,

The NBD driver transmits requests over sockets owned by user space direct=
ly
from nbd_queue_rq(). Hence, sk_lock is acquired while blk-mq holds
q->q_usage_counter and set->srcu. Since other kernel code acquires sk_loc=
k
before fs_reclaim, mm->mmap_lock and other subsystem locks, syzbot report=
s
multiple circular locking dependencies. Socket lockdep reclassification, =
the
existing workaround, introduces new races and module reference count leak=
s,
and does not suppress all of these reports.

This patch series fixes these lockdep complaints by deferring request
transmission to a workqueue, similar to the loop driver, and by removing
the socket lockdep reclassification code. Since requests are no longer
transmitted from a context in which signals can be pending, the
partial-send handling code is removed.

This patch series is organized as follows:
- Patch 1 fixes a missing wakeup of wait_for_reconnect() callers when
  NBD_RT_DISCONNECTED is set.
- Patches 2 and 3 prepare for deferring request transmission by
  simplifying the nbd_send_cmd() return values and by no longer taking a
  config_refs reference for each request.
- Patch 4 defers request transmission to a workqueue.
- Patch 5 fixes a nsock->tx_lock -> cpu_hotplug_lock lockdep complaint.
- Patch 6 removes the socket lockdep reclassification code.
- Patches 7 and 8 remove the partial-send handling code that has become
  unreachable.

Please consider this patch series for the next merge window.

Thanks,

Bart.

Bart Van Assche (8):
  nbd: Wake up config->conn_wait when setting NBD_RT_DISCONNECTED
  nbd: Requeue requests directly in nbd_send_cmd()
  nbd: Stop taking a config_refs reference per request
  nbd: Defer request transmission to a workqueue
  nbd: Call sk_set_memalloc() outside nsock->tx_lock
  nbd: Remove socket lockdep reclassification
  nbd: Remove the partial-send handling
  nbd: Remove the sent argument of sock_xmit()

 drivers/block/nbd.c | 394 ++++++++++++++++----------------------------
 1 file changed, 142 insertions(+), 252 deletions(-)
```
