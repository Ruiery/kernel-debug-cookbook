---
title: [PATCH 2/5] blk-mq: use a housekeeping CPU for passthrough requests on isolated hctxs
list: linux-block
message_id: 20261014-nvme-fabrics-isolcpu-v1-2-355156be27b2@kernel.org
link: https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-2-355156be27b2@kernel.org/
---

# [PATCH 2/5] blk-mq: use a housekeeping CPU for passthrough requests on isolated hctxs

来源：[https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-2-355156be27b2@kernel.org/](https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-2-355156be27b2@kernel.org/)

```
From: Daniel Wagner <wagi@kernel.org>

Since commit a46c27026da1 ("blk-mq: don't schedule block kworker on
isolated CPUs") isolated CPUs are removed from hctx->cpumask.  That
commit assumed the mask is only used for kworker placement and CPU
offline handling, but blk_mq_alloc_request_hctx uses it to pick the
software context of the request.  If only isolated CPUs are mapped to a
hardware context, the mask is empty and blk_mq_alloc_request_hctx fails
with -EXDEV, although the isolated CPUs still submit I/O to it.

The nvme fabrics transports allocate the Connect command for every I/O
queue this way, so connecting a controller fails with isolcpus=domain
or an isolated cpuset partition as soon as a hardware context only has
isolated CPUs.

Passthrough requests are inserted directly into hctx->dispatch, so
their software context only selects the CPU the completion runs on and
the hint for freeing the tag.  Use the software context of an online CPU
which is neither isolated from the scheduler domains nor from managed
interrupts for them.  Other requests and inactive hardware contexts
still fail.

Fixes: a46c27026da1 ("blk-mq: don't schedule block kworker on isolated CPUs")
Signed-off-by: Daniel Wagner <wagi@kernel.org>
---
 block/blk-mq.c | 37 +++++++++++++++++++++++++++++++++++--
 1 file changed, 35 insertions(+), 2 deletions(-)

diff --git a/block/blk-mq.c b/block/blk-mq.c
index a26a11c73ee3..79fb08400c48 100644
--- a/block/blk-mq.c
+++ b/block/blk-mq.c
@@ -697,6 +697,25 @@ struct request *blk_mq_alloc_request(struct request_queue *q, blk_opf_t opf,
 }
 EXPORT_SYMBOL(blk_mq_alloc_request);
 
+/*
+ * Return an online CPU which is neither isolated from the scheduler domains
+ * nor from managed interrupts, or nr_cpu_ids if there is none.
+ */
+static unsigned int blk_mq_housekeeping_cpu(void)
+{
+	unsigned int cpu;
+
+	rcu_read_lock();
+	for_each_online_cpu(cpu) {
+		if (!cpu_is_isolated(cpu) &&
+		    housekeeping_test_cpu(cpu, HK_TYPE_MANAGED_IRQ))
+			break;
+	}
+	rcu_read_unlock();
+
+	return cpu;
+}
+
 struct request *blk_mq_alloc_request_hctx(struct request_queue *q,
 	blk_opf_t opf, blk_mq_req_flags_t flags, unsigned int hctx_idx)
 {
@@ -747,8 +766,22 @@ struct request *blk_mq_alloc_request_hctx(struct request_queue *q,
 	if (!blk_mq_hw_queue_mapped(data.hctx))
 		goto out_queue_exit;
 	cpu = cpumask_first_and(data.hctx->cpumask, cpu_online_mask);
-	if (cpu >= nr_cpu_ids)
-		goto out_queue_exit;
+	if (cpu >= nr_cpu_ids) {
+		/*
+		 * Isolated CPUs are not part of hctx->cpumask, so it can be
+		 * empty although online CPUs are mapped to this hardware
+		 * context.  Passthrough requests are inserted directly into
+		 * hctx->dispatch, so use the software context of a
+		 * housekeeping CPU for them.  Inactive hardware contexts have
+		 * no online CPU left.
+		 */
+		if (!blk_op_is_passthrough(opf) ||
+		    test_bit(BLK_MQ_S_INACTIVE, &data.hctx->state))
+			goto out_queue_exit;
+		cpu = blk_mq_housekeeping_cpu();
+		if (cpu >= nr_cpu_ids)
+			goto out_queue_exit;
+	}
 	data.ctx = __blk_mq_get_ctx(q, cpu);
 
 	if (q->elevator)

-- 
2.56.0
```
