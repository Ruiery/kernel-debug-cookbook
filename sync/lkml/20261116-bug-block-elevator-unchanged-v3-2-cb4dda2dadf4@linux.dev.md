---
title: [PATCH v3 2/2] block: return early when the elevator doesn't change
list: linux-block
message_id: 20261116-bug-block-elevator-unchanged-v3-2-cb4dda2dadf4@linux.dev
link: https://lore.kernel.org/linux-block/20261116-bug-block-elevator-unchanged-v3-2-cb4dda2dadf4@linux.dev/
---

# [PATCH v3 2/2] block: return early when the elevator doesn't change

来源：[https://lore.kernel.org/linux-block/20261116-bug-block-elevator-unchanged-v3-2-cb4dda2dadf4@linux.dev/](https://lore.kernel.org/linux-block/20261116-bug-block-elevator-unchanged-v3-2-cb4dda2dadf4@linux.dev/)

```
Writing the scheduler a queue already uses to queue/scheduler used to
be a no-op. elevator_change() now only checks for an unchanged elevator
after freezing the queue, and doesn't treat "none" on a queue without
an elevator as unchanged at all, so that case also quiesces the queue
in elevator_switch() and resets nr_requests.

Every such write therefore drains in-flight I/O and waits for an RCU
grace period. udev rules and tuning tools that set the scheduler
unconditionally stall I/O on live disks each time they run.

Check under elevator_lock whether anything would change before
allocating scheduler resources and freezing the queue. The check can
race with another elevator change, which at worst leads to a redundant
switch, so keep the one done under the freeze as well.

Writing the current scheduler to queue/scheduler of a null_blk disk 20
times takes (median):

  operation                 before (ms)  after (ms)  change
  none -> none                     9.11        0.08    -99%
  mq-deadline -> mq-deadline       9.05        0.08    -99%

4k random reads at queue depth 1 for 10 seconds, while "none" is
written to queue/scheduler every 50 ms:

  metric             before  after  change
  IOPS               340562 390392    +15%
  max latency (us)    16302   1224    -92%

Fixes: af2814149883e ("block: freeze the queue in queue_attr_store")
Signed-off-by: Qiliang Yuan <qiliang.yuan@linux.dev>
Reviewed-by: Christoph Hellwig <hch@lst.de>
---
 block/elevator.c | 14 ++++++++++++++
 1 file changed, 14 insertions(+)

diff --git a/block/elevator.c b/block/elevator.c
index 9d9b2e84a1288..549cf51543a8b 100644
--- a/block/elevator.c
+++ b/block/elevator.c
@@ -654,10 +654,24 @@ static int elevator_change(struct request_queue *q, struct elv_change_ctx *ctx)
 {
 	unsigned int memflags;
 	struct blk_mq_tag_set *set = q->tag_set;
+	bool unchanged;
 	int ret = 0;
 
 	lockdep_assert_held(&set->update_nr_hwq_lock);
 
+	/*
+	 * Skip freezing the queue if nothing would change. This can race with
+	 * another elevator change, which at worst leads to a redundant switch.
+	 */
+	mutex_lock(&q->elevator_lock);
+	if (q->elevator)
+		unchanged = elevator_match(q->elevator->type, ctx->name);
+	else
+		unchanged = !strncmp(ctx->name, "none", 4);
+	mutex_unlock(&q->elevator_lock);
+	if (unchanged)
+		return 0;
+
 	if (strncmp(ctx->name, "none", 4)) {
 		ret = blk_mq_alloc_sched_res(q, ctx->type, &ctx->res,
 				set->nr_hw_queues);

-- 
2.43.0
```
