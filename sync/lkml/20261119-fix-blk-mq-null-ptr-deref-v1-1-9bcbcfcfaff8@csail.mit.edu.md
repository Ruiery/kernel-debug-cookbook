---
title: [PATCH] block: Fix NULL pointer dereference in blk_mq_complete_request_remote
list: linux-block
message_id: 20261119-fix-blk-mq-null-ptr-deref-v1-1-9bcbcfcfaff8@csail.mit.edu
link: https://lore.kernel.org/linux-block/20261119-fix-blk-mq-null-ptr-deref-v1-1-9bcbcfcfaff8@csail.mit.edu/
---

# [PATCH] block: Fix NULL pointer dereference in blk_mq_complete_request_remote

来源：[https://lore.kernel.org/linux-block/20261119-fix-blk-mq-null-ptr-deref-v1-1-9bcbcfcfaff8@csail.mit.edu/](https://lore.kernel.org/linux-block/20261119-fix-blk-mq-null-ptr-deref-v1-1-9bcbcfcfaff8@csail.mit.edu/)

```
Add NULL pointer validation in blk_mq_complete_request_remote() to
prevent kernel crashes when block drivers pass freed request structures.

When NVMe devices experience hardware failures or firmware bugs,
completion queue corruption can occur, leading to scenarios where
drivers attempt to complete already-freed requests. The NVMe genctr
validation in nvme_find_rq() catches most stale completions, but when
corruption produces a command_id whose genctr bits happen to match,
the freed request passes validation and reaches the block layer. The
block layer's __blk_mq_free_request() sets rq->mq_hctx to NULL,
but blk_mq_complete_request_remote() lacks validation before
dereferencing this pointer.

This manifests as a kernel crash like shown below (the stack trace
was obtained from a crash observed in a Linux VM on Hyper-V):

  nvme nvme0: resetting controller due to AER
  nvme nvme0: request 0xe3 genctr mismatch (got 0x0 expected 0x5)
  nvme nvme0: invalid id 227 completed on queue 6
  nvme nvme0: request 0x26 genctr mismatch (got 0xb expected 0x9)
  nvme nvme0: invalid id 45094 completed on queue 94

  BUG: kernel NULL pointer dereference, address: 00000000000000fe
  RIP: 0010:blk_mq_complete_request_remote+0x1b/0x150
  Call Trace:
   <IRQ>
   nvme_irq+0x182/0x320 [nvme]
   __handle_irq_event_percpu+0x47/0x180
   handle_irq_event+0x38/0x60
   handle_edge_irq+0x87/0x1a0
   __common_interrupt+0x3f/0xa0
   common_interrupt+0x42/0xa0

The crash occurs at offset 0xfe when accessing rq->mq_hctx->nr_ctx,
where mq_hctx is NULL.

Add a NULL check that returns true (signaling to callers that the
request has been handled) to gracefully drop freed requests, with a
WARN_ONCE to flag the condition for diagnosis.

Fixes: 40d09b53bfc5 ("blk-mq: add a new blk_mq_complete_request_remote API")
Signed-off-by: Srivatsa S. Bhat (Microsoft) <srivatsa@csail.mit.edu>
---
I'd like to call out a few unresolved aspects about this patch for
review attention:

1. I'm not sure if the NULL ptr check should be placed before or after
the rq->state update to MQ_RQ_COMPLETE. Do we need to update that
state even if we don't proceed with the complete-request operation?

2. While this was a real bug that I hit in one of my systems, I don't
have a way to repro that same scenario anymore (i.e., hardware/firmware
bug that introduces the corruption), so validating this kernel fix
against the original crash has been a bit of a challenge.

Still, I wanted to post this patch to report the bug and seek guidance
on how best to fix it and harden blk-mq against this NULL ptr dereference.

Thank you!
---
 block/blk-mq.c | 9 +++++++++
 1 file changed, 9 insertions(+)

diff --git a/block/blk-mq.c b/block/blk-mq.c
index 5ae22d556540..5dc9d7d806b5 100644
--- a/block/blk-mq.c
+++ b/block/blk-mq.c
@@ -1307,6 +1307,15 @@ static void blk_mq_raise_softirq(struct request *rq)
 
 bool blk_mq_complete_request_remote(struct request *rq)
 {
+	/*
+	 * Validate request is not freed (__blk_mq_free_request() sets
+	 * mq_hctx = NULL).
+	 */
+	if (unlikely(!rq->mq_hctx)) {
+		WARN_ONCE(1, "%s: attempt to complete freed request", __func__);
+		return true;
+	}
+
 	WRITE_ONCE(rq->state, MQ_RQ_COMPLETE);
 
 	/*

---
base-commit: 20eef29b7c8465ac98d7dd6d6f2ac07a8d8056ca
change-id: 20261118-fix-blk-mq-null-ptr-deref-7f376cd5ad90

Regards,
Srivatsa
```
