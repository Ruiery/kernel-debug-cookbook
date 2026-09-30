---
title: [PATCH] blk-mq: run the hw queue synchronously for unplugged scheduler inserts
list: linux-block
message_id: 20260930-bug-blk-mq-noplug-sched-dispatch-v1-1-ff1e49e52b00@gmail.com
link: https://lore.kernel.org/linux-block/20260930-bug-blk-mq-noplug-sched-dispatch-v1-1-ff1e49e52b00@gmail.com/
---

# [PATCH] blk-mq: run the hw queue synchronously for unplugged scheduler inserts

来源：[https://lore.kernel.org/linux-block/20260930-bug-blk-mq-noplug-sched-dispatch-v1-1-ff1e49e52b00@gmail.com/](https://lore.kernel.org/linux-block/20260930-bug-blk-mq-noplug-sched-dispatch-v1-1-ff1e49e52b00@gmail.com/)

```
When the submitter holds no plug, blk_mq_submit_bio() inserts a request
into the I/O scheduler and runs the hardware queue asynchronously. Now
that __submit_bio() no longer opens a plug around every bio, this path
is taken by all unplugged I/O to devices with an elevator, such as
io_uring submitting at most two SQEs per io_uring_enter() or synchronous
O_DIRECT reads and writes.

Each of these requests queues hctx->run_work on kblockd. kblockd is a
per-CPU WQ_HIGHPRI workqueue and blk_mq_hctx_next_cpu() returns
WORK_CPU_UNBOUND for single-queue devices, so the work runs on the
submitting CPU and the kworker preempts the submitter once per I/O.
With fio (io_uring, 4k randread, iodepth=16, one job) the submitter
context switches about once per I/O. A single-queue null_blk device
with mq-deadline drops from 289K to 193K IOPS, and a single-queue ublk
device, which defaults to mq-deadline, drops from 265K to 113K IOPS.

Run the hardware queue from the submitting context for scheduler
inserts, as flushing the per-bio plug did. Keep the asynchronous run for
the hctx->dispatch_busy case.

fio, io_uring, 4k randread, 16 vCPU KVM guest:

                                                  before     after
  null_blk, 1 queue, mq-deadline, qd16              193K      289K
  null_blk, 1 queue, none, qd16                     354K      356K
  null_blk, 4 queues, none, qd1                     356K      358K
  ublk (ublksrv null), 1 queue, mq-deadline, qd16   113K      265K
  ublk (ublksrv null), 4 x 1-queue devices, qd16    290K      852K

Fixes: 9cbbac29d752 ("block: Remove redundant plug in __submit_bio()")
Cc: stable@vger.kernel.org
Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
 block/blk-mq.c | 12 ++++++++++--
 1 file changed, 10 insertions(+), 2 deletions(-)

diff --git a/block/blk-mq.c b/block/blk-mq.c
index a26a11c73ee3e..54eff3cf45fae 100644
--- a/block/blk-mq.c
+++ b/block/blk-mq.c
@@ -3200,8 +3200,16 @@ void blk_mq_submit_bio(struct bio *bio)
 	}
 
 	hctx = rq->mq_hctx;
-	if ((rq->rq_flags & RQF_USE_SCHED) ||
-	    (hctx->dispatch_busy && (q->nr_hw_queues == 1 || !is_sync))) {
+	if (rq->rq_flags & RQF_USE_SCHED) {
+		/*
+		 * Run the queue from the submitting context, as flushing a plug
+		 * does. Punting every unplugged request to kblockd lets the
+		 * kworker preempt the submitter once per I/O.
+		 */
+		blk_mq_insert_request(rq, 0);
+		blk_mq_run_hw_queue(hctx, false);
+	} else if (hctx->dispatch_busy &&
+		   (q->nr_hw_queues == 1 || !is_sync)) {
 		blk_mq_insert_request(rq, 0);
 		blk_mq_run_hw_queue(hctx, true);
 	} else {

---
base-commit: 551c722f40809618230001baccf219193e22fc5a
change-id: 20260930-bug-blk-mq-noplug-sched-dispatch-4f19360b0bf7

Best regards,
-- 
Qiliang Yuan <odys.yuan@gmail.com>
```
