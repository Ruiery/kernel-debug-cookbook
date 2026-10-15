---
title: [PATCH v2 0/2] block: skip quiescing the queue for the default elevator
list: linux-block
message_id: 20261015-bug-block-elevator-init-quiesce-v2-0-505a2b0b1c07@gmail.com
link: https://lore.kernel.org/linux-block/20261015-bug-block-elevator-init-quiesce-v2-0-505a2b0b1c07@gmail.com/
---

# [PATCH v2 0/2] block: skip quiescing the queue for the default elevator

来源：[https://lore.kernel.org/linux-block/20261015-bug-block-elevator-init-quiesce-v2-0-505a2b0b1c07@gmail.com/](https://lore.kernel.org/linux-block/20261015-bug-block-elevator-init-quiesce-v2-0-505a2b0b1c07@gmail.com/)

```
Setting the default elevator of a new disk quiesces the queue, so every
disk added with a default elevator waits for an RCU grace period. Patch
1 skips the quiesce there, which brings START_DEV of a single-queue ublk
device from 7.74ms to 0.68ms at p50. Patch 2 renames a misleading label
in elevator_switch().

Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
V1 -> V2:
- Add Reviewed-by from Ming Lei and Nilay Shroff to patch 1.
- Rename out_unfreeze to out_unquiesce in a separate patch 2 (Nilay).
- Rebase onto for-7.4/block.

v1: https://lore.kernel.org/r/20261001-bug-block-elevator-init-quiesce-v1-1-5c85fa0ec59b@gmail.com

---
Qiliang Yuan (2):
      block: don't quiesce the queue when setting the default elevator
      block: rename the out_unfreeze label in elevator_switch()

 block/elevator.c | 11 +++++++----
 block/elevator.h |  2 ++
 2 files changed, 9 insertions(+), 4 deletions(-)
---
base-commit: 0f6b042f9a13968c4cd6cde1a70a7b242009ef46
change-id: 20260930-bug-block-elevator-init-quiesce-35d73f9b462d

Best regards,
-- 
Qiliang Yuan <odys.yuan@gmail.com>
```
