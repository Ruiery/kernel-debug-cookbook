---
title: [PATCH v5 2/2] loop: Perform __loop_clr_fd() from post_release callback.
list: linux-block
message_id: 1bced9b4-83df-4702-81ac-fc0c44baeeac@I-love.SAKURA.ne.jp
link: https://lore.kernel.org/linux-block/1bced9b4-83df-4702-81ac-fc0c44baeeac@I-love.SAKURA.ne.jp/
---

# [PATCH v5 2/2] loop: Perform __loop_clr_fd() from post_release callback.

来源：[https://lore.kernel.org/linux-block/1bced9b4-83df-4702-81ac-fc0c44baeeac@I-love.SAKURA.ne.jp/](https://lore.kernel.org/linux-block/1bced9b4-83df-4702-81ac-fc0c44baeeac@I-love.SAKURA.ne.jp/)

```
syzbot is reporting NULL pointer dereference in lo_rw_aio().
An analysis by the Gemini AI collaborator considers that this problem
is caused by a timing shift primarily exposed by commit 65565ca5f99b
("block: unify the synchronous bi_end_io callbacks"), along with helper
refactorings like commit 92c3737a2473 ("block: add a bio_submit_or_kill
helper").

But due to difficulty of reproducing this race, discussion about what is
happening and how to fix this problem is stalling. Also, we haven't
identified how many filesystems are subjected to this problem.

Therefore, introduce a grace period for flushing outstanding I/O
(which should be a good thing from the perspective of defensive
programming) so that we won't hit NULL pointer dereference problem.

Since calling drain_workqueue() from __loop_clr_fd() with disk->open_mutex
held causes lockdep warnings, call __loop_clr_fd() from lo_post_release().
Use rundown_owner for remembering who is responsible for calling
__loop_clr_fd() from lo_post_release().

Link: https://lkml.kernel.org/r/fbb3edda-f108-4e5b-acf2-266f043f8125@I-love.SAKURA.ne.jp
Reported-by: syzbot+cd8a9a308e879a4e2c28@syzkaller.appspotmail.com
Closes: https://syzkaller.appspot.com/bug?extid=cd8a9a308e879a4e2c28
Reported-by: syzbot+bc273027d5643e48e5b3@syzkaller.appspotmail.com
Closes: https://syzkaller.appspot.com/bug?extid=bc273027d5643e48e5b3
Depends-on: "block: Add post_release() operation"
Fixes: 65565ca5f99b ("block: unify the synchronous bi_end_io callbacks")
Assisted-by: Gemini-Pro
Signed-off-by: Tetsuo Handa <penguin-kernel@I-love.SAKURA.ne.jp>
Reviewed-by: Bart Van Assche <bvanassche@acm.org>
---
 drivers/block/loop.c | 66 ++++++++++++++++++++++++++++++++++----------
 1 file changed, 52 insertions(+), 14 deletions(-)

diff --git a/drivers/block/loop.c b/drivers/block/loop.c
index 758c20678bf6..45543c338717 100644
--- a/drivers/block/loop.c
+++ b/drivers/block/loop.c
@@ -75,6 +75,7 @@ struct loop_device {
 	struct gendisk		*lo_disk;
 	struct mutex		lo_mutex;
 	bool			idr_visible;
+	struct task_struct	*rundown_owner;
 };
 
 struct loop_cmd {
@@ -1138,11 +1139,39 @@ static int loop_configure(struct loop_device *lo, blk_mode_t mode,
 
 static void __loop_clr_fd(struct loop_device *lo)
 {
+	struct gendisk *disk = lo->lo_disk;
 	struct queue_limits lim;
 	struct file *filp;
 	gfp_t gfp = lo->old_gfp_mask;
 	int err;
 
+	/* Step 1: Flush all outstanding I/O, without open_mutex held. */
+	/*
+	 * Since loop_queue_rq() is called with RCU read lock, this synchronize_rcu()
+	 * makes sure that no more queue_work() calls are made from loop_queue_work()
+	 * from loop_queue_rq(). Subsequent loop_queue_rq() calls which are made after
+	 * this synchronize_rcu() returned shall see lo->lo_state != Lo_bound and
+	 * return with BLK_STS_IOERR.
+	 */
+	synchronize_rcu();
+	/*
+	 * This drain_workqueue() makes sure that no more loop_handle_cmd() calls are
+	 * made from loop_process_work() from loop_workfn()/loop_rootcg_workfn().
+	 */
+	drain_workqueue(lo->workqueue);
+	/*
+	 * This blk_mq_freeze_queue() waits for completion of all outstanding I/O
+	 * which has been scheduled via loop_queue_rq(), by waiting for q_usage_counter
+	 * to reach 0. Since the lo->lo_state != Lo_bound check in loop_queue_rq()
+	 * guarantees that no more new I/O requests are made, we can call
+	 * blk_mq_unfreeze_queue() immediately after blk_mq_freeze_queue() returns.
+	 */
+	blk_mq_unfreeze_queue(lo->lo_queue, blk_mq_freeze_queue(lo->lo_queue));
+
+	/* Step 2: Perform remaining cleanup, with open_mutex held. */
+	mutex_lock(&disk->open_mutex);
+	WARN_ON_ONCE(lo->lo_state != Lo_rundown);
+
 	spin_lock_irq(&lo->lo_lock);
 	filp = lo->lo_backing_file;
 	lo->lo_backing_file = NULL;
@@ -1153,12 +1182,7 @@ static void __loop_clr_fd(struct loop_device *lo)
 	lo->lo_sizelimit = 0;
 	memset(lo->lo_file_name, 0, LO_NAME_SIZE);
 
-	/*
-	 * Reset the block size to the default.
-	 *
-	 * No queue freezing needed because this is called from the final
-	 * ->release call only, so there can't be any outstanding I/O.
-	 */
+	/* Reset the block size to the default. */
 	lim = queue_limits_start_update(lo->lo_queue);
 	lim.logical_block_size = SECTOR_SIZE;
 	lim.physical_block_size = SECTOR_SIZE;
@@ -1201,11 +1225,9 @@ static void __loop_clr_fd(struct loop_device *lo)
 	WRITE_ONCE(lo->lo_state, Lo_unbound);
 	mutex_unlock(&lo->lo_mutex);
 
-	/*
-	 * Need not hold lo_mutex to fput backing file. Calling fput holding
-	 * lo_mutex triggers a circular lock dependency possibility warning as
-	 * fput can take open_mutex which is usually taken before lo_mutex.
-	 */
+	/* Step 3: Drop refcounts, without open_mutex held. */
+	mutex_unlock(&disk->open_mutex);
+
 	fput(filp);
 }
 
@@ -1754,7 +1776,6 @@ static int lo_open(struct gendisk *disk, blk_mode_t mode)
 static void lo_release(struct gendisk *disk)
 {
 	struct loop_device *lo = disk->private_data;
-	bool need_clear = false;
 
 	if (disk_openers(disk) > 0)
 		return;
@@ -1768,11 +1789,27 @@ static void lo_release(struct gendisk *disk)
 	if (lo->lo_state == Lo_bound && (lo->lo_flags & LO_FLAGS_AUTOCLEAR))
 		WRITE_ONCE(lo->lo_state, Lo_rundown);
 
-	need_clear = (lo->lo_state == Lo_rundown);
+	/*
+	 * In order to flush outstanding I/O (without open_mutex for deadlock
+	 * avoidance) before clearing the backing device, defer __loop_clr_fd()
+	 * to lo_post_release().
+	 * The Lo_rundown state guarantees that lo_open() will fail with -ENXIO.
+	 * The failing lo_open() guarantees that lo_release() will not overwrite
+	 * lo->rundown_owner until __loop_clr_fd() resets to the Lo_unbound state.
+	 */
+	if (lo->lo_state == Lo_rundown)
+		WRITE_ONCE(lo->rundown_owner, current);
 	mutex_unlock(&lo->lo_mutex);
+}
 
-	if (need_clear)
+static void lo_post_release(struct gendisk *disk)
+{
+	struct loop_device *lo = disk->private_data;
+
+	if (READ_ONCE(lo->rundown_owner) == current) {
+		WRITE_ONCE(lo->rundown_owner, NULL);
 		__loop_clr_fd(lo);
+	}
 }
 
 static void lo_free_disk(struct gendisk *disk)
@@ -1791,6 +1828,7 @@ static const struct block_device_operations lo_fops = {
 	.owner =	THIS_MODULE,
 	.open =         lo_open,
 	.release =	lo_release,
+	.post_release =	lo_post_release,
 	.ioctl =	lo_ioctl,
 #ifdef CONFIG_COMPAT
 	.compat_ioctl =	lo_compat_ioctl,
-- 
2.52.0
```
