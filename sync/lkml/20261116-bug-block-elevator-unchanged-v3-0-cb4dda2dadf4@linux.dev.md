---
title: [PATCH v3 0/2] block: make changing to the current I/O scheduler cheap again
list: linux-block
message_id: 20261116-bug-block-elevator-unchanged-v3-0-cb4dda2dadf4@linux.dev
link: https://lore.kernel.org/linux-block/20261116-bug-block-elevator-unchanged-v3-0-cb4dda2dadf4@linux.dev/
---

# [PATCH v3 0/2] block: make changing to the current I/O scheduler cheap again

来源：[https://lore.kernel.org/linux-block/20261116-bug-block-elevator-unchanged-v3-0-cb4dda2dadf4@linux.dev/](https://lore.kernel.org/linux-block/20261116-bug-block-elevator-unchanged-v3-0-cb4dda2dadf4@linux.dev/)

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
  none -> none                    13.10          9.11            0.08
  mq-deadline -> mq-deadline      10.95          9.05            0.08
  mq-deadline -> none             13.00          7.97            6.03

Signed-off-by: Qiliang Yuan <qiliang.yuan@linux.dev>
---
V2 -> V3:
- Point Fixes in patch 2 at the commit that added the freeze, as
  Christoph pointed out
- Add Christoph's Reviewed-by to patch 2
- Rebase onto v7.4-rc2-1025-g666539eecdf4

V1 -> V2:
- Keep the elevator check under the freeze and note the race in the
  comment, as Christoph suggested
- Say "change" instead of "rewrite" in the cover letter subject
- Rebase onto v7.4-rc2-470-g7e1392a42ea2 and update the numbers from a
  new run

v2: https://lore.kernel.org/r/20261114-bug-block-elevator-unchanged-v2-0-5a1fe7d72fa0@linux.dev
v1: https://lore.kernel.org/r/20261111-bug-block-elevator-unchanged-v1-0-583198bd4e21@linux.dev

---
Qiliang Yuan (2):
      block: don't request a module for the none elevator
      block: return early when the elevator doesn't change

 block/elevator.c | 17 +++++++++++++++++
 1 file changed, 17 insertions(+)
---
base-commit: 666539eecdf4db623f5e3c3e55cf9f2dfad24aa4
change-id: 20261111-bug-block-elevator-unchanged-a6cd2d761d38

Best regards,
-- 
Qiliang Yuan <qiliang.yuan@linux.dev>
```
