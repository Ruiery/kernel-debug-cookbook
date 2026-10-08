---
title: [PATCH 0/2] selftests: ublk: fix the fault_inject delay
list: linux-block
message_id: 20261008-bug-ublk-selftest-fault-inject-delay-v1-0-a96af7ead06e@gmail.com
link: https://lore.kernel.org/linux-block/20261008-bug-ublk-selftest-fault-inject-delay-v1-0-a96af7ead06e@gmail.com/
---

# [PATCH 0/2] selftests: ublk: fix the fault_inject delay

来源：[https://lore.kernel.org/linux-block/20261008-bug-ublk-selftest-fault-inject-delay-v1-0-a96af7ead06e@gmail.com/](https://lore.kernel.org/linux-block/20261008-bug-ublk-selftest-fault-inject-delay-v1-0-a96af7ead06e@gmail.com/)

```
The delay set by --delay_us on the fault_inject target is lost in two
ways. Its timespec is read after it has gone out of scope, which makes
generic_06 fail, and any other completion on the ring ends it early when
more than one I/O is in flight. Patch 1 keeps the timespec alive until
the SQE is submitted, and patch 2 makes the delay a pure timeout.

With both patches, a 1 s delay holds every I/O for 1.000 s at queue
depth 4.

Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
Qiliang Yuan (2):
      selftests: ublk: don't keep the fault_inject timespec on the stack
      selftests: ublk: make the fault_inject delay a pure timeout

 tools/testing/selftests/ublk/fault_inject.c | 14 ++++++++------
 1 file changed, 8 insertions(+), 6 deletions(-)
---
base-commit: e1274a6bc40a4618f6fbaebbdc51cca865d51bed
change-id: 20261008-bug-ublk-selftest-fault-inject-delay-46ea414ba226

Best regards,
-- 
Qiliang Yuan <odys.yuan@gmail.com>
```
