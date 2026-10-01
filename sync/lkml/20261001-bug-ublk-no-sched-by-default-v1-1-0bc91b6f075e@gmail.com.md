---
title: [PATCH] ublk: don't use an I/O scheduler by default
list: linux-block
message_id: 20261001-bug-ublk-no-sched-by-default-v1-1-0bc91b6f075e@gmail.com
link: https://lore.kernel.org/linux-block/20261001-bug-ublk-no-sched-by-default-v1-1-0bc91b6f075e@gmail.com/
---

# [PATCH] ublk: don't use an I/O scheduler by default

来源：[https://lore.kernel.org/linux-block/20261001-bug-ublk-no-sched-by-default-v1-1-0bc91b6f075e@gmail.com/](https://lore.kernel.org/linux-block/20261001-bug-ublk-no-sched-by-default-v1-1-0bc91b6f075e@gmail.com/)

```
Requests of a ublk device are handed to the ublk server through
io_uring, and the server does its own queueing and ordering, so an I/O
scheduler in front of the device only adds overhead. A single-queue
ublk device still gets mq-deadline by default, which costs throughput
on every I/O and an elevator setup on every START_DEV.

Set BLK_MQ_F_NO_SCHED_BY_DEFAULT so that add_disk() selects "none", as
loop does since commit 2112f5c1330a ("loop: Select I/O scheduler 'none'
from inside add_disk()"). Doing it in the kernel also avoids switching
the scheduler from user space after the device has been added, which
waits for RCU grace periods. A scheduler can still be selected through
sysfs. Zoned ublk devices don't need mq-deadline either, zone write
plugging serializes writes per zone in the block layer since
commit fde02699c242 ("block: mq-deadline: Remove support for zone write
locking").

ublk null target, single-queue devices with depth 16, fio io_uring 4k
randread at iodepth=16, 16 vCPU KVM guest:

                                 mq-deadline       none
  1 device                          111K IOPS   342K IOPS
  4 devices                         286K IOPS  1070K IOPS
  START_DEV p50 (1000 devices)        8.53ms      0.36ms

Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
Zoned ublk devices were not tested at runtime: none of the ublk servers
at hand (ublksrv, the kublk selftest server) serves zoned I/O.
---
 drivers/block/ublk_drv.c | 1 +
 1 file changed, 1 insertion(+)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 66eb55e7162e5..8053666c04482 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -4389,6 +4389,7 @@ static int ublk_add_tag_set(struct ublk_device *ub)
 	ub->tag_set.nr_hw_queues = ub->dev_info.nr_hw_queues;
 	ub->tag_set.queue_depth = ub->dev_info.queue_depth;
 	ub->tag_set.numa_node = NUMA_NO_NODE;
+	ub->tag_set.flags = BLK_MQ_F_NO_SCHED_BY_DEFAULT;
 	ub->tag_set.driver_data = ub;
 	return blk_mq_alloc_tag_set(&ub->tag_set);
 }

---
base-commit: 551c722f40809618230001baccf219193e22fc5a
change-id: 20261001-bug-ublk-no-sched-by-default-6f53fa4889e6

Best regards,
-- 
Qiliang Yuan <odys.yuan@gmail.com>
```
