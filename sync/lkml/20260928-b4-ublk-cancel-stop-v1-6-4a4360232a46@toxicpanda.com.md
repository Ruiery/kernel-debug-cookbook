---
title: [PATCH 6/9] ublk: split ublk_claim_cmd() out of ublk_cancel_cmd()
list: linux-block
message_id: 20260928-b4-ublk-cancel-stop-v1-6-4a4360232a46@toxicpanda.com
link: https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-6-4a4360232a46@toxicpanda.com/
---

# [PATCH 6/9] ublk: split ublk_claim_cmd() out of ublk_cancel_cmd()

来源：[https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-6-4a4360232a46@toxicpanda.com/](https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-6-4a4360232a46@toxicpanda.com/)

```
ublk_cancel_cmd() marks the io as canceled, takes the command off it and
completes the command. The next patches have callers which do the first
two steps under a mutex and must not complete the command there: the
control paths complete with IO_URING_F_UNLOCKED, where
io_uring_cmd_done() takes uring_lock, and ublk_fetch() takes ub->mutex
and cancel_mutex inside of uring_lock.

Move the marking into ublk_claim_cmd(), which returns the command for the
caller to complete. ublk_cancel_cmd() is ublk_claim_cmd() followed by
io_uring_cmd_done().

No functional change.

Assisted-by: LLM
Signed-off-by: Josef Bacik <josef@toxicpanda.com>
---
 drivers/block/ublk_drv.c | 17 ++++++++++++++---
 1 file changed, 14 insertions(+), 3 deletions(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 2ff6506b8664..99ac56d36dd0 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -2778,8 +2778,11 @@ static void ublk_start_cancel(struct ublk_device *ub)
 	ublk_put_disk(disk);
 }
 
-static void ublk_cancel_cmd(struct ublk_queue *ubq, u16 tag,
-		unsigned int issue_flags)
+/*
+ * Mark a fetched command as canceled and take it off the io, the caller
+ * completes it
+ */
+static struct io_uring_cmd *ublk_claim_cmd(struct ublk_queue *ubq, u16 tag)
 {
 	struct ublk_io *io = &ubq->ios[tag];
 	struct ublk_device *ub = ubq->dev;
@@ -2831,6 +2834,14 @@ static void ublk_cancel_cmd(struct ublk_queue *ubq, u16 tag,
 unlock:
 	ublk_io_unlock(io);
 
+	return cmd;
+}
+
+static void ublk_cancel_cmd(struct ublk_queue *ubq, u16 tag,
+			    unsigned int issue_flags)
+{
+	struct io_uring_cmd *cmd = ublk_claim_cmd(ubq, tag);
+
 	if (cmd)
 		io_uring_cmd_done(cmd, UBLK_IO_RES_ABORT, issue_flags);
 }
@@ -3224,7 +3235,7 @@ static inline void ublk_prep_cancel(struct io_uring_cmd *cmd,
 /*
  * Called by the issue path after ublk_prep_cancel(): a cancel which found
  * the command before it was marked took it off the io and left completing
- * it here.  io->lock orders this against ublk_cancel_cmd(), which sees the
+ * it here.  io->lock orders this against ublk_claim_cmd(), which sees the
  * marking if it runs after this, and completes the command itself then.
  */
 static bool ublk_take_canceled_cmd(struct ublk_io *io)

-- 
2.55.0
```
