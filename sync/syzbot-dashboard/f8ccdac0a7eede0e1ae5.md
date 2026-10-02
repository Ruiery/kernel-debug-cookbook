---
title: INFO: rcu detected stall in __dentry_kill
subsystems: mm
extid: f8ccdac0a7eede0e1ae5
link: https://syzkaller.appspot.com/bug?extid=f8ccdac0a7eede0e1ae5
source: syzbot-dashboard
---

# INFO: rcu detected stall in __dentry_kill

来源：[https://syzkaller.appspot.com/bug?extid=f8ccdac0a7eede0e1ae5](https://syzkaller.appspot.com/bug?extid=f8ccdac0a7eede0e1ae5)

## 崩溃报告

```
rcu: INFO: rcu_preempt detected stalls on CPUs/tasks:
rcu: 	Tasks blocked on level-0 rcu_node (CPUs 0-1): P5788/1:b.el
rcu: 	(detected by 0, t=10506 jiffies, g=15749, q=1307 ncpus=2)
task:syz-executor    state:R  running task     stack:21752 pid:5788  tgid:5788  ppid:5780   task_flags:0x400140 flags:0x00080001
Call Trace:
 <TASK>
 context_switch kernel/sched/core.c:5388 [inline]
 __schedule+0x1821/0x5740 kernel/sched/core.c:7189
 preempt_schedule_irq+0x4d/0xa0 kernel/sched/core.c:7513
 irqentry_exit_to_kernel_mode include/linux/irq-entry-common.h:539 [inline]
 irqentry_exit+0x14f/0x8b0 kernel/entry/common.c:164
 asm_sysvec_apic_timer_interrupt+0x1a/0x20 arch/x86/include/asm/idtentry.h:697
RIP: 0010:__orc_find arch/x86/kernel/unwind_orc.c:101 [inline]
RIP: 0010:orc_find arch/x86/kernel/unwind_orc.c:238 [inline]
RIP: 0010:unwind_next_frame+0x4d6/0x2550 arch/x86/kernel/unwind_orc.c:510
Code: 00 00 83 f8 01 4c 8b 7c 24 50 48 bd 00 00 00 00 00 fc ff df 4c 8b 6c 24 20 0f 84 86 16 00 00 e9 03 02 00 00 49 89 d5 48 89 d5 <48> 89 d8 48 29 e8 48 89 c1 48 c1 f9 02 48 c1 e8 3f 48 01 c8 48 83
RSP: 0018:ffffc90003c2f4b8 EFLAGS: 00000246
RAX: ffffffff9052f1d0 RBX: ffffffff9052f1d0 RCX: ffffffff9052f1d8
RDX: ffffffff9052f1d0 RSI: ffffffff90d3bfc2 RDI: ffffffff8c28b880
RBP: ffffffff9052f1d0 R08: 0000000000000003 R09: ffffffff8e95cc20
R10: ffffc90003c2f5d8 R11: ffffffff81b0e0e0 R12: ffffffff8243249e
R13: ffffffff9052f1d0 R14: ffffc90003c2f588 R15: ffffffff9052f1d4
 arch_stack_walk+0x11b/0x150 arch/x86/kernel/stacktrace.c:25
 stack_trace_save+0xa9/0x100 kernel/stacktrace.c:122
 kasan_save_stack mm/kasan/common.c:57 [inline]
 kasan_save_track+0x3e/0x80 mm/kasan/common.c:78
 unpoison_slab_object mm/kasan/common.c:340 [inline]
 __kasan_slab_alloc+0x6c/0x80 mm/kasan/common.c:366
 kasan_slab_alloc include/linux/kasan.h:253 [inline]
 slab_post_alloc_hook mm/slub.c:4570 [inline]
 slab_alloc_node mm/slub.c:4899 [inline]
 kmem_cache_alloc_noprof+0x2bc/0x650 mm/slub.c:4906
 kmem_alloc_batch lib/debugobjects.c:371 [inline]
 fill_pool+0x156/0x580 lib/debugobjects.c:420
 debug_objects_fill_pool lib/debugobjects.c:752 [inline]
 debug_object_activate+0x4a3/0x580 lib/debugobjects.c:841
 debug_rcu_head_queue kernel/rcu/rcu.h:236 [inline]
 __call_rcu_common kernel/rcu/tree.c:3116 [inline]
 call_rcu+0x43/0x890 kernel/rcu/tree.c:3251
 __destroy_inode+0x2b2/0x640 fs/inode.c:369
 destroy_inode fs/inode.c:392 [inline]
 evict+0x8a7/0xb10 fs/inode.c:865
 __dentry_kill+0x1a2/0x690 fs/dcache.c:718
 finish_dput+0xc9/0x480 fs/dcache.c:927
 __fput+0x691/0xa60 fs/file_table.c:518
 fput_close_sync+0x11f/0x240 fs/file_table.c:615
 __do_sys_close fs/open.c:1507 [inline]
 __se_sys_close fs/open.c:1492 [inline]
 __x64_sys_close+0x7e/0x110 fs/open.c:1492
 do_syscall_x64 arch/x86/entry/syscall_64.c:63 [inline]
 do_syscall_64+0x174/0x580 arch/x86/entry/syscall_64.c:94
 entry_SYSCALL_64_after_hwframe+0x77/0x7f
RIP: 0033:0x7efe5039bfc7
RSP: 002b:00007fff8a26cfa8 EFLAGS: 00000246 ORIG_RAX: 0000000000000003
RAX: ffffffffffffffda RBX: 0000000000000005 RCX: 00007efe5039bfc7
RDX: 0000000000000000 RSI: 0000000000008933 RDI: 0000000000000005
RBP: 0000000000000003 R08: 0000000000000000 R09: 0000000000000004
R10: 0000000000000005 R11: 0000000000000246 R12: 00007fff8a26d03c
R13: 00007efe504334c0 R14: 00007efe51144620 R15: 00007efe504334c0
 </TASK>
rcu: rcu_preempt kthread starved for 5285 jiffies! g15749 f0x0 RCU_GP_WAIT_FQS(5) ->state=0x0 ->cpu=0
rcu: 	Unless rcu_preempt kthread gets sufficient CPU time, OOM is now expected behavior.
rcu: RCU grace-period kthread stack dump:
task:rcu_preempt     state:R  running task     stack:27688 pid:16    tgid:16    ppid:2      task_flags:0x208040 flags:0x00080000
Call Trace:
 <TASK>
 context_switch kernel/sched/core.c:5388 [inline]
 __schedule+0x1821/0x5740 kernel/sched/core.c:7189
 __schedule_loop kernel/sched/core.c:7268 [inline]
 schedule+0x164/0x360 kernel/sched/core.c:7283
 schedule_timeout+0x158/0x2c0 kernel/time/sleep_timeout.c:99
 rcu_gp_fqs_loop+0x312/0x11d0 kernel/rcu/tree.c:2095
 rcu_gp_kthread+0x9e/0x2b0 kernel/rcu/tree.c:2297
 kthread+0x389/0x470 kernel/kthread.c:436
 ret_from_fork+0x514/0xb70 arch/x86/kernel/process.c:158
 ret_from_fork_asm+0x1a/0x30 arch/x86/entry/entry_64.S:245
 </TASK>
rcu: Stack dump where RCU GP kthread last ran:
CPU: 0 UID: 0 PID: 1163 Comm: kworker/u8:9 Not tainted syzkaller #0 PREEMPT(full) 
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 05/09/2026
Workqueue: events_unbound toggle_allocation_gate
RIP: 0010:csd_lock_wait kernel/smp.c:342 [inline]
RIP: 0010:smp_call_function_many_cond+0xfcf/0x13d0 kernel/smp.c:892
Code: 79 45 8b 2e 44 89 ee 83 e6 01 31 ff e8 aa 07 0c 00 41 83 e5 01 49 bd 00 00 00 00 00 fc ff df 75 07 e8 55 03 0c 00 eb 37 f3 90 <43> 0f b6 04 2c 84 c0 75 10 41 f7 06 01 00 00 00 74 1e e8 3a 03 0c
RSP: 0018:ffffc900058e7700 EFLAGS: 00000293
RAX: ffffffff81b9b376 RBX: ffff8880b863c388 RCX: ffff888028eb3e00
RDX: 0000000000000000 RSI: 0000000000000001 RDI: 0000000000000000
RBP: ffffc900058e7840 R08: ffffffff903034f7 R09: 1ffffffff206069e
R10: dffffc0000000000 R11: fffffbfff206069f R12: 1ffff110170e81b1
R13: dffffc0000000000 R14: ffff8880b8740d88 R15: 0000000000000001
FS:  0000000000000000(0000) GS:ffff8881252a0000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 00007f7680c6904c CR3: 000000000e74a000 CR4: 00000000003526f0
Call Trace:
 <TASK>
 on_each_cpu_cond_mask+0x3f/0x80 kernel/smp.c:1057
 on_each_cpu include/linux/smp.h:72 [inline]
 smp_text_poke_sync_each_cpu arch/x86/kernel/alternative.c:2773 [inline]
 smp_text_poke_batch_finish+0x5f5/0x1160 arch/x86/kernel/alternative.c:2983
 arch_jump_label_transform_apply+0x1c/0x30 arch/x86/kernel/jump_label.c:146
 static_key_enable_cpuslocked+0x128/0x240 kernel/jump_label.c:210
 static_key_enable+0x1a/0x20 kernel/jump_label.c:223
 toggle_allocation_gate+0xab/0x290 mm/kfence/core.c:906
 process_one_work kernel/workqueue.c:3314 [inline]
 process_scheduled_works+0xb5d/0x1860 kernel/workqueue.c:3397
 worker_thread+0xa53/0xfc0 kernel/workqueue.c:3478
 kthread+0x389/0x470 kernel/kthread.c:436
 ret_from_fork+0x514/0xb70 arch/x86/kernel/process.c:158
 ret_from_fork_asm+0x1a/0x30 arch/x86/entry/entry_64.S:245
 </TASK>
```
