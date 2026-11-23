---
title: [PATCH 2/2] jfs: set lbmDONE before dropping LCACHE_LOCK for lmPostGC()
list: linux-block
message_id: 20261123-work-loop-backing-file-v1-2-48f83eaf2499@kernel.org
link: https://lore.kernel.org/linux-block/20261123-work-loop-backing-file-v1-2-48f83eaf2499@kernel.org/
---

# [PATCH 2/2] jfs: set lbmDONE before dropping LCACHE_LOCK for lmPostGC()

来源：[https://lore.kernel.org/linux-block/20261123-work-loop-backing-file-v1-2-48f83eaf2499@kernel.org/](https://lore.kernel.org/linux-block/20261123-work-loop-backing-file-v1-2-48f83eaf2499@kernel.org/)

```
Since commit b15e4310633f ("jfs: Set the lbmDone flag at the end of
lbmIODone") lbmIODone() sets lbmDONE as the very last thing. For a group
commit write that means after it dropped LCACHE_LOCK, called lmPostGC()
and took the lock again. But lmPostGC() can hand the buffer back to the
freelist via lbmFree() or queue it for the next write via lbmWrite(),
and the buffer of the current log page is written by group commit over
and over. So the lbmDONE set afterwards can land on the next I/O of the
buffer.

At unmount lmLogShutdown() writes the current log page via lbmWrite()
and waits for it via lbmIOWait(log->bp, lbmFREE). If the completion of
an earlier group commit write of that page sets its lbmDONE in between
then lbmIOWait() returns while the page is still in flight and on the
write queue and lbmfree() asserts:

  BUG at fs/jfs/jfs_logmgr.c:1919 assert(bp->l_wqnext == NULL)
  kernel BUG at fs/jfs/jfs_logmgr.c:1919!
  RIP: 0010:lbmfree fs/jfs/jfs_logmgr.c:1919 [inline]
  RIP: 0010:lbmIOWait+0x5ab/0x5b0 fs/jfs/jfs_logmgr.c:2154
  Call Trace:
   lmLogShutdown+0x1ff/0x850 fs/jfs/jfs_logmgr.c:1657
   lmLogClose+0x28c/0x530 fs/jfs/jfs_logmgr.c:1457
   jfs_umount+0x2da/0x3b0 fs/jfs/jfs_umount.c:124
   jfs_put_super+0x8c/0x190 fs/jfs/super.c:194
   generic_shutdown_super+0x13d/0x2d0 fs/super.c:751
   kill_block_super+0x44/0xa0 fs/super.c:1903
   deactivate_locked_super+0xbe/0x110 fs/super.c:586
   cleanup_mnt+0x204/0x2a0 fs/namespace.c:1396

In my build of the same config R12 holds bp->l_flag at that point and in
the report it is 0x2e, i.e., lbmWRITE | lbmRELEASE | lbmSYNC | lbmDONE.
So the completion of the write lmLogShutdown() waits for hasn't run yet
and lbmDONE came from somewhere else. A completion that only gets to the
buffer after lbmWrite() stored those flags takes them for its own,
clears lbmWRITE and takes the buffer off the write queue. A read
completion clears lbmREAD and sets lbmDONE under the same LCACHE_LOCK.
The group commit branch is the only place in lbmIODone() that drops
LCACHE_LOCK before it sets lbmDONE.

With a workload that writes and fsyncs a few files before every unmount
on PREEMPT_RT the late lbmDONE lands on a new I/O of the buffer in about
one out of ten group commit completions. Mostly that's the next write
lmPostGC() itself just queued. But in about one out of 1800 completions
another task reinitialized the buffer while the lock was dropped.
Preempted completions kept it dropped for up to 14 ms. I haven't seen
the late lbmDONE land on lmLogShutdown()'s final write on its own in
about a million unmounts. But with a debug patch that holds the
completion right after lmPostGC() until lmLogShutdown() has submitted
that write every VM hits exactly the BUG above within the first few
unmounts, with the same 0x2e in R12. With this patch the same delay
leaves the completion nothing to do after lmPostGC() and 15400 unmounts
run clean.

So set lbmDONE before dropping the lock for lmPostGC() like lbmIODone()
did before commit b15e4310633f ("jfs: Set the lbmDone flag at the end of
lbmIODone") and don't touch the buffer after lmPostGC(). That doesn't
bring back what that commit fixed. That was lbmRead() returning while
lbmIODone() still used the buffer. Nobody waits for lbmDONE on a group
commit write. The transactions wait for their commit records via
tblkGC_COMMITTED instead.

Fixes: b15e4310633f ("jfs: Set the lbmDone flag at the end of lbmIODone")
Cc: stable@vger.kernel.org
Reported-by: syzbot+2e5cf2352e9f69ebf172@syzkaller.appspotmail.com
Closes: https://syzkaller.appspot.com/bug?extid=2e5cf2352e9f69ebf172
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/jfs/jfs_logmgr.c | 4 +++-
 1 file changed, 3 insertions(+), 1 deletion(-)

diff --git a/fs/jfs/jfs_logmgr.c b/fs/jfs/jfs_logmgr.c
index e96593d79a1df..ae3bd0cd85471 100644
--- a/fs/jfs/jfs_logmgr.c
+++ b/fs/jfs/jfs_logmgr.c
@@ -2279,9 +2279,11 @@ static void lbmIODone(struct bio *bio)
 	 *	Group Commit pageout:
 	 */
 	else if (bp->l_flag & lbmGC) {
+		/* lmPostGC() may free or requeue @bp. */
+		bp->l_flag |= lbmDONE;
 		LCACHE_UNLOCK(flags);
 		lmPostGC(bp);
-		LCACHE_LOCK(flags);		/* disable+lock */
+		return;
 	}
 
 	/*

-- 
2.53.0
```
