---
title: [PATCH v2] blk-mq: use a housekeeping CPU for passthrough requests on isolated hctxs
list: linux-block
message_id: 20261103-nvme-fabrics-isolcpu-v2-1-95ec70d58254@suse.de
link: https://lore.kernel.org/linux-block/20261103-nvme-fabrics-isolcpu-v2-1-95ec70d58254@suse.de/
---

# [PATCH v2] blk-mq: use a housekeeping CPU for passthrough requests on isolated hctxs

来源：[https://lore.kernel.org/linux-block/20261103-nvme-fabrics-isolcpu-v2-1-95ec70d58254@suse.de/](https://lore.kernel.org/linux-block/20261103-nvme-fabrics-isolcpu-v2-1-95ec70d58254@suse.de/)

```
blk_mq_alloc_request_hctx uses the first online CPU in hctx->cpumask to
select the software context for a request.

Since commit a46c27026da1 ("blk-mq: don't schedule block kworker on
isolated CPUs"), hctx->cpumask excludes isolated CPUs. If a hardware
context is mapped only to isolated CPUs, the mask is empty and
blk_mq_alloc_request_hctx fails with -EXDEV.

The NVMe fabrics transports use blk_mq_alloc_request_hctx to allocate
the Connect command for each I/O queue. As a result, connecting to a
controller can fail when using isolcpus=domain or an isolated cpuset
partition.

Passthrough requests bypass the software queues and go directly to
hctx->dispatch. Their software context is only used to select the
completion CPU and as a hint when freeing the tag.

Use the software context of an online housekeeping CPU for passthrough
requests.

Fixes: a46c27026da1 ("blk-mq: don't schedule block kworker on isolated CPUs")
Tested-by: Maurizio Lombardi <mlombard@redhat.com>
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
Connecting a fabrics controller fails when all CPUs of a hardware
context are isolated with isolcpus=domain or an isolated cpuset
partition. Since commit a46c27026da1 ("blk-mq: don't schedule block
kworker on isolated CPUs") the CPU mask of such a hardware context is
empty and blk_mq_alloc_request_hctx() fails the Connect command with
-EXDEV. This patch lets passthrough requests use the software context
of a housekeeping CPU instead.

The nvme fabrics fixes from v1 (patches 1 and 3-5) are in nvme-7.4, so
only the blk-mq patch is left. The blktest for this patch is nvme/070,
posted separately.
---
Changes in v2:
- Only the blk-mq patch left, the nvme patches are in nvme-7.4.
- Reword the commit message to describe what the fix does (Hannes).
- Add Tested-by from Maurizio.
- Link to v1: https://patch.msgid.link/20261014-nvme-fabrics-isolcpu-v1-0-355156be27b2@kernel.org
---
 block/blk-mq.c | 37 +++++++++++++++++++++++++++++++++++--
 1 file changed, 35 insertions(+), 2 deletions(-)

diff --git a/block/blk-mq.c b/block/blk-mq.c
index 5fca78778c31..77685e6283fa 100644
--- a/block/blk-mq.c
+++ b/block/blk-mq.c
@@ -717,6 +717,25 @@ struct request *blk_mq_alloc_request(struct request_queue *q, blk_opf_t opf,
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
@@ -767,8 +786,22 @@ struct request *blk_mq_alloc_request_hctx(struct request_queue *q,
 	if (!blk_mq_hw_queue_mapped(data.hctx))
 		goto out_queue_exit;
 	cpu = cpumask_first_and(data.hctx->cpumask, cpu_online_mask);
-	if (cpu >= nr_cpu_ids)
-		goto out_queue_exit;
+	if (cpu >= nr_cpu_ids) {
+		/*
+		 * Isolated CPUs are not part of hctx->cpumask, so it can be
+		 * empty although online CPUs are mapped to this hardware
+		 * context. Passthrough requests are inserted directly into
+		 * hctx->dispatch, so use the software context of a
+		 * housekeeping CPU for them. Inactive hardware contexts have
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

---
base-commit: c8c53d669d4e45b3a804013251a34387d7e11bfb
change-id: 20261013-nvme-fabrics-isolcpu-5b4948362f88

Best regards,
--  
Daniel Wagner <dwagner@suse.de>
```
