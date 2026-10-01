---
title: [PATCH] block: drop the cached plug time when blk_add_rq_to_plug() flushes
list: linux-block
message_id: 20260930-blk-plug-ts-flush-v1-1-bf8ca7bc5cd6@virtuozzo.com
link: https://lore.kernel.org/linux-block/20260930-blk-plug-ts-flush-v1-1-bf8ca7bc5cd6@virtuozzo.com/
---

# [PATCH] block: drop the cached plug time when blk_add_rq_to_plug() flushes

来源：[https://lore.kernel.org/linux-block/20260930-blk-plug-ts-flush-v1-1-bf8ca7bc5cd6@virtuozzo.com/](https://lore.kernel.org/linux-block/20260930-blk-plug-ts-flush-v1-1-bf8ca7bc5cd6@virtuozzo.com/)

```
blk_time_get_ns() caches the current time in the task's plug. The idea
is that the cache lives for one plug and is dropped when the plug is
flushed. __blk_flush_plug() and finish_task_switch() do that.

blk_add_rq_to_plug() also flushes, when the plug has too many requests
or the last request is at least BLK_PLUG_FLUSH_SIZE. But it calls
blk_mq_flush_plug_list() directly and never drops the cached time. So
a task that keeps submitting without sleeping stamps every request
after that with the time first cached in the plug. start_time_ns and
io_start_time_ns are stale and the disk stats charge each request for
the whole time since the plug began.

Drop the cached time after the flush, same as __blk_flush_plug() does.

Fixes: da4c8c3d0975 ("block: cache current nsec time in struct blk_plug")
Cc: stable@vger.kernel.org
Signed-off-by: Vasileios Almpanis <vasileios.almpanis@virtuozzo.com>
---
 block/blk-mq.c | 1 +
 1 file changed, 1 insertion(+)

diff --git a/block/blk-mq.c b/block/blk-mq.c
index a26a11c73ee3..7a37d9f1647d 100644
--- a/block/blk-mq.c
+++ b/block/blk-mq.c
@@ -1384,6 +1384,7 @@ static void blk_add_rq_to_plug(struct blk_plug *plug, struct request *rq)
 		   (!blk_queue_nomerges(rq->q) &&
 		    blk_rq_bytes(last) >= BLK_PLUG_FLUSH_SIZE)) {
 		blk_mq_flush_plug_list(plug, false);
+		blk_plug_invalidate_ts();
 		last = NULL;
 		trace_block_plug(rq->q);
 	}

---
base-commit: 551c722f40809618230001baccf219193e22fc5a
change-id: 20260930-blk-plug-ts-flush-365cde9630d8

-- 
Best regards, Vasileios Almpanis
Software Developer, Virtuozzo.
```
