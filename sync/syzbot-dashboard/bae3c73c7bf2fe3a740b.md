---
title: INFO: task hung in truncate_inode_pages
subsystems: block
extid: bae3c73c7bf2fe3a740b
link: https://syzkaller.appspot.com/bug?extid=bae3c73c7bf2fe3a740b
source: syzbot-dashboard
---

# INFO: task hung in truncate_inode_pages

来源：[https://syzkaller.appspot.com/bug?extid=bae3c73c7bf2fe3a740b](https://syzkaller.appspot.com/bug?extid=bae3c73c7bf2fe3a740b)

## 崩溃报告

```
INFO: task udevd:6124 blocked for more than 143 seconds.
      Not tainted 6.7.0-rc8-syzkaller-g0802e17d9aca #0
"echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.
task:udevd           state:D stack:0     pid:6124  tgid:6124  ppid:5713   flags:0x0000000d
Call trace:
 __switch_to+0x314/0x560 arch/arm64/kernel/process.c:556
 context_switch kernel/sched/core.c:5376 [inline]
 __schedule+0x1354/0x2360 kernel/sched/core.c:6688
 __schedule_loop kernel/sched/core.c:6763 [inline]
 schedule+0xb8/0x19c kernel/sched/core.c:6778
 io_schedule+0x8c/0x12c kernel/sched/core.c:8998
 folio_wait_bit_common+0x65c/0xb90 mm/filemap.c:1273
 __folio_lock mm/filemap.c:1611 [inline]
 folio_lock include/linux/pagemap.h:1031 [inline]
 __filemap_get_folio+0x1e4/0xa60 mm/filemap.c:1864
 truncate_inode_pages_range+0x468/0xf34 mm/truncate.c:376
 truncate_inode_pages+0x2c/0x3c mm/truncate.c:448
 kill_bdev block/bdev.c:76 [inline]
 blkdev_flush_mapping+0x134/0x280 block/bdev.c:632
 blkdev_put_whole block/bdev.c:663 [inline]
 blkdev_put+0x534/0x740 block/bdev.c:944
 bdev_release+0x5c/0x78 block/bdev.c:954
 blkdev_release+0x40/0x54 block/fops.c:616
 __fput+0x308/0x8e4 fs/file_table.c:394
 ____fput+0x20/0x30 fs/file_table.c:422
 task_work_run+0x230/0x2e0 kernel/task_work.c:180
 exit_task_work include/linux/task_work.h:38 [inline]
 do_exit+0x618/0x1f64 kernel/exit.c:869
 do_group_exit+0x194/0x22c kernel/exit.c:1018
 get_signal+0x1500/0x15ec kernel/signal.c:2904
 do_signal arch/arm64/kernel/signal.c:1249 [inline]
 do_notify_resume+0x3bc/0x393c arch/arm64/kernel/signal.c:1302
 exit_to_user_mode_prepare arch/arm64/kernel/entry-common.c:137 [inline]
 exit_to_user_mode arch/arm64/kernel/entry-common.c:144 [inline]
 el0_svc+0x9c/0x158 arch/arm64/kernel/entry-common.c:679
 el0t_64_sync_handler+0x84/0xfc arch/arm64/kernel/entry-common.c:696
 el0t_64_sync+0x190/0x194 arch/arm64/kernel/entry.S:595
INFO: task syz-executor412:6368 blocked for more than 143 seconds.
      Not tainted 6.7.0-rc8-syzkaller-g0802e17d9aca #0
"echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.
task:syz-executor412 state:D stack:0     pid:6368  tgid:6367  ppid:6123   flags:0x00000005
Call trace:
 __switch_to+0x314/0x560 arch/arm64/kernel/process.c:556
 context_switch kernel/sched/core.c:5376 [inline]
 __schedule+0x1354/0x2360 kernel/sched/core.c:6688
 __schedule_loop kernel/sched/core.c:6763 [inline]
 schedule+0xb8/0x19c kernel/sched/core.c:6778
 schedule_preempt_disabled+0x18/0x2c kernel/sched/core.c:6835
 __mutex_lock_common+0xbd8/0x21a0 kernel/locking/mutex.c:679
 __mutex_lock kernel/locking/mutex.c:747 [inline]
 mutex_lock_nested+0x2c/0x38 kernel/locking/mutex.c:799
 blkdev_get_by_dev+0x114/0x55c block/bdev.c:788
 bdev_open_by_dev+0x84/0x144 block/bdev.c:842
 blkdev_open+0x134/0x33c block/fops.c:600
 do_dentry_open+0x778/0x12b4 fs/open.c:948
 vfs_open+0x7c/0x90 fs/open.c:1082
 do_open fs/namei.c:3622 [inline]
 path_openat+0x1f6c/0x2888 fs/namei.c:3779
 do_filp_open+0x1bc/0x3cc fs/namei.c:3809
 do_sys_openat2+0x124/0x1b8 fs/open.c:1437
 do_sys_open fs/open.c:1452 [inline]
 __do_sys_openat fs/open.c:1468 [inline]
 __se_sys_openat fs/open.c:1463 [inline]
 __arm64_sys_openat+0x1f0/0x240 fs/open.c:1463
 __invoke_syscall arch/arm64/kernel/syscall.c:37 [inline]
 invoke_syscall+0x98/0x2b8 arch/arm64/kernel/syscall.c:51
 el0_svc_common+0x130/0x23c arch/arm64/kernel/syscall.c:136
 do_el0_svc+0x48/0x58 arch/arm64/kernel/syscall.c:155
 el0_svc+0x54/0x158 arch/arm64/kernel/entry-common.c:678
 el0t_64_sync_handler+0x84/0xfc arch/arm64/kernel/entry-common.c:696
 el0t_64_sync+0x190/0x194 arch/arm64/kernel/entry.S:595

Showing all locks held in the system:
1 lock held by khungtaskd/29:
 #0: ffff80008e6c48c0 (rcu_read_lock){....}-{1:2}, at: rcu_lock_acquire+0xc/0x44 include/linux/rcupdate.h:300
2 locks held by getty/5863:
 #0: ffff0000d28740a0 (&tty->ldisc_sem){++++}-{0:0}, at: ldsem_down_read+0x3c/0x4c drivers/tty/tty_ldsem.c:340
 #1: ffff800094e402f0 (&ldata->atomic_read_lock){+.+.}-{3:3}, at: n_tty_read+0x41c/0x1228 drivers/tty/n_tty.c:2201
1 lock held by udevd/6124:
 #0: ffff0000c9fc94c8 (&disk->open_mutex){+.+.}-{3:3}, at: blkdev_put+0xec/0x740 block/bdev.c:930
1 lock held by syz-executor412/6368:
 #0: ffff0000c9fc94c8 (&disk->open_mutex){+.+.}-{3:3}, at: blkdev_get_by_dev+0x114/0x55c block/bdev.c:788

=============================================
```
