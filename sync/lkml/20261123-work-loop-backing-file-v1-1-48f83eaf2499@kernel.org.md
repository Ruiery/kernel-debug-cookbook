---
title: [PATCH 1/2] jfs: wait for lbmDONE under LCACHE_LOCK in lbmRead()
list: linux-block
message_id: 20261123-work-loop-backing-file-v1-1-48f83eaf2499@kernel.org
link: https://lore.kernel.org/linux-block/20261123-work-loop-backing-file-v1-1-48f83eaf2499@kernel.org/
---

# [PATCH 1/2] jfs: wait for lbmDONE under LCACHE_LOCK in lbmRead()

来源：[https://lore.kernel.org/linux-block/20261123-work-loop-backing-file-v1-1-48f83eaf2499@kernel.org/](https://lore.kernel.org/linux-block/20261123-work-loop-backing-file-v1-1-48f83eaf2499@kernel.org/)

```
lbmRead() waits for the read without taking LCACHE_LOCK and returns as
soon as bp->l_flag is no longer lbmREAD. Since commit b15e4310633f
("jfs: Set the lbmDone flag at the end of lbmIODone") lbmIODone() clears
lbmREAD and wakes the reader first and only sets lbmDONE right before it
drops LCACHE_LOCK. So the reader can already be using the buffer again
when lbmIODone() ORs lbmDONE into bp->l_flag.

lmLogShutdown() reads the log superblock, updates it and writes it back
via lbmDirectWrite(). lbmDirectWrite() sets bp->l_flag without taking
LCACHE_LOCK and submits the write. If that store happens before the late
lbmDONE from the read completion then the write is marked as done before
it has even been issued:

  umount                                  read completion
  ======                                  ===============
  lmLogShutdown()
  -> lbmRead(log, 1, &bpsuper)
                                          lbmIODone()
                                          -> LCACHE_LOCK()
                                             bp->l_flag &= ~lbmREAD
                                             wake_up(&bp->l_ioevent)
     // bp->l_flag != lbmREAD
  -> lbmDirectWrite(log, bpsuper, ...)
     bp->l_flag = lbmWRITE | lbmRELEASE | lbmSYNC | lbmDIRECT
     submit_bio()
  -> lbmIOWait(bpsuper, lbmFREE)
     -> LCACHE_LOCK()
                                             bp->l_flag |= lbmDONE
                                             LCACHE_UNLOCK()
        // lbmDONE is set, don't wait
  -> lbmLogShutdown()
     // free all lbufs and their pages

lmLogShutdown() returns, the unmount finishes and the block device is
released while the superblock write is still queued. What happens next
depends on who gets there first. If the write is still sitting in the
loop device when the device is torn down then __loop_clr_fd() has
already cleared lo->lo_backing_file and the loop worker dereferences
NULL:

  KASAN: null-ptr-deref in range [0x00000000000000a0-0x00000000000000a7]
  Workqueue: loop6 loop_workfn
  RIP: 0010:file_inode include/linux/fs.h:1351 [inline]
  RIP: 0010:kiocb_start_write include/linux/fs.h:2797 [inline]
  RIP: 0010:lo_rw_aio+0xc26/0x1100 drivers/block/loop.c:398
  Call Trace:
   do_req_filebacked drivers/block/loop.c:430 [inline]
   loop_handle_cmd drivers/block/loop.c:1847 [inline]
   loop_process_work+0x638/0x11d0 drivers/block/loop.c:1882
   process_one_work kernel/workqueue.c:3495 [inline]
   process_scheduled_works+0xc3d/0x1630 kernel/workqueue.c:3578
   worker_thread+0xa47/0xfb0 kernel/workqueue.c:3659
   kthread+0x38b/0x470 kernel/kthread.c:436

If the loop worker gets to it first the freed page is written to the
backing file and lbmIODone() then runs on the freed lbuf:

  BUG: KASAN: slab-use-after-free in lbmIODone+0x130e/0x16b0 fs/jfs/jfs_logmgr.c:2192
  Read of size 4 by task ksoftirqd/0/16
  Call Trace:
   lbmIODone+0x130e/0x16b0 fs/jfs/jfs_logmgr.c:2192
   blk_update_request+0x57b/0xe50 block/blk-mq.c:1036
   blk_mq_end_request+0x3e/0x70 block/blk-mq.c:1167
   blk_complete_reqs block/blk-mq.c:1242 [inline]
   blk_done_softirq+0x10a/0x160 block/blk-mq.c:1247
   handle_softirqs+0x1d4/0x6c0 kernel/softirq.c:669
   run_ksoftirqd+0x53/0x190 kernel/softirq.c:1133
  Freed by task 5632:
   kfree+0x1c7/0x6d0 mm/slub.c:6930
   lbmLogShutdown fs/jfs/jfs_logmgr.c:1862 [inline]
   lmLogShutdown+0x456/0x850 fs/jfs/jfs_logmgr.c:1681
   lmLogClose+0x28c/0x530 fs/jfs/jfs_logmgr.c:1457
   jfs_umount+0x2da/0x3b0 fs/jfs/jfs_umount.c:124
   jfs_put_super+0x8c/0x190 fs/jfs/super.c:194
   generic_shutdown_super+0x140/0x2d0 fs/super.c:723
   kill_block_super+0x44/0xa0 fs/super.c:1852
   cleanup_mnt+0x204/0x2a0 fs/namespace.c:1396

If the loop worker got hold of lo->lo_backing_file right before
__loop_clr_fd() cleared it then it writes through a file that is being
released instead. That's syzbot's "WARNING in file_remove_privs_flags".
I haven't seen that one in my runs but in all four logs of it that
syzbot kept the process that owns the loop device had mounted a jfs
image a few seconds earlier.

On PREEMPT_RT LCACHE_LOCK doesn't disable preemption. The woken umount
task preempts the completion on the same CPU, gets all the way to
lbmIOWait() and only then lets the completion finish. With syzbot's
reproducer that happens in about one out of 70 unmounts. Without
PREEMPT_RT the umount task has to be running on another CPU already and
I've only seen it once in 26400 unmounts. lmLogFileSystem() does the
same read, update and direct write of the log superblock for external
logs.

The lockless wait isn't new. Before commit b15e4310633f ("jfs: Set the
lbmDone flag at the end of lbmIODone") lbmIODone() set lbmDONE first and
that ended the reader's wait early as well. lbmDirectWrite()'s
store could then get lost in lbmIODone()'s read-modify-write of
bp->l_flag when it cleared lbmREAD, leaving nothing but lbmDONE behind.
That window was a lot smaller but syzbot hit it too.

So wait for the read via lbmIOWait() which waits for lbmDONE under
LCACHE_LOCK. lbmIODone() sets lbmDONE and drops the lock as the last
thing it does so once lbmIOWait() returns the completion is done with
the buffer. Note that lbmRead() keeps ignoring lbmERROR like it did
before. That's a separate problem.

Link: https://lore.kernel.org/69e2ca14.a00a0220.1bd0ca.0031.GAE@google.com
Fixes: 1da177e4c3f4 ("Linux-2.6.12-rc2")
Fixes: b15e4310633f ("jfs: Set the lbmDone flag at the end of lbmIODone")
Cc: stable@vger.kernel.org
Reported-by: syzbot+cd8a9a308e879a4e2c28@syzkaller.appspotmail.com
Closes: https://syzkaller.appspot.com/bug?extid=cd8a9a308e879a4e2c28
Reported-by: syzbot+ecf51a7ccb6b1394e90c@syzkaller.appspotmail.com
Closes: https://syzkaller.appspot.com/bug?extid=ecf51a7ccb6b1394e90c
Reported-by: syzbot+bc273027d5643e48e5b3@syzkaller.appspotmail.com
Closes: https://syzkaller.appspot.com/bug?extid=bc273027d5643e48e5b3
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/jfs/jfs_logmgr.c | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/fs/jfs/jfs_logmgr.c b/fs/jfs/jfs_logmgr.c
index 306165e61438c..e96593d79a1df 100644
--- a/fs/jfs/jfs_logmgr.c
+++ b/fs/jfs/jfs_logmgr.c
@@ -1984,7 +1984,7 @@ static int lbmRead(struct jfs_log * log, int pn, struct lbuf ** bpp)
 		submit_bio(bio);
 	}
 
-	wait_event(bp->l_ioevent, (bp->l_flag != lbmREAD));
+	lbmIOWait(bp, 0);
 
 	return 0;
 }

-- 
2.53.0
```
