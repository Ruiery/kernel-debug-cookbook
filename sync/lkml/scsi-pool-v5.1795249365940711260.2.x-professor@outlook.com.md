---
title: [PATCH v5 2/2] scsi: bsg: Release io_uring requests from end-I/O
list: linux-block
message_id: scsi-pool-v5.1795249365940711260.2.x-professor@outlook.com
link: https://lore.kernel.org/linux-block/scsi-pool-v5.1795249365940711260.2.x-professor@outlook.com/
---

# [PATCH v5 2/2] scsi: bsg: Release io_uring requests from end-I/O

来源：[https://lore.kernel.org/linux-block/scsi-pool-v5.1795249365940711260.2.x-professor@outlook.com/](https://lore.kernel.org/linux-block/scsi-pool-v5.1795249365940711260.2.x-professor@outlook.com/)

```
The bsg io_uring path keeps its completed request until task work copies=0A=
sense data and unmaps the data buffer. A DEFER_TASKRUN ring can leave=0A=
that work pending while its task faults on memory backed by the same=0A=
queue. If completed requests hold all available tags, the fault's I/O=0A=
cannot proceed and the task cannot run the work which releases them.=0A=
=0A=
Save the result and bounded sense data in end-I/O, return RQ_END_IO_FREE,=
=0A=
and let task work use the saved state. The saved BIO chain holds its own=0A=
references, which blk_rq_unmap_user() releases. Canceled task work still=0A=
unmaps it, suppresses sense copyback, and completes with -ECANCELED.=0A=
=0A=
Use the bsg completion pool for sense snapshots. Only commands supplying=0A=
a response buffer with a nonzero length take a slot. Take it before=0A=
mapping data, because unmapping a bounced READ copies data back even=0A=
when the command was never submitted. If no slot is available, return=0A=
-EAGAIN; io_uring may retry a nonblocking attempt in io-wq. An io-wq=0A=
attempt that finds the pool empty completes with -EAGAIN, requiring=0A=
userspace to resubmit.=0A=
=0A=
Return the slot in end-I/O when no sense data needs copying, allowing=0A=
successful commands to release it without waiting for task work. Task=0A=
work returns any remaining slot before posting the CQE. Clear the saved=0A=
sense length on cancellation or copy failure so the CQE does not report=0A=
sense bytes that were not delivered.=0A=
=0A=
Fixes: 7b6d3255e7f8 ("scsi: bsg: add io_uring passthrough handler")=0A=
Suggested-by: Yang Xiuwei <yangxiuwei@kylinos.cn>=0A=
Cc: stable@vger.kernel.org=0A=
Signed-off-by: Yingjie Wang <x-professor@outlook.com>=0A=
---=0A=
Changes in v5:=0A=
- Use the shared per-device pool from patch 1.=0A=
- Return the sense buffer in end-I/O when no sense data needs copying (Yang=
).=0A=
- Drop the unrelated multishot rejection and timeout snapshot.=0A=
- Rebase on synchronous v5.=0A=
=0A=
 drivers/scsi/scsi_bsg.c | 109 +++++++++++++++++++++++++++++-----------=0A=
 1 file changed, 80 insertions(+), 29 deletions(-)=0A=
=0A=
diff --git a/drivers/scsi/scsi_bsg.c b/drivers/scsi/scsi_bsg.c=0A=
index c17cad798326..d1ad956df9d6 100644=0A=
--- a/drivers/scsi/scsi_bsg.c=0A=
+++ b/drivers/scsi/scsi_bsg.c=0A=
@@ -16,9 +16,13 @@=0A=
  */=0A=
 struct scsi_bsg_uring_cmd_pdu {=0A=
 	struct bio *bio;		/* mapped user buffer, unmap in task work */=0A=
-	struct request *req;		/* block request, freed in task work */=0A=
+	u8 *sense_buffer;		/* sense snapshot from the per-device pool */=0A=
 	u64 response_addr;		/* user space response buffer address */=0A=
-	u32 max_response_len;		/* user response buffer size */=0A=
+	/* max_response_len is replaced by res2 after the end-I/O snapshot. */=0A=
+	union {=0A=
+		u32 max_response_len;	/* maximum sense snapshot size */=0A=
+		u64 res2;		/* saved completion result */=0A=
+	};=0A=
 };=0A=
 static_assert(sizeof(struct scsi_bsg_uring_cmd_pdu) <=3D sizeof_field(stru=
ct io_uring_cmd, pdu));=0A=
 =0A=
@@ -28,17 +32,22 @@ static inline struct scsi_bsg_uring_cmd_pdu *scsi_bsg_u=
ring_cmd_pdu(=0A=
 	return io_uring_cmd_to_pdu(ioucmd, struct scsi_bsg_uring_cmd_pdu);=0A=
 }=0A=
 =0A=
-/* Task work: build res2 (layout in uapi/linux/bsg.h) and copy sense to us=
er. */=0A=
+static u64 scsi_bsg_res2_clear_sense_len(u64 res2)=0A=
+{=0A=
+	return bsg_scsi_res2_build(bsg_scsi_res2_device_status(res2),=0A=
+				   bsg_scsi_res2_driver_status(res2),=0A=
+				   bsg_scsi_res2_host_status(res2), 0,=0A=
+				   bsg_scsi_res2_resid_len(res2));=0A=
+}=0A=
+=0A=
+/* Task work: unmap the saved BIO and copy sense to user space. */=0A=
 static void scsi_bsg_uring_task_cb(struct io_tw_req tw_req, io_tw_token_t =
tw)=0A=
 {=0A=
 	struct io_uring_cmd *ioucmd =3D io_uring_cmd_from_tw(tw_req);=0A=
 	struct scsi_bsg_uring_cmd_pdu *pdu =3D scsi_bsg_uring_cmd_pdu(ioucmd);=0A=
-	struct request *rq =3D pdu->req;=0A=
-	struct scsi_cmnd *scmd =3D blk_mq_rq_to_pdu(rq);=0A=
-	u64 res2;=0A=
+	u64 res2 =3D pdu->res2;=0A=
+	u8 sense_len =3D bsg_scsi_res2_sense_len(res2);=0A=
 	int ret =3D 0;=0A=
-	u8 driver_status =3D 0;=0A=
-	u8 sense_len_wr =3D 0;=0A=
 =0A=
 	if (pdu->bio)=0A=
 		ret =3D blk_rq_unmap_user(pdu->bio);=0A=
@@ -48,27 +57,22 @@ static void scsi_bsg_uring_task_cb(struct io_tw_req tw_=
req, io_tw_token_t tw)=0A=
 	 * has exited, this may run from a kworker or in a different task, so=0A=
 	 * don't copy the sense data to the submitter's address.=0A=
 	 */=0A=
-	if (unlikely(tw.cancel))=0A=
+	if (unlikely(tw.cancel)) {=0A=
 		ret =3D -ECANCELED;=0A=
-=0A=
-	if (scsi_status_is_check_condition(scmd->result)) {=0A=
-		driver_status =3D DRIVER_SENSE;=0A=
-		if (pdu->response_addr && !tw.cancel)=0A=
-			sense_len_wr =3D min_t(unsigned int, pdu->max_response_len,=0A=
-					     scmd->sense_len);=0A=
-	}=0A=
-=0A=
-	if (sense_len_wr) {=0A=
-		if (copy_to_user(uptr64(pdu->response_addr), scmd->sense_buffer,=0A=
-				 sense_len_wr))=0A=
+		sense_len =3D 0;=0A=
+	} else if (sense_len) {=0A=
+		if (copy_to_user(uptr64(pdu->response_addr), pdu->sense_buffer,=0A=
+				 sense_len)) {=0A=
 			ret =3D -EFAULT;=0A=
+			sense_len =3D 0;=0A=
+		}=0A=
 	}=0A=
 =0A=
-	res2 =3D bsg_scsi_res2_build(status_byte(scmd->result), driver_status,=0A=
-				  host_byte(scmd->result), sense_len_wr,=0A=
-				  scmd->resid_len);=0A=
+	if (!sense_len)=0A=
+		res2 =3D scsi_bsg_res2_clear_sense_len(res2);=0A=
 =0A=
-	blk_mq_free_request(rq);=0A=
+	if (pdu->sense_buffer)=0A=
+		bsg_uring_cmd_put_completion_buf(ioucmd, pdu->sense_buffer);=0A=
 	io_uring_cmd_done32(ioucmd, ret, res2,=0A=
 			    IO_URING_CMD_TASK_WORK_ISSUE_FLAGS);=0A=
 }=0A=
@@ -78,9 +82,34 @@ static enum rq_end_io_ret scsi_bsg_uring_cmd_done(struct=
 request *req,=0A=
 						  const struct io_comp_batch *iocb)=0A=
 {=0A=
 	struct io_uring_cmd *ioucmd =3D req->end_io_data;=0A=
+	struct scsi_bsg_uring_cmd_pdu *pdu =3D scsi_bsg_uring_cmd_pdu(ioucmd);=0A=
+	struct scsi_cmnd *scmd =3D blk_mq_rq_to_pdu(req);=0A=
+	u8 driver_status =3D 0;=0A=
+	u8 sense_len =3D 0;=0A=
+=0A=
+	if (scsi_status_is_check_condition(scmd->result)) {=0A=
+		driver_status =3D DRIVER_SENSE;=0A=
+		if (pdu->sense_buffer) {=0A=
+			sense_len =3D min_t(unsigned int, pdu->max_response_len,=0A=
+					  scmd->sense_len);=0A=
+			if (sense_len)=0A=
+				memcpy(pdu->sense_buffer, scmd->sense_buffer,=0A=
+				       sense_len);=0A=
+		}=0A=
+	}=0A=
+=0A=
+	pdu->res2 =3D bsg_scsi_res2_build(status_byte(scmd->result),=0A=
+					driver_status, host_byte(scmd->result),=0A=
+					sense_len, scmd->resid_len);=0A=
+=0A=
+	/* Return the buffer now if there is no sense data to copy. */=0A=
+	if (!sense_len && pdu->sense_buffer) {=0A=
+		bsg_uring_cmd_put_completion_buf(ioucmd, pdu->sense_buffer);=0A=
+		pdu->sense_buffer =3D NULL;=0A=
+	}=0A=
 =0A=
 	io_uring_cmd_do_in_task_lazy(ioucmd, scsi_bsg_uring_task_cb);=0A=
-	return RQ_END_IO_NONE;=0A=
+	return RQ_END_IO_FREE;=0A=
 }=0A=
 =0A=
 static int scsi_bsg_map_user_buffer(struct request *req,=0A=
@@ -123,6 +152,9 @@ static int scsi_bsg_uring_cmd(struct request_queue *q, =
struct io_uring_cmd *iouc=0A=
 	u32 dout_xfer_len =3D READ_ONCE(cmd->dout_xfer_len);=0A=
 	u64 din_xferp =3D READ_ONCE(cmd->din_xferp);=0A=
 	u32 din_xfer_len =3D READ_ONCE(cmd->din_xfer_len);=0A=
+	u64 response_addr =3D READ_ONCE(cmd->response);=0A=
+	u32 max_response_len =3D min_t(u32, READ_ONCE(cmd->max_response_len),=0A=
+				     SCSI_SENSE_BUFFERSIZE);=0A=
 	int ret;=0A=
 =0A=
 	if (cmd->protocol !=3D BSG_PROTOCOL_SCSI ||=0A=
@@ -168,8 +200,25 @@ static int scsi_bsg_uring_cmd(struct request_queue *q,=
 struct io_uring_cmd *iouc=0A=
 		goto out_free_req;=0A=
 	}=0A=
 =0A=
-	pdu->response_addr =3D cmd->response;=0A=
-	pdu->max_response_len =3D cmd->max_response_len;=0A=
+	pdu->response_addr =3D response_addr;=0A=
+	pdu->max_response_len =3D max_response_len;=0A=
+=0A=
+	/*=0A=
+	 * Take a sense buffer before mapping data: unmapping a bounced READ=0A=
+	 * copies back even if no I/O ran, so rejecti
```
