---
title: [PATCH 3/9] ublk: publish io->cmd under io->lock in the commit paths
list: linux-block
message_id: 20260928-b4-ublk-cancel-stop-v1-3-4a4360232a46@toxicpanda.com
link: https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-3-4a4360232a46@toxicpanda.com/
---

# [PATCH 3/9] ublk: publish io->cmd under io->lock in the commit paths

来源：[https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-3-4a4360232a46@toxicpanda.com/](https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-3-4a4360232a46@toxicpanda.com/)

```
io->cmd shares its storage with io->req. FETCH, COMMIT_AND_FETCH and
NEED_GET_DATA switch the io from one to the other in
ublk_fill_io_cmd() without a lock of their own. That was fine as long
as everything else looking at io->cmd ran under the uring_lock of the
same ring, which is the case for the io_uring cancel callback.

ublk_cancel_cmd() is also called from the control path, from
ublk_cancel_dev() with IO_URING_F_UNLOCKED, and the next patches add
more such callers which run while the server still commits requests.
Nothing orders their reads of io->flags and io->cmd against
ublk_fill_io_cmd() then. A reader can find UBLK_IO_FLAG_ACTIVE set and
still pick up the request pointer from the union.

The batch commit path calls ublk_fill_io_cmd() under io->lock already.
Do the same in the other three callers, so that io->lock covers every
switch of the union to a command. io->lock is per io and only taken by
the task which commits that io, so the fast path gains an uncontended
lock in a cacheline it writes anyway.

ublk_batch_prep_io() calls __ublk_fetch() with io->lock held, which
makes the order io->lock, then ubq->cancel_lock.

The readers move under io->lock in the next patch.

Assisted-by: LLM
Signed-off-by: Josef Bacik <josef@toxicpanda.com>
---
 drivers/block/ublk_drv.c | 12 +++++++++++-
 1 file changed, 11 insertions(+), 1 deletion(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 50c99b28ef21..17a33539f271 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -3169,6 +3169,9 @@ ublk_fill_io_cmd(struct ublk_io *io, struct io_uring_cmd *cmd)
 {
 	struct request *req = io->req;
 
+	/* io->cmd shares its storage with io->req, switch them under io->lock */
+	lockdep_assert_held(&io->lock);
+
 	io->cmd = cmd;
 	io->flags |= UBLK_IO_FLAG_ACTIVE;
 	/* now this cmd slot is owned by ublk driver */
@@ -3338,8 +3341,11 @@ static int ublk_fetch(struct io_uring_cmd *cmd, struct ublk_device *ub,
 	 */
 	mutex_lock(&ub->mutex);
 	ret = ublk_validate_io_buf(ub, cmd, &auto_buf);
-	if (!ret)
+	if (!ret) {
+		ublk_io_lock(io);
 		ret = __ublk_fetch(cmd, ub, io, q_id);
+		ublk_io_unlock(io);
+	}
 	if (!ret) {
 		ublk_apply_io_buf(ub, io, cmd, buf_addr, &auto_buf, NULL);
 		ublk_mark_io_ready(ub, q_id);
@@ -3496,7 +3502,9 @@ static int ublk_ch_uring_cmd_local(struct io_uring_cmd *cmd,
 		if (ret)
 			goto out;
 		io->res = result;
+		ublk_io_lock(io);
 		req = ublk_fill_io_cmd(io, cmd);
+		ublk_io_unlock(io);
 		ublk_apply_io_buf(ub, io, cmd, addr, &auto_buf, &buf_idx);
 		if (buf_idx != UBLK_INVALID_BUF_IDX)
 			io_buffer_unregister(cmd, buf_idx, issue_flags);
@@ -3514,7 +3522,9 @@ static int ublk_ch_uring_cmd_local(struct io_uring_cmd *cmd,
 		 * uring_cmd active first and prepare for handling new requeued
 		 * request
 		 */
+		ublk_io_lock(io);
 		req = ublk_fill_io_cmd(io, cmd);
+		ublk_io_unlock(io);
 		io->buf.addr = addr;
 		if (likely(ublk_get_data(ubq, io, req))) {
 			__ublk_prep_compl_io_cmd(io, req);

-- 
2.55.0
```
