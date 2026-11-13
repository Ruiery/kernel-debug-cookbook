---
title: [PATCH RFC 3/3] fs/pipe: copy a run of anonymous buffers in one user access section
list: linux-block
message_id: 20261113-pipe-pool-regression-smap-v1-3-b0dc69558ab3@debian.org
link: https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-3-b0dc69558ab3@debian.org/
---

# [PATCH RFC 3/3] fs/pipe: copy a run of anonymous buffers in one user access section

来源：[https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-3-b0dc69558ab3@debian.org/](https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-3-b0dc69558ab3@debian.org/)

```
anon_pipe_read() copies one pipe_buffer per copy_page_to_iter() call.
On x86 every call opens and closes its own user access section, so a
64 KiB read that drains a full default pipe executes 16 STAC/CLAC pairs.

Hand up to PIPE_DEF_BUFFERS consecutive anonymous buffers that the read
consumes whole to copy_bvecs_to_iter_full(), then release them. That
includes buffers that splice() or tee() took from another pipe, which
keep anon_pipe_buf_ops.

A last buffer that the read takes only part of, packet buffers, and
buffers with other pipe_buf_operations, such as watch queue notes, page
cache pages and vmsplice()d pages, keep the buffer by buffer loop.

A fault inside the batch consumes nothing and leaves the buffers to the
existing loop, so short reads and -EFAULT behave as before. An injected
usercopy fault takes the same way out.

What this buys depends on what SMAP costs the CPU. With the buffer by
buffer loop, booting with clearcpuid=smap speeds pipe_bench up by 4-14%
on a Sapphire Rapids Xeon Gold 6450C.

pipe_bench from the pipe selftests runs 1, 2 or 5 writers against 1, 5
or 10 readers on one 1 MiB pipe, with 64 KiB writes and reads.

The numbers below come from an earlier version of this patch, which did
the copies in fs/pipe.c and left runs of a single buffer to the old
loop. Throughput change, median of 2 boots x 5 runs, SMAP on:

  writers  readers  Sapphire Rapids
        1        1           +5.2%
        1        5           +9.7%
        1       10           +8.7%
        2        1          +15.3%
        2        5           +8.4%
        2       10           +8.6%
        5        1          +11.9%
        5        5           +9.8%
        5       10           +8.0%

Suggested-by: Mateusz Guzik <mjguzik@gmail.com>
Link: https://lore.kernel.org/all/CAGudoHF3de_55YvdztPs7QiYs25u6nPEV=uMOzfr=bWmwof69g@mail.gmail.com/
Signed-off-by: Breno Leitao <leitao@debian.org>
---
 fs/pipe.c | 44 +++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 43 insertions(+), 1 deletion(-)

diff --git a/fs/pipe.c b/fs/pipe.c
index 29ae6c4a6c642c..a0d4c8b2f685bb 100644
--- a/fs/pipe.c
+++ b/fs/pipe.c
@@ -297,6 +297,40 @@ static inline unsigned int pipe_update_tail(struct pipe_inode_info *pipe,
 	return tail;
 }
 
+/*
+ * Read the anonymous buffers at @tail that the read consumes whole with one
+ * copy_bvecs_to_iter_full() call, which can copy them to a user buffer in one
+ * user access section. Returns the bytes read, or 0 to go buffer by buffer.
+ */
+static size_t anon_pipe_read_batch(struct pipe_inode_info *pipe,
+				   struct iov_iter *to, size_t total_len,
+				   unsigned int head, unsigned int *tailp,
+				   bool *wake_writer)
+{
+	struct bio_vec bv[PIPE_DEF_BUFFERS];
+	unsigned int tail = *tailp, n;
+	size_t len = 0;
+
+	for (n = 0; n < PIPE_DEF_BUFFERS && !pipe_empty(head, tail + n); n++) {
+		struct pipe_buffer *buf = pipe_buf(pipe, tail + n);
+
+		if (buf->ops != &anon_pipe_buf_ops ||
+		    (buf->flags & PIPE_BUF_FLAG_PACKET) ||
+		    buf->len > total_len - len)
+			break;
+		bvec_set_page(&bv[n], buf->page, buf->len, buf->offset);
+		len += buf->len;
+	}
+	if (!n || !copy_bvecs_to_iter_full(bv, n, to))
+		return 0;
+
+	*wake_writer |= pipe_full(head, tail, pipe->max_usage);
+	while (n--)
+		tail = pipe_update_tail(pipe, pipe_buf(pipe, tail), tail);
+	*tailp = tail;
+	return len;
+}
+
 static ssize_t
 anon_pipe_read(struct kiocb *iocb, struct iov_iter *to)
 {
@@ -304,7 +338,7 @@ anon_pipe_read(struct kiocb *iocb, struct iov_iter *to)
 	struct file *filp = iocb->ki_filp;
 	struct pipe_inode_info *pipe = filp->private_data;
 	bool wake_writer = false, wake_next_reader = false;
-	ssize_t ret;
+	ssize_t ret, batched;
 
 	/* Null read succeeds. */
 	if (unlikely(total_len == 0))
@@ -350,6 +384,14 @@ anon_pipe_read(struct kiocb *iocb, struct iov_iter *to)
 		}
 #endif
 
+		batched = anon_pipe_read_batch(pipe, to, total_len, head,
+					       &tail, &wake_writer);
+		if (batched) {
+			ret += batched;
+			total_len -= batched;
+			if (!total_len)
+				break;	/* common path: read succeeded */
+		}
 		if (!pipe_empty(head, tail)) {
 			struct pipe_buffer *buf = pipe_buf(pipe, tail);
 			size_t chars = buf->len;

-- 
2.53.1-Meta
```
