---
title: [PATCH 5/9] ublk: complete a command canceled before it was marked from its issuer
list: linux-block
message_id: 20260928-b4-ublk-cancel-stop-v1-5-4a4360232a46@toxicpanda.com
link: https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-5-4a4360232a46@toxicpanda.com/
---

# [PATCH 5/9] ublk: complete a command canceled before it was marked from its issuer

来源：[https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-5-4a4360232a46@toxicpanda.com/](https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-5-4a4360232a46@toxicpanda.com/)

```
The issue paths store the command in io->cmd first and call
ublk_prep_cancel() on their way out, which is where io_uring puts the
command on its list of cancelable commands. The io_uring cancel callback
only ever sees commands from that list. A cancel from the control path
finds the command in io->cmd as soon as it is stored, and can complete it
before it is marked:

    issue path                      control path
    ublk_fill_io_cmd()
                                    ublk_cancel_cmd()
                                      io_uring_cmd_done()
                                        not cancelable, nothing to remove
    ublk_prep_cancel()
      io_uring_cmd_mark_cancelable()
        adds the completed request to the list

Leaving such a command alone is no better. FETCH, COMMIT_AND_FETCH and
NEED_GET_DATA queue it right after, no cancel may come after the one
which skipped it, and a server waits for all its commands before it
exits.

Fix by taking the command off the io all the same in ublk_cancel_cmd(),
but setting UBLK_IO_FLAG_CANCEL_DEFERRED instead of completing it, and
by having the issue path look for that flag under io->lock once
ublk_prep_cancel() has marked the command, and complete the command with
UBLK_IO_RES_ABORT then. A cancel which takes io->lock after that sees
the marking and completes the command itself.

IORING_URING_CMD_CANCELABLE is not one of the flags the server passes in
the SQE. It is a bit io_uring keeps for itself in the same word of its
own copy of the command: io_uring_cmd_mark_cancelable() sets it and
io_uring_cmd_done() clears it, both with uring_lock held. The control
path does not hold uring_lock, so read the word with READ_ONCE().

Assisted-by: LLM
Signed-off-by: Josef Bacik <josef@toxicpanda.com>
---
 drivers/block/ublk_drv.c | 41 +++++++++++++++++++++++++++++++++++++++++
 1 file changed, 41 insertions(+)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 1455ce27d3d1..2ff6506b8664 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -191,6 +191,14 @@ struct ublk_batch_io_data {
 /* atomic RW with ubq->cancel_lock */
 #define UBLK_IO_FLAG_CANCELED	0x80000000
 
+/*
+ * Set next to UBLK_IO_FLAG_CANCELED by a cancel which took a command
+ * before io_uring marked it cancelable, the issue path completes the
+ * command then, see ublk_take_canceled_cmd().  Set and cleared under
+ * io->lock.
+ */
+#define UBLK_IO_FLAG_CANCEL_DEFERRED	0x40000000
+
 /*
  * Initialize refcount to a large number to include any registered buffers.
  * UBLK_IO_COMMIT_AND_FETCH_REQ will release these references minus those for
@@ -2807,6 +2815,17 @@ static void ublk_cancel_cmd(struct ublk_queue *ubq, u16 tag,
 		io->flags |= UBLK_IO_FLAG_CANCELED;
 		cmd = io->cmd;
 		io->cmd = NULL;
+		/*
+		 * The issue path stores the command before ublk_prep_cancel()
+		 * marks it cancelable, and completing it in between would
+		 * leave a completed request on io_uring's list of cancelable
+		 * commands.  Leave the completion to the issue path then, it
+		 * looks for this once the command is marked.
+		 */
+		if (!(READ_ONCE(cmd->flags) & IORING_URING_CMD_CANCELABLE)) {
+			io->flags |= UBLK_IO_FLAG_CANCEL_DEFERRED;
+			cmd = NULL;
+		}
 	}
 	spin_unlock(&ubq->cancel_lock);
 unlock:
@@ -3202,6 +3221,24 @@ static inline void ublk_prep_cancel(struct io_uring_cmd *cmd,
 	io_uring_cmd_mark_cancelable(cmd, issue_flags);
 }
 
+/*
+ * Called by the issue path after ublk_prep_cancel(): a cancel which found
+ * the command before it was marked took it off the io and left completing
+ * it here.  io->lock orders this against ublk_cancel_cmd(), which sees the
+ * marking if it runs after this, and completes the command itself then.
+ */
+static bool ublk_take_canceled_cmd(struct ublk_io *io)
+{
+	bool canceled;
+
+	ublk_io_lock(io);
+	canceled = io->flags & UBLK_IO_FLAG_CANCEL_DEFERRED;
+	io->flags &= ~UBLK_IO_FLAG_CANCEL_DEFERRED;
+	ublk_io_unlock(io);
+
+	return canceled;
+}
+
 static void ublk_io_release(void *priv)
 {
 	struct request *rq = priv;
@@ -3466,6 +3503,8 @@ static int ublk_ch_uring_cmd_local(struct io_uring_cmd *cmd,
 			goto out;
 
 		ublk_prep_cancel(cmd, issue_flags, ubq, tag);
+		if (ublk_take_canceled_cmd(io))
+			io_uring_cmd_done(cmd, UBLK_IO_RES_ABORT, issue_flags);
 		return -EIOCBQUEUED;
 	}
 
@@ -3542,6 +3581,8 @@ static int ublk_ch_uring_cmd_local(struct io_uring_cmd *cmd,
 		goto out;
 	}
 	ublk_prep_cancel(cmd, issue_flags, ubq, tag);
+	if (ublk_take_canceled_cmd(io))
+		io_uring_cmd_done(cmd, UBLK_IO_RES_ABORT, issue_flags);
 	return -EIOCBQUEUED;
 
  out:

-- 
2.55.0
```
