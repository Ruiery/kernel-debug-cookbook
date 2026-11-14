---
title: [PATCH 03/12] nvmet: take freeze protection for writes to files
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-3-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-3-f5ae61c898b1@kernel.org/
---

# [PATCH 03/12] nvmet: take freeze protection for writes to files

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-3-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-3-f5ae61c898b1@kernel.org/)

```
The file backend calls ->write_iter() of the backing file without
taking freeze protection. So a write to a namespace goes through to a
filesystem that is frozen. With the backing file on ext4 and
buffered_io:

  WARNING: fs/ext4/ext4_jbd2.c:90 at ext4_journal_check_start+0x1f6/0x2d0, CPU#1: kworker/1:1/56
  Workqueue: nvmet-buffered-io-wq nvmet_file_buffered_io_work
  Call Trace:
   <TASK>
   __ext4_journal_start_sb+0x7a/0x470
   ext4_dirty_inode+0xa1/0x120
   __mark_inode_dirty+0x154/0x1110
   file_update_time_flags+0x3ab/0x4b0
   ext4_buffered_write_iter+0x143/0x630
   ext4_file_write_iter+0x7b9/0x1570
   nvmet_file_submit_bvec+0x2e7/0x590
   nvmet_file_execute_io+0x460/0x830
   process_one_work+0x946/0x1820
   worker_thread+0x4f1/0xd60
   kthread+0x364/0x460
   ret_from_fork+0x525/0x770
   ret_from_fork_asm+0x1a/0x30
   </TASK>

The same happens with direct I/O.

Take freeze protection around the write. A write that wasn't queued
drops it right away. A write that was queued drops it in the completion
callback. nvmet_file_io_done() is also called for I/O that wasn't queued
so queued I/O gets its own callback.

Note that buffered I/O is tried with IOCB_NOWAIT first. That attempt
must not wait until the filesystem is thawed. So it only tries to get
freeze protection and fails with -EAGAIN otherwise. The write is then
retried from the workqueue like any other write that would have
blocked.

Fixes: d5eff33ee6f8 ("nvmet: add simple file backed ns support")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/nvme/target/io-cmd-file.c | 37 ++++++++++++++++++++++++++++++-------
 1 file changed, 30 insertions(+), 7 deletions(-)

diff --git a/drivers/nvme/target/io-cmd-file.c b/drivers/nvme/target/io-cmd-file.c
index 695963dd932ee..2a2be95263733 100644
--- a/drivers/nvme/target/io-cmd-file.c
+++ b/drivers/nvme/target/io-cmd-file.c
@@ -77,27 +77,39 @@ static ssize_t nvmet_file_submit_bvec(struct nvmet_req *req, loff_t pos,
 		unsigned long nr_segs, size_t count, int ki_flags)
 {
 	struct kiocb *iocb = &req->f.iocb;
-	ssize_t (*call_iter)(struct kiocb *iocb, struct iov_iter *iter);
+	struct file *file = req->ns->file;
 	struct iov_iter iter;
+	ssize_t ret;
 	int rw;
 
 	if (req->cmd->rw.opcode == nvme_cmd_write) {
 		if (req->cmd->rw.control & cpu_to_le16(NVME_RW_FUA))
 			ki_flags |= IOCB_DSYNC;
-		call_iter = req->ns->file->f_op->write_iter;
 		rw = ITER_SOURCE;
 	} else {
-		call_iter = req->ns->file->f_op->read_iter;
 		rw = ITER_DEST;
 	}
 
 	iov_iter_bvec(&iter, rw, req->f.bvec, nr_segs, count);
 
 	iocb->ki_pos = pos;
-	iocb->ki_filp = req->ns->file;
-	iocb->ki_flags = ki_flags | iocb->ki_filp->f_iocb_flags;
+	iocb->ki_filp = file;
+	iocb->ki_flags = ki_flags | file->f_iocb_flags;
 
-	return call_iter(iocb, &iter);
+	if (rw == ITER_DEST)
+		return file->f_op->read_iter(iocb, &iter);
+
+	/* The IOCB_NOWAIT attempt must not wait for a thaw. */
+	if (ki_flags & IOCB_NOWAIT) {
+		if (!kiocb_start_write_trylock(iocb))
+			return -EAGAIN;
+	} else {
+		kiocb_start_write(iocb);
+	}
+	ret = file->f_op->write_iter(iocb, &iter);
+	if (ret != -EIOCBQUEUED)
+		kiocb_end_write(iocb);
+	return ret;
 }
 
 static void nvmet_file_io_done(struct kiocb *iocb, long ret)
@@ -117,6 +129,17 @@ static void nvmet_file_io_done(struct kiocb *iocb, long ret)
 	nvmet_req_complete(req, status);
 }
 
+static void nvmet_file_io_complete(struct kiocb *iocb, long ret)
+{
+	struct nvmet_req *req = container_of(iocb, struct nvmet_req, f.iocb);
+
+	/* A queued write still holds freeze protection. */
+	if (req->cmd->rw.opcode == nvme_cmd_write)
+		kiocb_end_write(iocb);
+
+	nvmet_file_io_done(iocb, ret);
+}
+
 static bool nvmet_file_execute_io(struct nvmet_req *req, int ki_flags)
 {
 	ssize_t nr_bvec = req->sg_cnt;
@@ -175,7 +198,7 @@ static bool nvmet_file_execute_io(struct nvmet_req *req, int ki_flags)
 	 * for the IOCB_NOWAIT case.
 	 */
 	if (!(ki_flags & IOCB_NOWAIT))
-		req->f.iocb.ki_complete = nvmet_file_io_done;
+		req->f.iocb.ki_complete = nvmet_file_io_complete;
 
 	ret = nvmet_file_submit_bvec(req, pos, bv_cnt, total_len, ki_flags);
 

-- 
2.53.0
```
