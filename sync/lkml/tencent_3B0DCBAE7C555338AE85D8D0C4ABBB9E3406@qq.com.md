---
title: [PATCH] block: release queue freeze lockdep locks under mq_freeze_lock
list: linux-block
message_id: tencent_3B0DCBAE7C555338AE85D8D0C4ABBB9E3406@qq.com
link: https://lore.kernel.org/linux-block/tencent_3B0DCBAE7C555338AE85D8D0C4ABBB9E3406@qq.com/
---

# [PATCH] block: release queue freeze lockdep locks under mq_freeze_lock

来源：[https://lore.kernel.org/linux-block/tencent_3B0DCBAE7C555338AE85D8D0C4ABBB9E3406@qq.com/](https://lore.kernel.org/linux-block/tencent_3B0DCBAE7C555338AE85D8D0C4ABBB9E3406@qq.com/)

```
The lockdep model for the queue freeze owner decides whether to acquire
the q_usage_counter io and queue lockdep maps based on
mq_freeze_disk_dead and mq_freeze_queue_dying.  These two flags are
re-sampled by blk_freeze_set_owner() whenever the freeze depth drops to
zero, i.e. after the previous owner released its freeze.

blk_mq_unfreeze_queue_nomemrestore() used to release the matching
lockdep locks only after dropping mq_freeze_lock.  Between dropping the
lock and reading the live flags a new freeze can run
blk_freeze_set_owner() and flip the flags from false to true if the disk
dies in that window.  The original owner then observes the flipped
flags and skips the release, leaking both lockdep maps, which triggers
"WARNING: lock held when returning to user space" with
&q->q_usage_counter(io) and &q->q_usage_counter(queue) still held.

Perform the lockdep release while still holding mq_freeze_lock so that
blk_freeze_set_owner() cannot interleave and the flags observed at
release match the values sampled at acquire time.

Fixes: 6f491a8d4b92 ("block: track disk DEAD state automatically for modeling queue freeze lockdep")
Reported-by: syzbot+1eb53c83ab8b0a0302a6@syzkaller.appspotmail.com
Closes: https://syzkaller.appspot.com/bug?id=1eb53c83ab8b0a0302a6
Signed-off-by: Shuai Liu <847807867@qq.com>
---
 block/blk-mq.c | 30 ++++++++++++++++++++++++------
 1 file changed, 24 insertions(+), 6 deletions(-)

diff --git a/block/blk-mq.c b/block/blk-mq.c
index 025a799f35b9..db769c7c88ff 100644
--- a/block/blk-mq.c
+++ b/block/blk-mq.c
@@ -208,11 +208,10 @@ void blk_mq_freeze_queue_nomemsave(struct request_queue *q)
 }
 EXPORT_SYMBOL_GPL(blk_mq_freeze_queue_nomemsave);
 
-bool __blk_mq_unfreeze_queue(struct request_queue *q, bool force_atomic)
+/* caller has to hold q->mq_freeze_lock */
+static bool __blk_mq_unfreeze_queue_locked(struct request_queue *q,
+					   bool force_atomic)
 {
-	bool unfreeze;
-
-	mutex_lock(&q->mq_freeze_lock);
 	if (force_atomic)
 		q->q_usage_counter.data->force_atomic = true;
 	q->mq_freeze_depth--;
@@ -221,7 +220,15 @@ bool __blk_mq_unfreeze_queue(struct request_queue *q, bool force_atomic)
 		percpu_ref_resurrect(&q->q_usage_counter);
 		wake_up_all(&q->mq_freeze_wq);
 	}
-	unfreeze = blk_unfreeze_check_owner(q);
+	return blk_unfreeze_check_owner(q);
+}
+
+bool __blk_mq_unfreeze_queue(struct request_queue *q, bool force_atomic)
+{
+	bool unfreeze;
+
+	mutex_lock(&q->mq_freeze_lock);
+	unfreeze = __blk_mq_unfreeze_queue_locked(q, force_atomic);
 	mutex_unlock(&q->mq_freeze_lock);
 
 	return unfreeze;
@@ -229,8 +236,19 @@ bool __blk_mq_unfreeze_queue(struct request_queue *q, bool force_atomic)
 
 void blk_mq_unfreeze_queue_nomemrestore(struct request_queue *q)
 {
-	if (__blk_mq_unfreeze_queue(q, false))
+	mutex_lock(&q->mq_freeze_lock);
+	/*
+	 * Release the lockdep freeze locks while still holding
+	 * mq_freeze_lock.  blk_freeze_set_owner() re-samples
+	 * mq_freeze_disk_dead/mq_freeze_queue_dying once the freeze depth
+	 * reaches zero, and reading the flags after dropping the lock races
+	 * with that re-sampling: if the disk died in between, the flags flip
+	 * and the release is skipped even though the matching acquire
+	 * grabbed the locks, leaking them.
+	 */
+	if (__blk_mq_unfreeze_queue_locked(q, false))
 		blk_unfreeze_release_lock(q);
+	mutex_unlock(&q->mq_freeze_lock);
 }
 EXPORT_SYMBOL_GPL(blk_mq_unfreeze_queue_nomemrestore);
 
-- 
2.53.0
```
