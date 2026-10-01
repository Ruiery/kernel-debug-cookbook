---
title: [PATCH] block: don't quiesce the queue when setting the default elevator
list: linux-block
message_id: 20261001-bug-block-elevator-init-quiesce-v1-1-5c85fa0ec59b@gmail.com
link: https://lore.kernel.org/linux-block/20261001-bug-block-elevator-init-quiesce-v1-1-5c85fa0ec59b@gmail.com/
---

# [PATCH] block: don't quiesce the queue when setting the default elevator

来源：[https://lore.kernel.org/linux-block/20261001-bug-block-elevator-init-quiesce-v1-1-5c85fa0ec59b@gmail.com/](https://lore.kernel.org/linux-block/20261001-bug-block-elevator-init-quiesce-v1-1-5c85fa0ec59b@gmail.com/)

```
elevator_set_default() runs from blk_register_queue() while the disk is
still being added: the block device is not visible yet and uevents are
suppressed, so no file system I/O can be issued. elevator_change()
freezes the queue and cancels the dispatch work before switching, which
is enough to drain dispatch activity from passthrough requests, as the
comment in elevator_change() already states.

elevator_switch() still quiesces the queue unconditionally, though, so
every disk added with a default elevator waits for an RCU grace period.
Commit 245a489e81e1 ("block: avoid to quiesce queue in
elevator_init_mq") had removed this wait from the default elevator
setup, and it came back when that setup was folded into
elevator_change().

The wait is paid in full by callers that add disks one at a time. ublk
adds the disk of a single-queue device from START_DEV, which takes 7.7ms
at p50 in a 16 vCPU KVM guest, most of it in blk_mq_quiesce_queue()
called from elevator_set_default().

Skip quiescing in elevator_switch() when setting the default elevator.

ublk null target, 1000 single-queue devices created one by one:

                     before      after
  START_DEV p50      7.74ms     0.68ms
  START_DEV p99     14.61ms     1.32ms
  devices/s             114        971

Fixes: 1e44bedbc921 ("block: unifying elevator change")
Cc: stable@vger.kernel.org
Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
 block/elevator.c | 7 +++++--
 block/elevator.h | 2 ++
 2 files changed, 7 insertions(+), 2 deletions(-)

diff --git a/block/elevator.c b/block/elevator.c
index 2161b6eea680c..da9ba70ac9321 100644
--- a/block/elevator.c
+++ b/block/elevator.c
@@ -573,7 +573,8 @@ static int elevator_switch(struct request_queue *q, struct elv_change_ctx *ctx)
 			return -EINVAL;
 	}
 
-	blk_mq_quiesce_queue(q);
+	if (!ctx->no_quiesce)
+		blk_mq_quiesce_queue(q);
 
 	if (q->elevator) {
 		ctx->old = q->elevator;
@@ -594,7 +595,8 @@ static int elevator_switch(struct request_queue *q, struct elv_change_ctx *ctx)
 	blk_add_trace_msg(q, "elv switch: %s", ctx->name);
 
 out_unfreeze:
-	blk_mq_unquiesce_queue(q);
+	if (!ctx->no_quiesce)
+		blk_mq_unquiesce_queue(q);
 
 	if (ret) {
 		pr_warn("elv: switch to \"%s\" failed, falling back to \"none\"\n",
@@ -731,6 +733,7 @@ void elevator_set_default(struct request_queue *q)
 	struct elv_change_ctx ctx = {
 		.name = "mq-deadline",
 		.no_uevent = true,
+		.no_quiesce = true,
 	};
 	int err;
 
diff --git a/block/elevator.h b/block/elevator.h
index 3eb32516be0b1..3886d97427e33 100644
--- a/block/elevator.h
+++ b/block/elevator.h
@@ -43,6 +43,8 @@ struct elevator_resources {
 struct elv_change_ctx {
 	const char *name;
 	bool no_uevent;
+	/* the disk isn't added yet, so skip quiescing the queue */
+	bool no_quiesce;
 
 	/* for unregistering old elevator */
 	struct elevator_queue *old;

---
base-commit: 551c722f40809618230001baccf219193e22fc5a
change-id: 20260930-bug-block-elevator-init-quiesce-35d73f9b462d

Best regards,
-- 
Qiliang Yuan <odys.yuan@gmail.com>
```
