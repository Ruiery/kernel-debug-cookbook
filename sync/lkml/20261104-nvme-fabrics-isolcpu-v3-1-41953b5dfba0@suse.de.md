---
title: [PATCH v3] blk-mq: allow passthrough requests on hctxs without online CPUs
list: linux-block
message_id: 20261104-nvme-fabrics-isolcpu-v3-1-41953b5dfba0@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-fabrics-isolcpu-v3-1-41953b5dfba0@suse.de/
---

# [PATCH v3] blk-mq: allow passthrough requests on hctxs without online CPUs

来源：[https://lore.kernel.org/linux-block/20261104-nvme-fabrics-isolcpu-v3-1-41953b5dfba0@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-fabrics-isolcpu-v3-1-41953b5dfba0@suse.de/)

```
blk_mq_alloc_request_hctx() picks the first online CPU in hctx->cpumask
to find a software context for the request. If no CPU in the mask is
online, allocation fails with -EXDEV.

This triggers in two scenarios:

 1. Commit 20e4d8139319 ("blk-mq: simplify queue mapping & schedule with
    each possisble CPU") maps all possible CPUs to hardware contexts. If
    certain CPUs are offline (e.g. booted with maxcpus= or offlined via
    sysfs), a hardware context may end up mapped entirely to offline CPUs.

 2. Commit a46c27026da1 ("blk-mq: don't schedule block kworker on
    isolated CPUs") strips isolated CPUs from hctx->cpumask. If an hctx
    is mapped exclusively to isolated CPUs (isolcpus=domain or an isolated
    cpuset partition), hctx->cpumask ends up empty.

NVMe fabrics transports allocate the Connect command for each I/O queue
using blk_mq_alloc_request_hctx(). If an hctx only maps offline or
isolated CPUs, connecting to the controller fails. Skipping these queues
is not an option because isolated CPUs still submit I/O through them,
as will offline CPUs once brought online.

Passthrough requests bypass the software staging queues and dispatch
directly. For these requests, the software context only serves to pick
a completion CPU and provide a hint when releasing the tag.

Fall back to an online housekeeping CPU's software context when allocating
passthrough requests on an hctx without an online CPU in its mask.

Hardware contexts whose last online CPU went offline are inactive.
blk-mq drained them for the CPU offline, so allocations on them still
fail.

Fixes: 20e4d8139319 ("blk-mq: simplify queue mapping & schedule with each possisble CPU")
Fixes: a46c27026da1 ("blk-mq: don't schedule block kworker on isolated CPUs")
Tested-by: Maurizio Lombardi <mlombard@redhat.com>
Reviewed-by: Aaron Tomlin <atomlin@atomlin.com>
Reviewed-by: Nilay Shroff <nilay@linux.ibm.com>
Reviewed-by: Christoph Hellwig <hch@lst.de>
Reviewed-by: Sebastian Andrzej Siewior <bigeasy@linutronix.de>
Reviewed-by: Hannes Reinecke <hare@kernel.org>
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
Connecting an NVMe over Fabrics controller fails in current upstream if
a hardware context has no online CPU in its CPU mask, which happens with
isolated and with offline CPUs. The commit message explains both cases.

Testing, QEMU VM with 8 CPUs, nvme-loop and nvme-tcp against nvmet in
the same VM, nvme-tcp also against nvmet in a second VM:

  - Isolated CPU: blktests nvme/079 fails without the patch and passes
    with it.
  - Offline CPUs: booted with maxcpus=4, the connect fails with -EXDEV
    on I/O queues 3 and 4 without the patch. With the patch the connect
    works, also I/O from the CPUs after bringing them online. blktests
    nvme/080 fails without the patch and passes with it.

The blktests are posted separately.
---
Changes in v3:
- Same code as v2, update the code comment and the commit message.
  Sashiko pointed out that the patch also allocates on hardware
  contexts mapped only to offline CPUs. This is intended: connecting
  fails in current upstream while CPUs are offline too, since commit
  20e4d8139319, so add it as a second Fixes tag.
- Link to v2: https://patch.msgid.link/20261103-nvme-fabrics-isolcpu-v2-1-95ec70d58254@suse.de

Changes in v2:
- Only the blk-mq patch left, the nvme patches are in nvme-7.4.
- Reword the commit message to describe what the fix does (Hannes).
- Add Tested-by from Maurizio.
- Link to v1: https://patch.msgid.link/20261014-nvme-fabrics-isolcpu-v1-0-355156be27b2@kernel.org
---
 block/blk-mq.c | 39 +++++++++++++++++++++++++++++++++++++--
 1 file changed, 37 insertions(+), 2 deletions(-)

diff --git a/block/blk-mq.c b/block/blk-mq.c
index 5fca78778c31..c87f2d597126 100644
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
@@ -767,8 +786,24 @@ struct request *blk_mq_alloc_request_hctx(struct request_queue *q,
 	if (!blk_mq_hw_queue_mapped(data.hctx))
 		goto out_queue_exit;
 	cpu = cpumask_first_and(data.hctx->cpumask, cpu_online_mask);
-	if (cpu >= nr_cpu_ids)
-		goto out_queue_exit;
+	if (cpu >= nr_cpu_ids) {
+		/*
+		 * Only isolated or offline CPUs are mapped to this hardware
+		 * context. Isolated CPUs are not part of hctx->cpumask, and
+		 * offline CPUs may come online later and need the hardware
+		 * context then. Passthrough requests are inserted directly
+		 * into hctx->dispatch, so use the software context of a
+		 * housekeeping CPU for them. Inactive hardware contexts lost
+		 * their last online CPU and were drained for the CPU offline,
+		 * don't allocate requests on them.
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
