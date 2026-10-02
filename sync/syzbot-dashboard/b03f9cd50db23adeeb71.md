---
title: possible deadlock in ocfs2_read_blocks (2)
subsystems: block,ocfs2
extid: b03f9cd50db23adeeb71
link: https://syzkaller.appspot.com/bug?extid=b03f9cd50db23adeeb71
source: syzbot-dashboard
---

# possible deadlock in ocfs2_read_blocks (2)

来源：[https://syzkaller.appspot.com/bug?extid=b03f9cd50db23adeeb71](https://syzkaller.appspot.com/bug?extid=b03f9cd50db23adeeb71)

## 崩溃报告

```
======================================================
WARNING: possible circular locking dependency detected
syzkaller #0 Tainted: G             L     
------------------------------------------------------
syz.3.993/9951 is trying to acquire lock:
ffff8880724887d0 (&oi->ip_io_mutex){+.+.}-{4:4}, at: ocfs2_read_blocks+0x1ef/0x14d0 fs/ocfs2/buffer_head_io.c:229

but task is already holding lock:
ffff888026afda68 (&q->limits_lock){+.+.}-{4:4}, at: queue_limits_start_update include/linux/blkdev.h:1101 [inline]
ffff888026afda68 (&q->limits_lock){+.+.}-{4:4}, at: loop_configure+0x787/0xdc0 drivers/block/loop.c:1083

which lock already depends on the new lock.


the existing dependency chain (in reverse order) is:

-> #2 (&q->limits_lock){+.+.}-{4:4}:
       __mutex_lock_common kernel/locking/mutex.c:646 [inline]
       __mutex_lock+0x19d/0x1550 kernel/locking/mutex.c:821
       queue_limits_start_update include/linux/blkdev.h:1101 [inline]
       loop_set_dio drivers/block/loop.c:1460 [inline]
       lo_simple_ioctl drivers/block/loop.c:1528 [inline]
       lo_ioctl+0x16ca/0x2150 drivers/block/loop.c:1594
       blkdev_ioctl+0x5e3/0x740 block/ioctl.c:798
       vfs_ioctl fs/ioctl.c:51 [inline]
       __do_sys_ioctl fs/ioctl.c:597 [inline]
       __se_sys_ioctl+0xfc/0x170 fs/ioctl.c:583
       do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
       do_syscall_64+0x166/0x520 arch/x86/entry/syscall_64.c:84
       entry_SYSCALL_64_after_hwframe+0x77/0x7f

-> #1 (&q->q_usage_counter(io)#24){++++}-{0:0}:
       bio_queue_enter block/blk.h:95 [inline]
       blk_mq_submit_bio+0x7f8/0x2a70 block/blk-mq.c:3127
       __submit_bio_noacct_mq block/blk-core.c:756 [inline]
       submit_bio_noacct_nocheck+0x2f4/0xa40 block/blk-core.c:790
       ocfs2_read_blocks+0x85e/0x14d0 fs/ocfs2/buffer_head_io.c:324
       ocfs2_read_inode_block_full fs/ocfs2/inode.c:1968 [inline]
       ocfs2_read_inode_block+0xe0/0x190 fs/ocfs2/inode.c:1980
       ocfs2_get_clusters+0x341/0xc00 fs/ocfs2/extent_map.c:625
       ocfs2_extent_map_get_blocks+0x202/0x6a0 fs/ocfs2/extent_map.c:678
       ocfs2_read_virt_blocks+0x283/0x9c0 fs/ocfs2/extent_map.c:1001
       ocfs2_read_dir_block fs/ocfs2/dir.c:522 [inline]
       ocfs2_find_entry_el fs/ocfs2/dir.c:790 [inline]
       ocfs2_find_entry+0x3c3/0x2050 fs/ocfs2/dir.c:1165
       ocfs2_find_files_on_disk+0xe0/0x340 fs/ocfs2/dir.c:2082
       ocfs2_lookup_ino_from_name+0x52/0x100 fs/ocfs2/dir.c:2104
       _ocfs2_get_system_file_inode fs/ocfs2/sysfile.c:133 [inline]
       ocfs2_get_system_file_inode+0x32f/0x810 fs/ocfs2/sysfile.c:110
       ocfs2_init_global_system_inodes+0x318/0x6e0 fs/ocfs2/super.c:461
       ocfs2_initialize_super fs/ocfs2/super.c:2192 [inline]
       ocfs2_fill_super+0x456e/0x6840 fs/ocfs2/super.c:993
       get_tree_bdev_flags+0x430/0x4f0 fs/super.c:1887
       vfs_get_tree+0x92/0x2a0 fs/super.c:1947
       fc_mount fs/namespace.c:1198 [inline]
       do_new_mount_fc fs/namespace.c:3772 [inline]
       do_new_mount+0x319/0xdc0 fs/namespace.c:3848
       do_mount fs/namespace.c:4181 [inline]
       __do_sys_mount fs/namespace.c:4397 [inline]
       __se_sys_mount+0x31d/0x420 fs/namespace.c:4374
       do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
       do_syscall_64+0x166/0x520 arch/x86/entry/syscall_64.c:84
       entry_SYSCALL_64_after_hwframe+0x77/0x7f

-> #0 (&oi->ip_io_mutex){+.+.}-{4:4}:
       check_prev_add kernel/locking/lockdep.c:3181 [inline]
       check_prevs_add kernel/locking/lockdep.c:3300 [inline]
       validate_chain kernel/locking/lockdep.c:3924 [inline]
       __lock_acquire+0x15ff/0x2e50 kernel/locking/lockdep.c:5254
       lock_acquire+0x115/0x350 kernel/locking/lockdep.c:5908
       __mutex_lock_common kernel/locking/mutex.c:646 [inline]
       __mutex_lock+0x19d/0x1550 kernel/locking/mutex.c:821
       ocfs2_read_blocks+0x1ef/0x14d0 fs/ocfs2/buffer_head_io.c:229
       ocfs2_read_inode_block_full fs/ocfs2/inode.c:1968 [inline]
       ocfs2_read_inode_block+0xe0/0x190 fs/ocfs2/inode.c:1980
       ocfs2_assign_bh fs/ocfs2/dlmglue.c:2415 [inline]
       ocfs2_inode_lock_full_nested+0x2bb/0x1b30 fs/ocfs2/dlmglue.c:2510
       ocfs2_statfs+0x1ba/0xa70 fs/ocfs2/super.c:1577
       statfs_by_dentry fs/statfs.c:66 [inline]
       vfs_statfs+0x147/0x2d0 fs/statfs.c:90
       loop_get_discard_config drivers/block/loop.c:774 [inline]
       loop_update_limits+0x375/0x920 drivers/block/loop.c:984
       loop_configure+0x7d2/0xdc0 drivers/block/loop.c:1084
       lo_ioctl+0xad5/0x2150 drivers/block/loop.c:1564
       blkdev_ioctl+0x5e3/0x740 block/ioctl.c:798
       vfs_ioctl fs/ioctl.c:51 [inline]
       __do_sys_ioctl fs/ioctl.c:597 [inline]
       __se_sys_ioctl+0xfc/0x170 fs/ioctl.c:583
       do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
       do_syscall_64+0x166/0x520 arch/x86/entry/syscall_64.c:84
       entry_SYSCALL_64_after_hwframe+0x77/0x7f

other info that might help us debug this:

Chain exists of:
  &oi->ip_io_mutex --> &q->q_usage_counter(io)#24 --> &q->limits_lock

 Possible unsafe locking scenario:

       CPU0                    CPU1
       ----                    ----
  lock(&q->limits_lock);
                               lock(&q->q_usage_counter(io)#24);
                               lock(&q->limits_lock);
  lock(&oi->ip_io_mutex);

 *** DEADLOCK ***

locks held by syz.3.993/9951: 2, last CPU#1:
 #0: ffff888026af3430 (&lo->lo_mutex){+.+.}-{4:4}, at: loop_global_lock_killable drivers/block/loop.c:119 [inline]
 #0: ffff888026af3430 (&lo->lo_mutex){+.+.}-{4:4}, at: loop_configure+0x35d/0xdc0 drivers/block/loop.c:1038
 #1: ffff888026afda68 (&q->limits_lock){+.+.}-{4:4}, at: queue_limits_start_update include/linux/blkdev.h:1101 [inline]
 #1: ffff888026afda68 (&q->limits_lock){+.+.}-{4:4}, at: loop_configure+0x787/0xdc0 drivers/block/loop.c:1083

stack backtrace:
CPU: 1 UID: 0 PID: 9951 Comm: syz.3.993 Tainted: G             L      syzkaller #0 PREEMPT(full) 
Tainted: [L]=SOFTLOCKUP
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 07/24/2026
Call Trace:
 <TASK>
 dump_stack_lvl+0xe8/0x150 lib/dump_stack.c:120
 print_circular_bug+0x2e2/0x300 kernel/locking/lockdep.c:2059
 check_noncircular+0x12f/0x150 kernel/locking/lockdep.c:2191
 check_prev_add kernel/locking/lockdep.c:3181 [inline]
 check_prevs_add kernel/locking/lockdep.c:3300 [inline]
 validate_chain kernel/locking/lockdep.c:3924 [inline]
 __lock_acquire+0x15ff/0x2e50 kernel/locking/lockdep.c:5254
 lock_acquire+0x115/0x350 kernel/locking/lockdep.c:5908
 __mutex_lock_common kernel/locking/mutex.c:646 [inline]
 __mutex_lock+0x19d/0x1550 kernel/locking/mutex.c:821
 ocfs2_read_blocks+0x1ef/0x14d0 fs/ocfs2/buffer_head_io.c:229
 ocfs2_read_inode_block_full fs/ocfs2/inode.c:1968 [inline]
 ocfs2_read_inode_block+0xe0/0x190 fs/ocfs2/inode.c:1980
 ocfs2_assign_bh fs/ocfs2/dlmglue.c:2415 [inline]
 ocfs2_inode_lock_full_nested+0x2bb/0x1b30 fs/ocfs2/dlmglue.c:2510
 ocfs2_statfs+0x1ba/0xa70 fs/ocfs2/super.c:1577
 statfs_by_dentry fs/statfs.c:66 [inline]
 vfs_statfs+0x147/0x2d0 fs/statfs.c:90
 loop_get_discard_config drivers/block/loop.c:774 [inline]
 loop_update_limits+0x375/0x920 drivers/block/loop.c:984
 loop_configure+0x7d2/0xdc0 drivers/block/loop.c:1084
 lo_ioctl+0xad5/0x2150 drivers/block/loop.c:1564
 blkdev_ioctl+0x5e3/0x740 block/ioctl.c:798
 vfs_ioctl fs/ioctl.c:51 [inline]
 __do_sys_ioctl fs/ioctl.c:597 [inline]
 __se_sys_ioctl+0xfc/0x170 fs/ioctl.c:583
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x166/0x520 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f
RIP: 0033:0x7f61a979e0d9
Code: ff c3 66 2e 0f 1f 84 00 00 00 00 00 0f 1f 44 00 00 48 89 f8 48 89 f7 48 89 d6 48 89 ca 4d 89 c2 4d 89 c8 4c 8b 4c 24 08 0f 05 <48> 3d 01 f0 ff ff 73 01 c3 48 c7 c1 e8 ff ff ff f7 d8 64 89 01 48
RSP: 002b:00007f61aa701028 EFLAGS: 00000246 ORIG_RAX: 0000000000000010
RAX: ffffffffffffffda RBX: 00007f61a9a26180 RCX: 00007f61a979e0d9
RDX: 0000200000001800 RSI: 
```
