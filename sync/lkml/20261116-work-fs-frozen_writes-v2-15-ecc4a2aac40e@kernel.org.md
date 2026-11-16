---
title: [PATCH v2 15/17] loop: use kiocb_write_iter()
list: linux-block
message_id: 20261116-work-fs-frozen_writes-v2-15-ecc4a2aac40e@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-15-ecc4a2aac40e@kernel.org/
---

# [PATCH v2 15/17] loop: use kiocb_write_iter()

来源：[https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-15-ecc4a2aac40e@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-15-ecc4a2aac40e@kernel.org/)

```
Use the new helpers instead of open-coding freeze protection for writes
to the backing file.

No functional changes.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/block/loop.c | 10 ++++------
 1 file changed, 4 insertions(+), 6 deletions(-)

diff --git a/drivers/block/loop.c b/drivers/block/loop.c
index d2f29aadabcc1..872d78006b131 100644
--- a/drivers/block/loop.c
+++ b/drivers/block/loop.c
@@ -325,8 +325,7 @@ static void lo_rw_aio_do_completion(struct loop_cmd *cmd)
 		return;
 	kfree(cmd->bvec);
 	cmd->bvec = NULL;
-	if (req_op(rq) == REQ_OP_WRITE)
-		kiocb_end_write(&cmd->iocb);
+	kiocb_end_write_iter(&cmd->iocb);
 	if (likely(!blk_should_fake_timeout(rq->q)))
 		blk_mq_complete_request(rq);
 }
@@ -395,10 +394,9 @@ static int lo_rw_aio(struct loop_device *lo, struct loop_cmd *cmd,
 		cmd->iocb.ki_flags = 0;
 	}
 
-	if (rw == ITER_SOURCE) {
-		kiocb_start_write(&cmd->iocb);
-		ret = file->f_op->write_iter(&cmd->iocb, &iter);
-	} else
+	if (rw == ITER_SOURCE)
+		ret = kiocb_write_iter(&cmd->iocb, &iter);
+	else
 		ret = file->f_op->read_iter(&cmd->iocb, &iter);
 
 	lo_rw_aio_do_completion(cmd);

-- 
2.53.0
```
