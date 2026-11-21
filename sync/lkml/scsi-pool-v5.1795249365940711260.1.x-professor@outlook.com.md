---
title: [PATCH v5 1/2] block: bsg: add a per-device pool of uring_cmd completion buffers
list: linux-block
message_id: scsi-pool-v5.1795249365940711260.1.x-professor@outlook.com
link: https://lore.kernel.org/linux-block/scsi-pool-v5.1795249365940711260.1.x-professor@outlook.com/
---

# [PATCH v5 1/2] block: bsg: add a per-device pool of uring_cmd completion buffers

来源：[https://lore.kernel.org/linux-block/scsi-pool-v5.1795249365940711260.1.x-professor@outlook.com/](https://lore.kernel.org/linux-block/scsi-pool-v5.1795249365940711260.1.x-professor@outlook.com/)

```
A bsg uring_cmd driver needs storage for completion data which outlives=0A=
its block request when the request is freed in end-I/O. scsi_bsg needs=0A=
to preserve sense data until task work can copy it to userspace.=0A=
=0A=
Allocate a pool when a bsg queue with a uring_cmd handler is registered,=0A=
and free it when the bsg device is released. Each pool has BSG_DEFAULT_CMDS=
=0A=
slots of SCSI_SENSE_BUFFERSIZE bytes, for the only in-tree uring_cmd=0A=
consumer, scsi_bsg. Transport bsg devices and kernels without io_uring=0A=
allocate no pool. A bitmap and the buffers share one allocation.=0A=
=0A=
The get helper returns NULL when the pool is empty so the driver can=0A=
return -EAGAIN without allocating or waiting for a buffer in the I/O=0A=
path. Slots are shared by all openers of a device. One opener can retain=0A=
all 64 slots, for example with unreaped CHECK CONDITION completions on=0A=
a DEFER_TASKRUN ring, causing other openers to receive -EAGAIN too.=0A=
bsg nodes are normally restricted to privileged users, and sharing avoids=
=0A=
allocating a pool on every open. SG_SET_COMMAND_Q does not resize it.=0A=
=0A=
A checked-out buffer must be returned before completing or failing its=0A=
command. io_uring retains the file reference through command completion,=0A=
and the open cdev keeps the bsg device alive, so the pool cannot be freed=
=0A=
while a buffer is checked out. Protect the bitmap with irqsave locking=0A=
because buffers can be returned from end-I/O as well as process context.=0A=
=0A=
The next patch makes scsi_bsg use the pool to release completed requests=0A=
before task work. No caller checks out buffers in this patch alone.=0A=
=0A=
Cc: stable@vger.kernel.org=0A=
Co-developed-by: Yang Xiuwei <yangxiuwei@kylinos.cn>=0A=
Signed-off-by: Yang Xiuwei <yangxiuwei@kylinos.cn>=0A=
Signed-off-by: Yingjie Wang <x-professor@outlook.com>=0A=
---=0A=
Changes in v5:=0A=
- Replace the per-file pool with Yang's per-device pool: inline bitmap,=0A=
  one allocation, irqsave locking. Return quietly on invalid get/put=0A=
  arguments and trim comments. The subject changed accordingly.=0A=
- Add Co-developed-by and retain Yang's Signed-off-by from his posted patch=
.=0A=
=0A=
This patch is a prerequisite for the following fix; it has no Fixes tag=0A=
of its own.=0A=
=0A=
 block/bsg.c         | 109 ++++++++++++++++++++++++++++++++++++++++++++=0A=
 include/linux/bsg.h |   3 ++=0A=
 2 files changed, 112 insertions(+)=0A=
=0A=
diff --git a/block/bsg.c b/block/bsg.c=0A=
index b296fa373292..73ec02ee8c23 100644=0A=
--- a/block/bsg.c=0A=
+++ b/block/bsg.c=0A=
@@ -12,10 +12,12 @@=0A=
 #include <linux/idr.h>=0A=
 #include <linux/bsg.h>=0A=
 #include <linux/slab.h>=0A=
+#include <linux/bitmap.h>=0A=
 #include <linux/io_uring/cmd.h>=0A=
 =0A=
 #include <scsi/scsi.h>=0A=
 #include <scsi/scsi_ioctl.h>=0A=
+#include <scsi/scsi_device.h>=0A=
 #include <scsi/sg.h>=0A=
 =0A=
 #define BSG_DESCRIPTION	"Block layer SCSI generic (bsg) driver"=0A=
@@ -30,6 +32,7 @@ struct bsg_device {=0A=
 	unsigned int reserved_size;=0A=
 	bsg_sg_io_fn *sg_io_fn;=0A=
 	bsg_uring_cmd_fn *uring_cmd_fn;=0A=
+	struct bsg_completion_pool *completion_pool;=0A=
 };=0A=
 =0A=
 static inline struct bsg_device *to_bsg_device(struct inode *inode)=0A=
@@ -40,6 +43,101 @@ static inline struct bsg_device *to_bsg_device(struct i=
node *inode)=0A=
 #define BSG_DEFAULT_CMDS	64=0A=
 #define BSG_MAX_DEVS		(1 << MINORBITS)=0A=
 =0A=
+/*=0A=
+ * Per-device completion buffers for uring_cmd. These can retain completio=
n=0A=
+ * data after the request is freed. scsi_bsg is the only user, so each=0A=
+ * buffer holds SCSI_SENSE_BUFFERSIZE bytes.=0A=
+ */=0A=
+struct bsg_completion_pool {=0A=
+	spinlock_t lock;		/* protects checked_out, including in end-I/O */=0A=
+	DECLARE_BITMAP(checked_out, BSG_DEFAULT_CMDS);=0A=
+	u8 bufs[];=0A=
+};=0A=
+=0A=
+static struct bsg_completion_pool *bsg_completion_pool_alloc(void)=0A=
+{=0A=
+	struct bsg_completion_pool *pool;=0A=
+=0A=
+	pool =3D kzalloc(struct_size(pool, bufs,=0A=
+				   BSG_DEFAULT_CMDS * SCSI_SENSE_BUFFERSIZE),=0A=
+		       GFP_KERNEL);=0A=
+	if (!pool)=0A=
+		return NULL;=0A=
+	spin_lock_init(&pool->lock);=0A=
+	return pool;=0A=
+}=0A=
+=0A=
+static void bsg_completion_pool_free(struct bsg_completion_pool *pool)=0A=
+{=0A=
+	if (!pool)=0A=
+		return;=0A=
+	WARN_ON_ONCE(!bitmap_empty(pool->checked_out, BSG_DEFAULT_CMDS));=0A=
+	kfree(pool);=0A=
+}=0A=
+=0A=
+/**=0A=
+ * bsg_uring_cmd_get_completion_buf - check out a per-device completion bu=
ffer=0A=
+ * @ioucmd: the uring command being issued=0A=
+ * @len: required buffer size=0A=
+ *=0A=
+ * The caller must return the buffer before completing or failing the comm=
and.=0A=
+ *=0A=
+ * Return: the buffer, or NULL if there is no pool, @len exceeds the buffe=
r=0A=
+ * size, or the pool is exhausted.=0A=
+ */=0A=
+void *bsg_uring_cmd_get_completion_buf(struct io_uring_cmd *ioucmd, size_t=
 len)=0A=
+{=0A=
+	struct bsg_device *bd =3D to_bsg_device(file_inode(ioucmd->file));=0A=
+	struct bsg_completion_pool *pool =3D bd->completion_pool;=0A=
+	unsigned long flags;=0A=
+	unsigned int index;=0A=
+	void *buf =3D NULL;=0A=
+=0A=
+	if (!pool || len > SCSI_SENSE_BUFFERSIZE)=0A=
+		return NULL;=0A=
+=0A=
+	spin_lock_irqsave(&pool->lock, flags);=0A=
+	index =3D find_first_zero_bit(pool->checked_out, BSG_DEFAULT_CMDS);=0A=
+	if (index < BSG_DEFAULT_CMDS) {=0A=
+		__set_bit(index, pool->checked_out);=0A=
+		buf =3D pool->bufs + index * SCSI_SENSE_BUFFERSIZE;=0A=
+	}=0A=
+	spin_unlock_irqrestore(&pool->lock, flags);=0A=
+	return buf;=0A=
+}=0A=
+EXPORT_SYMBOL_GPL(bsg_uring_cmd_get_completion_buf);=0A=
+=0A=
+/**=0A=
+ * bsg_uring_cmd_put_completion_buf - return a per-device completion buffe=
r=0A=
+ * @ioucmd: the uring command that checked out the buffer=0A=
+ * @buf: buffer previously returned by bsg_uring_cmd_get_completion_buf()=
=0A=
+ *=0A=
+ * Return each buffer exactly once, from submission error handling,=0A=
+ * end-I/O or task work. A second return while the buffer is free=0A=
+ * triggers a warning.=0A=
+ */=0A=
+void bsg_uring_cmd_put_completion_buf(struct io_uring_cmd *ioucmd, void *b=
uf)=0A=
+{=0A=
+	struct bsg_device *bd =3D to_bsg_device(file_inode(ioucmd->file));=0A=
+	struct bsg_completion_pool *pool =3D bd->completion_pool;=0A=
+	unsigned long flags;=0A=
+	unsigned long offset;=0A=
+	unsigned int index;=0A=
+=0A=
+	if (!pool || !buf)=0A=
+		return;=0A=
+	offset =3D (unsigned long)buf - (unsigned long)pool->bufs;=0A=
+	if (offset >=3D BSG_DEFAULT_CMDS * SCSI_SENSE_BUFFERSIZE ||=0A=
+	    offset % SCSI_SENSE_BUFFERSIZE)=0A=
+		return;=0A=
+	index =3D offset / SCSI_SENSE_BUFFERSIZE;=0A=
+=0A=
+	spin_lock_irqsave(&pool->lock, flags);=0A=
+	WARN_ON_ONCE(!__test_and_clear_bit(index, pool->checked_out));=0A=
+	spin_unlock_irqrestore(&pool->lock, flags);=0A=
+}=0A=
+EXPORT_SYMBOL_GPL(bsg_uring_cmd_put_completion_buf);=0A=
+=0A=
 static DEFINE_IDA(bsg_minor_ida);=0A=
 static const struct class bsg_class;=0A=
 static int bsg_major;=0A=
@@ -203,6 +301,7 @@ static void bsg_device_release(struct device *dev)=0A=
 {=0A=
 	struct bsg_device *bd =3D container_of(dev, struct bsg_device, device);=
=0A=
 =0A=
+	bsg_completion_pool_free(bd->completion_pool);=0A=
 	ida_free(&bsg_minor_ida, MINOR(bd->device.devt));=0A=
 	kfree(bd);=0A=
 }=0A=
@@ -234,10 +333,20 @@ struct bsg_device *bsg_register_queue(struct request_=
queue *q,=0A=
 	bd->sg_io_fn =3D sg_io_fn;=0A=
 	bd->uring_cmd_fn =3D uring_cmd_fn;=0A=
 =0A=
+	/* Transport bsg devices have no uring_cmd handler and need no pool. */=
=0A=
+	if (IS_ENABLED(CONFIG_IO_URING) && uring_cmd_fn) {=0A=
+		bd->completion_pool =3D bsg_completion_pool_alloc();=0A=
+		if (!bd->completion_pool) {=0A=
+			kfree(bd);=0A=
+			return ERR_PTR(-ENOMEM);=0A=
+		}=0A=
+	}=0A=
+=0A=
 	ret =3D ida_alloc_max(&bsg_minor_ida, BSG_MAX_DEVS - 1, GFP_KERNEL);=0A=
 	if (ret < 0) {=0A=
 		if (ret =3D=3D -ENOSPC)=0A=
 			dev_err(parent, "bsg: too many bsg devices\n");=0A=
+		bsg_completion_pool_free(bd->com
```
