---
title: [PATCH 0/2] block: make rewriting the current I/O scheduler cheap again
list: linux-block
message_id: 20261111-bug-block-elevator-unchanged-v1-0-583198bd4e21@linux.dev
link: https://lore.kernel.org/linux-block/20261111-bug-block-elevator-unchanged-v1-0-583198bd4e21@linux.dev/
---

# [PATCH 0/2] block: make rewriting the current I/O scheduler cheap again

来源：[https://lore.kernel.org/linux-block/20261111-bug-block-elevator-unchanged-v1-0-583198bd4e21@linux.dev/](https://lore.kernel.org/linux-block/20261111-bug-block-elevator-unchanged-v1-0-583198bd4e21@linux.dev/)

```
Writing the scheduler a queue already uses to queue/scheduler takes
about 10 ms and freezes the queue, which stalls I/O on live disks every
time a udev rule or tuning tool sets the scheduler unconditionally.

Patch 1 stops requesting a "none-iosched" module on every write of
"none". Patch 2 returns before freezing the queue when the elevator
wouldn't change.

On a null_blk disk (median of 20 writes, all kernels measured in the
same run):

  operation                   base (ms)  patch 1 (ms)  patch 1+2 (ms)
  none -> none                    13.09          9.06            0.08
  mq-deadline -> mq-deadline       9.19          9.14            0.08
  mq-deadline -> none             12.00          7.96            7.97

Signed-off-by: Qiliang Yuan <qiliang.yuan@linux.dev>
---
Qiliang Yuan (2):
      block: don't request a module for the none elevator
      block: return early when the elevator doesn't change

 block/elevator.c | 20 ++++++++++++++++++--
 1 file changed, 18 insertions(+), 2 deletions(-)
---
base-commit: 79eb6679ef6a0d5ea68da53a8321fb1dc72299b9
change-id: 20261111-bug-block-elevator-unchanged-a6cd2d761d38

Best regards,
-- 
Qiliang Yuan <qiliang.yuan@linux.dev>
```
