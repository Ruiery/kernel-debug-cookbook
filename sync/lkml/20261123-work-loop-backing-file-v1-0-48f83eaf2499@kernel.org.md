---
title: [PATCH 0/2] jfs: fix lbmDONE races in lbmIODone() (was "loop bug saga")
list: linux-block
message_id: 20261123-work-loop-backing-file-v1-0-48f83eaf2499@kernel.org
link: https://lore.kernel.org/linux-block/20261123-work-loop-backing-file-v1-0-48f83eaf2499@kernel.org/
---

# [PATCH 0/2] jfs: fix lbmDONE races in lbmIODone() (was "loop bug saga")

来源：[https://lore.kernel.org/linux-block/20261123-work-loop-backing-file-v1-0-48f83eaf2499@kernel.org/](https://lore.kernel.org/linux-block/20261123-work-loop-backing-file-v1-0-48f83eaf2499@kernel.org/)

```
This is the root cause of syzbot's "general protection fault in
lo_rw_aio" (cf. [1]) which got a lot of loop patches over the last
months (cf. [2]). It's not a loop bug. jfs releases the block device
while its own log superblock write is still queued and the loop device
gets torn down underneath it. Bart already pointed at b15e4310633f
("jfs: Set the lbmDone flag at the end of lbmIODone") in [3].

Since b15e4310633f lbmIODone() sets lbmDONE as the last thing it does.
lbmRead() doesn't take LCACHE_LOCK and returns as soon as lbmREAD is
gone. So in lmLogShutdown() the late lbmDONE of the read completion can
land on the superblock write that lbmDirectWrite() just submitted.
lbmIOWait() returns right away, jfs frees the buffers and the unmount
finishes. The first patch makes lbmRead() wait for lbmDONE under
LCACHE_LOCK.

On PREEMPT_RT the woken umount task preempts the completion that holds
LCACHE_LOCK on the same CPU, so this happens all the time. With the
reproducer from [4] every RT VM I booted hit the lbmIODone() UAF within
a minute and the lo_rw_aio() NULL deref a few seconds later. With some
instrumentation that's an early lbmIOWait() return in about one out of
70 unmounts. Without PREEMPT_RT I've seen it once in 26400 unmounts.
With the first patch applied it's zero in 19200 unmounts and the
reproducer doesn't trigger anything anymore.

The lockless wait in lbmRead() isn't new. Before b15e4310633f the early
return let lbmDirectWrite()'s flags get lost in the read-modify-write
that clears lbmREAD instead. That's the much rarer pre-7.1 version
syzbot hit in [4]. With b15e4310633f reverted I've seen it once in
244600 unmounts.

The second patch is the group commit side of b15e4310633f. lbmIODone()
now sets lbmDONE after lmPostGC() ran with the lock dropped, which may
have freed or requeued the buffer already. That's syzbot's "kernel BUG
in lbmIOWait" (cf. [5]) and it's a lot harder to hit. On PREEMPT_RT the
late lbmDONE lands on a new I/O of the buffer in about one out of ten
group commit completions but I haven't seen it land on lmLogShutdown()'s
final write on its own in about a million unmounts. With a delay that
holds the completion after lmPostGC() until lmLogShutdown() has
submitted that write every VM hits syzbot's BUG within the first few
unmounts, down to the 0x2e in R12. With the second patch the same delay
is harmless. The details are in the patch.

None of the loop changes that were proposed are needed for this.

/*
 * I'm also appending some deets on the nilfs detour that was in the
 * original patch series so we don't have to rehash that discussion:
 */

Tetsuo's loop debug check (cf. [6]) also fired for nilfs2 on syzbot ci
(cf. [7]). His "block: wait for inflight requests in bdev_release()"
(cf. [8]) cites that report as evidence that reads leak past the
release of the block device via readahead. I looked into it and it's a
false positive of the check.

When nilfs2 searches for the super root at mount it reads ahead through
buffer heads in the page cache of the block device. If the mount fails
it doesn't wait for that readahead. That's fine because the last close
waits for it:

  bdev_release()
  -> blkdev_put_whole()
     -> blkdev_flush_mapping()
        -> kill_bdev()
           -> truncate_inode_pages()
              -> discard_buffer()
                 -> lock_buffer()

The reports are printed by the loop worker while it processes exactly
the reads that the closing task waits for. lo_release() and
__loop_clr_fd() haven't run yet and lo->lo_backing_file is still valid.
Both logs go on for more than ten seconds after the reports without a
splat.

The check fires because loop_clr_fd() already switches the device to
Lo_rundown when the caller is the only opener and blkdev_put_whole()
drops bd_openers to zero before it flushes the page cache and calls
->release(). So "lo_state != Lo_bound && disk_openers() == 0" is true
for every command a final close drains after such a LOOP_CLR_FD.
syzkaller closes the loop device before mount(2) and opens it again
afterwards to issue LOOP_CLR_FD. That only reports if another opener,
probably udevd's blkid probe, kept the device open across the mount and
closes it in between. That happened about once in 600 to 700 mounts of
those images.

There's no hole in the block layer or in mm that would let these reads
escape. The bios belong to locked buffer heads in the page cache of the
block device and nothing gets rid of those without waiting for them.
All 48 crash reports of [1] I looked at are on the write side as well.
A read would fault on file->f_op instead of in file_inode() and I
couldn't find a syzbot report like that.

So a check that wants to catch I/O after the teardown should test
whether __loop_clr_fd() has started, e.g., by looking at
lo->lo_backing_file. lo_state and the number of openers can't tell a
final close that is still draining from the teardown. The comment in
the debug patch says the state "should remain unchanged unless
__loop_clr_fd() by error starts" but loop_clr_fd() changes it.

jfs is different. It writes its log from pages it allocated itself, so
kill_bdev() never sees that I/O and nothing in the block layer can wait
for it.

[1]: https://syzkaller.appspot.com/bug?extid=cd8a9a308e879a4e2c28
[2]: https://lore.kernel.org/69e2ca14.a00a0220.1bd0ca.0031.GAE@google.com
[3]: https://lore.kernel.org/fb1e0f16346994e32b479e4be596436b2a614b03.1791234123.git.bvanassche@acm.org
[4]: https://syzkaller.appspot.com/bug?extid=ecf51a7ccb6b1394e90c
[5]: https://syzkaller.appspot.com/bug?extid=2e5cf2352e9f69ebf172
[6]: https://lore.kernel.org/cc2910d3-3113-44d4-94ef-0c8d365fac9c@I-love.SAKURA.ne.jp
[7]: https://lore.kernel.org/6acbe268.8cdf6287.1eb53.00ed.GAE@google.com
[8]: https://lore.kernel.org/81c9adbe-14f3-4d1b-8a88-8b796e91f3a9@I-love.SAKURA.ne.jp

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
Christian Brauner (2):
      jfs: wait for lbmDONE under LCACHE_LOCK in lbmRead()
      jfs: set lbmDONE before dropping LCACHE_LOCK for lmPostGC()

 fs/jfs/jfs_logmgr.c | 6 ++++--
 1 file changed, 4 insertions(+), 2 deletions(-)
---
base-commit: 2dc60bd9975fc8666a13d58410499e06e6799ba9
change-id: 20261123-work-loop-backing-file-c1d1030c3d64
```
