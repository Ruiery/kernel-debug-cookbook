---
title: [PATCH v6 0/1] block/blk-mq: use atomic_t for quiesce_depth to avoid lock contention on RT
list: linux-rt-users
message_id: cover.1778048987.git.ionut.nechita@windriver.com
link: https://lore.kernel.org/linux-rt-users/cover.1778048987.git.ionut.nechita@windriver.com/
---

# [PATCH v6 0/1] block/blk-mq: use atomic_t for quiesce_depth to avoid lock contention on RT

来源：[https://lore.kernel.org/linux-rt-users/cover.1778048987.git.ionut.nechita@windriver.com/](https://lore.kernel.org/linux-rt-users/cover.1778048987.git.ionut.nechita@windriver.com/)

```
Hi Jens,

This is v6 of the fix for the RT kernel performance regression caused by
commit 6bda857bcbb86 ("block: fix ordering between checking
QUEUE_FLAG_QUIESCED request adding").

Changes since v5 (Mar 3):
- Rewrote the memory-ordering comments per Bart Van Assche's review.
  The previous wording incorrectly described smp_mb__after_atomic() as
  ordering against "subsequent loads in blk_mq_run_hw_queue()". The
  comments now describe the actual reader/writer pairing: writer-side
  smp_mb__after_atomic() in blk_mq_quiesce_queue_nowait() and
  blk_mq_unquiesce_queue() pairs with reader-side smp_rmb() in
  blk_mq_run_hw_queue() so the re-check observes the latest
  quiesce_depth value.
- Rebased on top of linux-next (next-20260505).
- No functional / code-generation changes.

Changes since v4 (Feb 13):
- Rebased on top of linux-next (20260302)
- No code changes

Changes since v3 (Feb 11):
- Rebased on top of axboe/for-7.0/block
- Fixed Fixes tag commit hash to match upstream (6bda857bcbb86)
- Added Reviewed-by from Sebastian Andrzej Siewior
- No code changes

Changes since v2 (Feb 10):
- Replaced raw_spinlock_t quiesce_sync_lock with atomic_t for
  quiesce_depth, as suggested by Sebastian Andrzej Siewior
- Eliminated QUEUE_FLAG_QUIESCED entirely; blk_queue_quiesced() now
  checks atomic_read(&q->quiesce_depth) > 0
- Use atomic_dec_if_positive() in blk_mq_unquiesce_queue() to avoid
  race between WARN check and decrement
- Removed the unrelated blk_mq_run_hw_queues() async=true change
- Removed blk-mq-debugfs.c QUIESCED flag entry
- Uses smp_mb__after_atomic() / smp_rmb() for memory ordering instead
  of any spinlock in the hot path

Changes since v1 (RESEND, Jan 9):
- Rebased on top of axboe/for-7.0/block
- No code changes

The problem: on PREEMPT_RT kernels, the spinlock_t queue_lock added in
blk_mq_run_hw_queue() converts to a sleeping rt_mutex, causing all IRQ
threads (one per MSI-X vector) to serialize. On megaraid_sas with 128
MSI-X vectors and 120 hw queues, throughput drops from 640 MB/s to
153 MB/s.

The fix converts quiesce_depth to atomic_t, which serves as both the
depth tracker and the quiesce indicator (depth > 0 means quiesced).
This eliminates QUEUE_FLAG_QUIESCED and removes the need for any lock
in the hot path. Memory ordering is ensured by smp_mb__after_atomic()
on the writer side (after modifying quiesce_depth) paired with
smp_rmb() on the reader side (before re-checking quiesce state in
blk_mq_run_hw_queue()).

Link: https://lore.kernel.org/linux-block/20260303073744.20585-1-ionut.nechita@windriver.com/

Ionut Nechita (1):
  block/blk-mq: use atomic_t for quiesce_depth to avoid lock contention
    on RT

 block/blk-core.c       |  1 +
 block/blk-mq-debugfs.c |  1 -
 block/blk-mq.c         | 53 +++++++++++++++++++++---------------------
 include/linux/blkdev.h |  9 ++++---
 4 files changed, 34 insertions(+), 30 deletions(-)

--
2.54.0
```
