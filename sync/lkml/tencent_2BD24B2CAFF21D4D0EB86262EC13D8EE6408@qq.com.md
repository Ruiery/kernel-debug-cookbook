---
title: [PATCH] blktrace: always record v2 format for the ftrace tracer
list: linux-block
message_id: tencent_2BD24B2CAFF21D4D0EB86262EC13D8EE6408@qq.com
link: https://lore.kernel.org/linux-block/tencent_2BD24B2CAFF21D4D0EB86262EC13D8EE6408@qq.com/
---

# [PATCH] blktrace: always record v2 format for the ftrace tracer

来源：[https://lore.kernel.org/linux-block/tencent_2BD24B2CAFF21D4D0EB86262EC13D8EE6408@qq.com/](https://lore.kernel.org/linux-block/tencent_2BD24B2CAFF21D4D0EB86262EC13D8EE6408@qq.com/)

```
The legacy BLKTRACESETUP ioctl creates a blk_trace with version 1, and
__blk_add_trace() wrote v1 (struct blk_io_trace) records into the ftrace
buffer. The ftrace read path, however, unconditionally parses entries as
v2 (struct blk_io_trace2): the 32-bit pid at offset 28 of a v1 record is
interpreted as the v2 action field. If the pid happens to equal
__BLK_TA_BOUNCE (14), print_one_line() hits the uninitialized hole in
what2act[] and calls a NULL .print handler, crashing with RIP 0x0.

The relay path is the only consumer of v1 records (blkparse); ftrace
always wants v2. Drop the version switch in the ftrace branch and always
record v2, keeping the existing 0 -> 2 normalization for the sysfs path.

Reported-by: syzbot+2fca70610179be6c24a4@syzkaller.appspotmail.com
Closes: https://syzkaller.appspot.com/bug?extid=2fca70610179be6c24a4
Fixes: 4d8bc7bd4f73 ("blktrace: move ftrace blk_io_tracer to blk_io_trace2")
Signed-off-by: Shuai Liu <847807867@qq.com>

---
Tested with the syzbot C reproducer on x86-64 QEMU: without this patch the
kernel panics in print_one_line() with RIP 0x0; with it, reading
/sys/kernel/tracing/trace returns 2958 bytes of correctly parsed events.

Developed with AI assistance (code analysis and patch drafting); all changes
reviewed and runtime-verified by me.
---
 kernel/trace/blktrace.c | 72 +++++++++++------------------------------
 1 file changed, 18 insertions(+), 54 deletions(-)

diff --git a/kernel/trace/blktrace.c b/kernel/trace/blktrace.c
index 8cd2520b4c99..a9e9fc30e5ef 100644
--- a/kernel/trace/blktrace.c
+++ b/kernel/trace/blktrace.c
@@ -385,66 +385,30 @@ static void __blk_add_trace(struct blk_trace *bt, sector_t sector, int bytes,
 	if (blk_tracer) {
 		buffer = blk_tr->array_buffer.buffer;
 		trace_ctx = tracing_gen_ctx_flags(0);
-		switch (bt->version) {
-		case 1:
-			trace_len = sizeof(struct blk_io_trace);
-			break;
-		case 2:
-		default:
-			/*
-			 * ftrace always uses v2 (blk_io_trace2) format.
-			 *
-			 * For sysfs-enabled tracing path (enabled via
-			 * /sys/block/DEV/trace/enable), blk_trace_setup_queue()
-			 * never initializes bt->version, leaving it 0 from
-			 * kzalloc(). We must handle version==0 safely here.
-			 *
-			 * Fall through to default to ensure we never hit the
-			 * old bug where default set trace_len=0, causing
-			 * buffer underflow and memory corruption.
-			 *
-			 * Always use v2 format for ftrace and normalize
-			 * bt->version to 2 when uninitialized.
-			 */
-			trace_len = sizeof(struct blk_io_trace2);
-			if (bt->version == 0)
-				bt->version = 2;
-			break;
-		}
-		trace_len += pdu_len + cgid_len;
+		/*
+		 * ftrace always consumes v2 (blk_io_trace2) records, no matter
+		 * which format was requested through BLKTRACESETUP. The v1
+		 * layout is only meaningful for the relay buffer read by
+		 * blkparse. Recording v1 here made print_one_line() read the
+		 * 32-bit pid as the action field, which could call a NULL
+		 * handler.
+		 *
+		 * The sysfs-enabled path never initializes bt->version, so
+		 * normalize an uninitialized version to v2 as well.
+		 */
+		if (bt->version == 0)
+			bt->version = 2;
+		trace_len = sizeof(struct blk_io_trace2) + pdu_len + cgid_len;
 		event = trace_buffer_lock_reserve(buffer, TRACE_BLK,
 						  trace_len, trace_ctx);
 		if (!event)
 			return;
 
 		tracing_record_cmdline(current);
-		switch (bt->version) {
-		case 1:
-			record_blktrace_event(ring_buffer_event_data(event),
-					      pid, cpu, sector, bytes,
-					      what, bt->dev, error, cgid, cgid_len,
-					      pdu_data, pdu_len);
-			break;
-		case 2:
-		default:
-			/*
-			 * Use v2 recording function (record_blktrace_event2)
-			 * which writes blk_io_trace2 structure with correct
-			 * field layout:
-			 *   - 32-bit pid at offset 28
-			 *   - 64-bit action at offset 32
-			 *
-			 * Fall through to default handles version==0 case
-			 * (from sysfs path), ensuring we always use correct
-			 * v2 recording function to match the v2 buffer
-			 * allocated above.
-			 */
-			record_blktrace_event2(ring_buffer_event_data(event),
-					       pid, cpu, sector, bytes,
-					       what, bt->dev, error, cgid, cgid_len,
-					       pdu_data, pdu_len);
-			break;
-		}
+		record_blktrace_event2(ring_buffer_event_data(event),
+				       pid, cpu, sector, bytes,
+				       what, bt->dev, error, cgid, cgid_len,
+				       pdu_data, pdu_len);
 
 		trace_buffer_unlock_commit(blk_tr, buffer, event, trace_ctx);
 		return;
-- 
2.53.0
```
