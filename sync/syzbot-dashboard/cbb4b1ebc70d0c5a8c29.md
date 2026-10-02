---
title: INFO: task hung in nbd_add_socket (2)
subsystems: block,block,block
extid: cbb4b1ebc70d0c5a8c29
link: https://syzkaller.appspot.com/bug?extid=cbb4b1ebc70d0c5a8c29
source: syzbot-dashboard
---

# INFO: task hung in nbd_add_socket (2)

来源：[https://syzkaller.appspot.com/bug?extid=cbb4b1ebc70d0c5a8c29](https://syzkaller.appspot.com/bug?extid=cbb4b1ebc70d0c5a8c29)

## 崩溃报告

```
INFO: task syz-executor301:5181 blocked for more than 143 seconds.
      Not tainted 6.7.0-syzkaller-01193-g6c1dd1fe5d8a #0
"echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.
task:syz-executor301 state:D stack:28144 pid:5181  tgid:5180  ppid:5096   flags:0x00000006
Call Trace:
 <TASK>
 context_switch kernel/sched/core.c:5399 [inline]
 __schedule+0xf12/0x5c00 kernel/sched/core.c:6726
 __schedule_loop kernel/sched/core.c:6801 [inline]
 schedule+0xe9/0x270 kernel/sched/core.c:6816
 blk_mq_freeze_queue_wait+0x13f/0x190 block/blk-mq.c:140
 nbd_add_socket+0x18c/0x980 drivers/block/nbd.c:1150
 __nbd_ioctl drivers/block/nbd.c:1494 [inline]
 nbd_ioctl+0x8b9/0xd60 drivers/block/nbd.c:1551
 blkdev_ioctl+0x2f3/0x760 block/ioctl.c:633
 vfs_ioctl fs/ioctl.c:51 [inline]
 __do_sys_ioctl fs/ioctl.c:871 [inline]
 __se_sys_ioctl fs/ioctl.c:857 [inline]
 __x64_sys_ioctl+0x18f/0x210 fs/ioctl.c:857
 do_syscall_x64 arch/x86/entry/common.c:52 [inline]
 do_syscall_64+0xd3/0x250 arch/x86/entry/common.c:83
 entry_SYSCALL_64_after_hwframe+0x63/0x6b
RIP: 0033:0x7fee59f2d4b9
RSP: 002b:00007fee59eeb228 EFLAGS: 00000246 ORIG_RAX: 0000000000000010
RAX: ffffffffffffffda RBX: 00007fee59fb4328 RCX: 00007fee59f2d4b9
RDX: 0000000000000004 RSI: 000000000000ab00 RDI: 0000000000000003
RBP: 00007fee59fb4320 R08: 00007fee59eeb6c0 R09: 00007fee59eeb6c0
R10: 00007fee59eeb6c0 R11: 0000000000000246 R12: 00007fee59fb432c
R13: 00007fee59f811a4 R14: 64626e2f7665642f R15: 00007ffd23ff3e88
 </TASK>
INFO: task syz-executor301:5182 blocked for more than 143 seconds.
      Not tainted 6.7.0-syzkaller-01193-g6c1dd1fe5d8a #0
"echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.
task:syz-executor301 state:D stack:30200 pid:5182  tgid:5180  ppid:5096   flags:0x00000006
Call Trace:
 <TASK>
 context_switch kernel/sched/core.c:5399 [inline]
 __schedule+0xf12/0x5c00 kernel/sched/core.c:6726
 __schedule_loop kernel/sched/core.c:6801 [inline]
 schedule+0xe9/0x270 kernel/sched/core.c:6816
 schedule_preempt_disabled+0x13/0x20 kernel/sched/core.c:6873
 __mutex_lock_common kernel/locking/mutex.c:684 [inline]
 __mutex_lock+0x5b9/0x9d0 kernel/locking/mutex.c:752
 nbd_ioctl+0x151/0xd60 drivers/block/nbd.c:1544
 blkdev_ioctl+0x2f3/0x760 block/ioctl.c:633
 vfs_ioctl fs/ioctl.c:51 [inline]
 __do_sys_ioctl fs/ioctl.c:871 [inline]
 __se_sys_ioctl fs/ioctl.c:857 [inline]
 __x64_sys_ioctl+0x18f/0x210 fs/ioctl.c:857
 do_syscall_x64 arch/x86/entry/common.c:52 [inline]
 do_syscall_64+0xd3/0x250 arch/x86/entry/common.c:83
 entry_SYSCALL_64_after_hwframe+0x63/0x6b
RIP: 0033:0x7fee59f2d4b9
RSP: 002b:00007fee59eca228 EFLAGS: 00000246 ORIG_RAX: 0000000000000010
RAX: ffffffffffffffda RBX: 00007fee59fb4338 RCX: 00007fee59f2d4b9
RDX: 0000000000000000 RSI: 000000000000ab03 RDI: 0000000000000003
RBP: 00007fee59fb4330 R08: 00007ffd23ff3e87 R09: 00007fee59eca6c0
R10: 0000000000000000 R11: 0000000000000246 R12: 00007fee59fb433c
R13: 00007fee59f811a4 R14: 64626e2f7665642f R15: 00007ffd23ff3e88
 </TASK>
INFO: task syz-executor301:5183 blocked for more than 143 seconds.
      Not tainted 6.7.0-syzkaller-01193-g6c1dd1fe5d8a #0
"echo 0 > /proc/sys/kernel/hung_task_timeout_secs" disables this message.
task:syz-executor301 state:D stack:29136 pid:5183  tgid:5180  ppid:5096   flags:0x00000006
Call Trace:
 <TASK>
 context_switch kernel/sched/core.c:5399 [inline]
 __schedule+0xf12/0x5c00 kernel/sched/core.c:6726
 __schedule_loop kernel/sched/core.c:6801 [inline]
 schedule+0xe9/0x270 kernel/sched/core.c:6816
 schedule_preempt_disabled+0x13/0x20 kernel/sched/core.c:6873
 __mutex_lock_common kernel/locking/mutex.c:684 [inline]
 __mutex_lock+0x5b9/0x9d0 kernel/locking/mutex.c:752
 nbd_ioctl+0x151/0xd60 drivers/block/nbd.c:1544
 blkdev_ioctl+0x2f3/0x760 block/ioctl.c:633
 vfs_ioctl fs/ioctl.c:51 [inline]
 __do_sys_ioctl fs/ioctl.c:871 [inline]
 __se_sys_ioctl fs/ioctl.c:857 [inline]
 __x64_sys_ioctl+0x18f/0x210 fs/ioctl.c:857
 do_syscall_x64 arch/x86/entry/common.c:52 [inline]
 do_syscall_64+0xd3/0x250 arch/x86/entry/common.c:83
 entry_SYSCALL_64_after_hwframe+0x63/0x6b
RIP: 0033:0x7fee59f2d4b9
RSP: 002b:00007fee59ea9228 EFLAGS: 00000246 ORIG_RAX: 0000000000000010
RAX: ffffffffffffffda RBX: 00007fee59fb4348 RCX: 00007fee59f2d4b9
RDX: 0000000000000001 RSI: 000000000000ab07 RDI: 0000000000000003
RBP: 00007fee59fb4340 R08: 00007ffd23ff3e87 R09: 00007fee59ea96c0
R10: 0000000000000000 R11: 0000000000000246 R12: 00007fee59fb434c
R13: 00007fee59f811a4 R14: 64626e2f7665642f R15: 00007ffd23ff3e88
 </TASK>
INFO: lockdep is turned off.
NMI backtrace for cpu 0
CPU: 0 PID: 28 Comm: khungtaskd Not tainted 6.7.0-syzkaller-01193-g6c1dd1fe5d8a #0
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 11/17/2023
Call Trace:
 <TASK>
 __dump_stack lib/dump_stack.c:88 [inline]
 dump_stack_lvl+0xd9/0x1b0 lib/dump_stack.c:106
 nmi_cpu_backtrace+0x277/0x390 lib/nmi_backtrace.c:113
 nmi_trigger_cpumask_backtrace+0x299/0x300 lib/nmi_backtrace.c:62
 trigger_all_cpu_backtrace include/linux/nmi.h:160 [inline]
 check_hung_uninterruptible_tasks kernel/hung_task.c:222 [inline]
 watchdog+0xf87/0x1210 kernel/hung_task.c:379
 kthread+0x2c6/0x3a0 kernel/kthread.c:388
 ret_from_fork+0x45/0x80 arch/x86/kernel/process.c:147
 ret_from_fork_asm+0x11/0x20 arch/x86/entry/entry_64.S:242
 </TASK>
Sending NMI from CPU 0 to CPUs 1:
NMI backtrace for cpu 1
CPU: 1 PID: 58 Comm: kworker/u4:4 Not tainted 6.7.0-syzkaller-01193-g6c1dd1fe5d8a #0
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 11/17/2023
Workqueue: events_unbound toggle_allocation_gate
RIP: 0010:mmu_notifier_arch_invalidate_secondary_tlbs include/linux/mmu_notifier.h:496 [inline]
RIP: 0010:flush_tlb_mm_range+0x1c0/0x320 arch/x86/mm/tlb.c:1040
Code: 48 8d bb f0 07 00 00 48 b8 00 00 00 00 00 fc ff df 48 89 fa 48 c1 ea 03 80 3c 02 00 0f 85 2d 01 00 00 48 83 bb f0 07 00 00 00 <0f> 85 e9 00 00 00 48 83 c4 08 5b 5d 41 5c 41 5d 41 5e 41 5f c3 48
RSP: 0018:ffffc90001597968 EFLAGS: 00000046
RAX: dffffc0000000000 RBX: ffff888013078000 RCX: 0000000000000000
RDX: 1ffff1100260f0fe RSI: 1ffffffff1e7333c RDI: ffff8880130787f0
RBP: 00002aaaaaaac000 R08: 0000000000000000 R09: 0000000000008e6a
R10: ffff888013078627 R11: 0000000000000000 R12: 00002aaaaaaab000
R13: ffff8880b993c400 R14: ffff8880130788c0 R15: 0000000000000001
FS:  0000000000000000(0000) GS:ffff8880b9900000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 000055c048916680 CR3: 000000000cf79000 CR4: 0000000000350ef0
Call Trace:
 <NMI>
 </NMI>
 <TASK>
 __text_poke+0x5bd/0xca0 arch/x86/kernel/alternative.c:1878
 text_poke_bp_batch+0x1cd/0x750 arch/x86/kernel/alternative.c:2223
 text_poke_flush arch/x86/kernel/alternative.c:2417 [inline]
 text_poke_flush arch/x86/kernel/alternative.c:2414 [inline]
 text_poke_finish+0x30/0x40 arch/x86/kernel/alternative.c:2424
 arch_jump_label_transform_apply+0x1c/0x30 arch/x86/kernel/jump_label.c:146
 jump_label_update+0x1d7/0x400 kernel/jump_label.c:829
 static_key_disable_cpuslocked+0x154/0x1c0 kernel/jump_label.c:235
 static_key_disable+0x1a/0x20 kernel/jump_label.c:243
 toggle_allocation_gate mm/kfence/core.c:831 [inline]
 toggle_allocation_gate+0x13f/0x250 mm/kfence/core.c:818
 process_one_work+0x886/0x15d0 kernel/workqueue.c:2633
 process_scheduled_works kernel/workqueue.c:2706 [inline]
 worker_thread+0x8b9/0x1290 kernel/workqueue.c:2787
 kthread+0x2c6/0x3a0 kernel/kthread.c:388
 ret_from_fork+0x45/0x80 arch/x86/kernel/process.c:147
 ret_from_fork_asm+0x11/0x20 arch/x86/entry/entry_64.S:242
 </TASK>
```
