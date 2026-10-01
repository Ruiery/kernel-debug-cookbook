---
title: [PATCH 0/2] blk-mq: stop waiting for an SRCU grace period when freeing a tag set
list: linux-block
message_id: 20261001-bug-blk-mq-global-tags-srcu-v1-0-e8415da10d1b@gmail.com
link: https://lore.kernel.org/linux-block/20261001-bug-blk-mq-global-tags-srcu-v1-0-e8415da10d1b@gmail.com/
---

# [PATCH 0/2] blk-mq: stop waiting for an SRCU grace period when freeing a tag set

来源：[https://lore.kernel.org/linux-block/20261001-bug-blk-mq-global-tags-srcu-v1-0-e8415da10d1b@gmail.com/](https://lore.kernel.org/linux-block/20261001-bug-blk-mq-global-tags-srcu-v1-0-e8415da10d1b@gmail.com/)

```
blk_mq_free_tag_set() calls srcu_barrier() on the tag set's own
tags_srcu before cleaning it up. That costs a full SRCU grace period,
1-3 ms, on every tag set teardown. When the free happens under a lock,
the cost multiplies. ublk drops its last device reference under the
global ublk_ctl_mutex, which caps 16-thread deletion of 4000 devices at
19 s on 7.3-rc5.

The SRCU callbacks free only blk-mq-owned memory and never touch the
tag set, so patch 1 makes the SRCU instance global and drops the
per-set barrier and cleanup. Patch 2 removes the tag_set argument that
was added to blk_mq_free_rq_map() and blk_mq_free_tags() only to reach
the per-set instance.

With patch 1, 16-thread deletion of 4000 ublk devices takes 2.9 s and
serial DEL_DEV drops from 3.45 ms to 0.17 ms. Destroying 256 null_blk
devices from 16 threads goes from 5.15 s to 4.30 s.

Tested on 7.3-rc5 with ublk and null_blk create/destroy loops. A
KASAN + lockdep + DEBUG_OBJECTS_RCU_HEAD kernel ran a 10-minute stress
that raced device creation and destruction, I/O, scheduler and
nr_requests changes, and CPU hotplug against inflight, debugfs busy and
tags readers. It produced no reports.

Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
Qiliang Yuan (2):
      blk-mq: share one tags_srcu instance across all tag sets
      blk-mq: drop the tag_set argument from blk_mq_free_rq_map/tags

 block/blk-mq-tag.c     | 19 +++++++++++++------
 block/blk-mq.c         | 25 +++++++++----------------
 block/blk-mq.h         |  6 ++++--
 include/linux/blk-mq.h |  3 ---
 4 files changed, 26 insertions(+), 27 deletions(-)
---
base-commit: 551c722f40809618230001baccf219193e22fc5a
change-id: 20261001-bug-blk-mq-global-tags-srcu-811e8d958281

Best regards,
-- 
Qiliang Yuan <odys.yuan@gmail.com>
```
