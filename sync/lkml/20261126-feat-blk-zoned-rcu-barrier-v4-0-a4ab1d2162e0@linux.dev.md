---
title: [PATCH v4 0/2] block: skip rcu_barrier() when releasing zoned disks
list: linux-block
message_id: 20261126-feat-blk-zoned-rcu-barrier-v4-0-a4ab1d2162e0@linux.dev
link: https://lore.kernel.org/linux-block/20261126-feat-blk-zoned-rcu-barrier-v4-0-a4ab1d2162e0@linux.dev/
---

# [PATCH v4 0/2] block: skip rcu_barrier() when releasing zoned disks

来源：[https://lore.kernel.org/linux-block/20261126-feat-blk-zoned-rcu-barrier-v4-0-a4ab1d2162e0@linux.dev/](https://lore.kernel.org/linux-block/20261126-feat-blk-zoned-rcu-barrier-v4-0-a4ab1d2162e0@linux.dev/)

```
Releasing a zoned disk calls rcu_barrier() before destroying its zone
write plug mempool, which waits for every RCU callback in the system.
Patch 1 calls it only when plugs of the disk still wait for RCU
freeing. Patch 2 frees the plugs left in the hash table directly, so
disks with partially written zones skip the wait as well.

Removing 32 zoned null_blk devices goes from 848 to 428 ms (-50%), and
from 865 to 433 ms (-50%) with four partially written zones on each.

Signed-off-by: Qiliang Yuan <qiliang.yuan@linux.dev>
---
V3 -> V4:
- Call rcu_barrier() only when plugs of the disk wait for RCU freeing,
  instead of wait_var_event(), which did not flush lazy RCU callbacks
  (Bart Van Assche)
- Add patch 2 to free the plugs left in the hash table directly at disk
  release (Bart Van Assche)
- Drop the Reviewed-by of Damien Le Moal from patch 1, the wait changed

V2 -> V3:
- Initialize nr_zone_wplugs_freeing in disk_init_zone_resources() (Damien Le Moal)

V1 -> V2:
- Keep the original comment above the wait (Damien Le Moal)
- Add Reviewed-by (Damien Le Moal)

v3: https://lore.kernel.org/r/20261125-feat-blk-zoned-rcu-barrier-v3-1-707f65bae05a@linux.dev
v2: https://lore.kernel.org/r/20261124-feat-blk-zoned-rcu-barrier-v2-1-6d2212a48c5c@linux.dev
v1: https://lore.kernel.org/r/20261121-feat-blk-zoned-rcu-barrier-v1-1-766875b525be@linux.dev

---
Qiliang Yuan (2):
      block: don't wait for all RCU callbacks when freeing zone write plugs
      block: free remaining zone write plugs directly on disk release

 block/blk-zoned.c      | 29 +++++++++++++++++++++++------
 include/linux/blkdev.h |  1 +
 2 files changed, 24 insertions(+), 6 deletions(-)
---
base-commit: 5f22fb20497f4983094131f00a734362300d22d2
change-id: 20261120-feat-blk-zoned-rcu-barrier-cb9044e67ab3

Best regards,
-- 
Qiliang Yuan <qiliang.yuan@linux.dev>
```
