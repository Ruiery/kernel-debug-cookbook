---
title: INFO: rcu detected stall in call_usermodehelper_exec_async (4)
subsystems: mm,mm,mm,cgroups,mm,mm
extid: be81254ae29faa71cdfe
link: https://syzkaller.appspot.com/bug?extid=be81254ae29faa71cdfe
source: syzbot-dashboard
---

# INFO: rcu detected stall in call_usermodehelper_exec_async (4)

来源：[https://syzkaller.appspot.com/bug?extid=be81254ae29faa71cdfe](https://syzkaller.appspot.com/bug?extid=be81254ae29faa71cdfe)

## 崩溃报告

```
rcu: INFO: rcu_preempt detected stalls on CPUs/tasks:
rcu: 	1-...!: (1 GPs behind) idle=5e54/1/0x4000000000000000 softirq=17788/17788 fqs=6
rcu: 	(detected by 0, t=10504 jiffies, g=16305, q=1397 ncpus=2)
Sending NMI from CPU 0 to CPUs 1:
NMI backtrace for cpu 1
CPU: 1 UID: 0 PID: 5951 Comm: kworker/u8:8 Not tainted syzkaller #0 PREEMPT(full) 
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 07/24/2026
RIP: 0010:native_save_fl arch/x86/include/asm/irqflags.h:26 [inline]
RIP: 0010:arch_local_save_flags arch/x86/include/asm/irqflags.h:109 [inline]
RIP: 0010:arch_irqs_disabled arch/x86/include/asm/irqflags.h:151 [inline]
RIP: 0010:lock_is_held_type+0xf2/0x150 kernel/locking/lockdep.c:5984
Code: c5 0f 94 c3 eb 05 bb 01 00 00 00 48 c7 c7 85 b4 6f 8e e8 f1 1a 00 00 b8 ff ff ff ff 65 0f c1 05 dc 1c b1 07 83 f8 01 75 25 9c <58> a9 00 02 00 00 75 39 41 f7 c4 00 02 00 00 74 01 fb 89 d8 5b 41
RSP: 0018:ffffc90000a18cb8 EFLAGS: 00000046
RAX: 0000000000000001 RBX: 0000000000000001 RCX: 0000000001000002
RDX: 0000000001000001 RSI: ffffffff8e6fb485 RDI: ffffffff8c6d8b80
RBP: 00000000ffffffff R08: 0000000001000001 R09: 0000000000000004
R10: dffffc0000000000 R11: fffff52000143190 R12: 0000000000000046
R13: ffff8880352cddc0 R14: ffff88807c51e2c0 R15: 0000000000000002
FS:  0000000000000000(0000) GS:ffff888124ddf000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 00007efd7c6f3f60 CR3: 00000000773ae000 CR4: 00000000003526f0
Call Trace:
 <IRQ>
 lock_is_held include/linux/lockdep.h:249 [inline]
 advance_sched+0xe4/0xc80 net/sched/sch_taprio.c:933
 __run_hrtimer kernel/time/hrtimer.c:2067 [inline]
 __hrtimer_run_queues+0x3bc/0xa10 kernel/time/hrtimer.c:2124
 hrtimer_interrupt+0x4cd/0xaa0 kernel/time/hrtimer.c:2243
 local_apic_timer_interrupt arch/x86/kernel/apic/apic.c:1051 [inline]
 __sysvec_apic_timer_interrupt+0x102/0x430 arch/x86/kernel/apic/apic.c:1068
 instr_sysvec_apic_timer_interrupt arch/x86/kernel/apic/apic.c:1062 [inline]
 sysvec_apic_timer_interrupt+0xa1/0xc0 arch/x86/kernel/apic/apic.c:1062
 </IRQ>
 <TASK>
 asm_sysvec_apic_timer_interrupt+0x1a/0x20 arch/x86/include/asm/idtentry.h:674
RIP: 0010:__raw_spin_unlock_irqrestore include/linux/spinlock_api_smp.h:211 [inline]
RIP: 0010:_raw_spin_unlock_irqrestore+0x47/0x80 kernel/locking/spinlock.c:221
Code: f7 e8 fd d2 bd f5 f7 c3 00 02 00 00 74 05 e8 30 0a ea f5 9c 58 a9 00 02 00 00 75 29 f7 c3 00 02 00 00 74 01 fb bf 01 00 00 00 <e8> 94 ec ae f5 65 48 8b 05 5c 22 ae 07 48 85 c0 74 18 5b 41 5e c3
RSP: 0018:ffffc90002e27758 EFLAGS: 00000206
RAX: 0000000000000002 RBX: 0000000000000282 RCX: 8000000000000001
RDX: 0000000000000007 RSI: ffffffff8e4733de RDI: 0000000000000001
RBP: 0000000000000008 R08: ffffffff907a047f R09: 1ffffffff20f408f
R10: dffffc0000000000 R11: fffffbfff20f4090 R12: 0000000000000000
R13: ffff888078ae4000 R14: ffffffff9ac56e98 R15: 0000000000000000
 __debug_check_no_obj_freed lib/debugobjects.c:1180 [inline]
 debug_check_no_obj_freed+0x39e/0x450 lib/debugobjects.c:1201
 __free_pages_prepare mm/page_alloc.c:1425 [inline]
 __free_frozen_pages+0x5cc/0xd90 mm/page_alloc.c:2962
 __slab_free+0x274/0x2c0 mm/slub.c:5815
 qlink_free mm/kasan/quarantine.c:163 [inline]
 qlist_free_all+0x99/0x100 mm/kasan/quarantine.c:179
 kasan_quarantine_reduce+0x148/0x160 mm/kasan/quarantine.c:286
 __kasan_slab_alloc+0x22/0x80 mm/kasan/common.c:350
 kasan_slab_alloc include/linux/kasan.h:253 [inline]
 slab_post_alloc_hook mm/slub.c:4683 [inline]
 slab_alloc_node mm/slub.c:4996 [inline]
 __do_kmalloc_node mm/slub.c:5413 [inline]
 __kmalloc_noprof+0x307/0x720 mm/slub.c:5439
 _kmalloc_noprof include/linux/slab.h:995 [inline]
 load_elf_phdrs fs/binfmt_elf.c:537 [inline]
 load_elf_binary+0x2c6/0x28d0 fs/binfmt_elf.c:866
 search_binary_handler fs/exec.c:1759 [inline]
 exec_binprm fs/exec.c:1791 [inline]
 bprm_execve+0x930/0x1590 fs/exec.c:1847
 kernel_execve+0x8c3/0x9c0 fs/exec.c:1991
 call_usermodehelper_exec_async+0x20f/0x360 kernel/umh.c:107
 ret_from_fork+0x514/0xb70 arch/x86/kernel/process.c:158
 ret_from_fork_asm+0x1a/0x30 arch/x86/entry/entry_64.S:245
 </TASK>
rcu: rcu_preempt kthread starved for 10474 jiffies! g16305 f0x0 RCU_GP_WAIT_FQS(5) ->state=R ->cpu=0
rcu: 	Unless rcu_preempt kthread gets sufficient CPU time, OOM is now expected behavior.
rcu: RCU grace-period kthread stack dump:
task:rcu_preempt     state:R  running task     stack:27496 pid:17    tgid:17    ppid:2      task_flags:0x208040 flags:0x00080000
Call Trace:
 <TASK>
 context_switch kernel/sched/core.c:5520 [inline]
 __schedule+0x17d4/0x5820 kernel/sched/core.c:7270
 __schedule_loop kernel/sched/core.c:7347 [inline]
 schedule+0x164/0x2b0 kernel/sched/core.c:7362
 schedule_timeout+0x152/0x2c0 kernel/time/sleep_timeout.c:99
 rcu_gp_fqs_loop+0x30c/0x11f0 kernel/rcu/tree.c:2122
 rcu_gp_kthread+0x9e/0x2b0 kernel/rcu/tree.c:2330
 kthread+0x38b/0x480 kernel/kthread.c:436
 ret_from_fork+0x514/0xb70 arch/x86/kernel/process.c:158
 ret_from_fork_asm+0x1a/0x30 arch/x86/entry/entry_64.S:245
 </TASK>
rcu: Stack dump where RCU GP kthread last ran:
CPU: 0 UID: 0 PID: 4981 Comm: udevd Not tainted syzkaller #0 PREEMPT(full) 
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 07/24/2026
RIP: 0010:csd_lock_wait kernel/smp.c:363 [inline]
RIP: 0010:csd_lock kernel/smp.c:396 [inline]
RIP: 0010:smp_call_function_many_cond+0x61e/0x1500 kernel/smp.c:944
Code: b6 04 04 84 c0 0f 85 d5 03 00 00 44 8b 3b 44 89 fe 83 e6 01 31 ff e8 51 51 0c 00 41 83 e7 01 75 07 e8 46 4c 0c 00 eb 3f f3 90 <48> b8 00 00 00 00 00 fc ff df 41 0f b6 04 04 84 c0 75 0f f7 03 01
RSP: 0018:ffffc90002e97420 EFLAGS: 00000293
RAX: ffffffff81bb677e RBX: ffff8880b87414c8 RCX: ffff88807e849f40
RDX: 0000000000000000 RSI: 0000000000000001 RDI: 0000000000000000
RBP: ffffc90002e97570 R08: ffff88807e84b4df R09: 1ffff1100fd0969b
R10: dffffc0000000000 R11: 0000000000000000 R12: 1ffff110170e8299
R13: 0000000000000001 R14: ffff8880b87414c0 R15: 0000000000000001
FS:  00007f28f2dbd880(0000) GS:ffff888124cdf000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 00007f8e8feb2e9c CR3: 000000007df0a000 CR4: 00000000003526f0
Call Trace:
 <TASK>
 __flush_tlb_multi arch/x86/include/asm/paravirt.h:46 [inline]
 flush_tlb_multi arch/x86/mm/tlb.c:1361 [inline]
 flush_tlb_mm_range+0x8ff/0x1090 arch/x86/mm/tlb.c:1435
 dup_mmap+0x1758/0x1dc0 mm/mmap.c:1884
 dup_mm kernel/fork.c:1543 [inline]
 copy_mm+0x11a/0x480 kernel/fork.c:1595
 copy_process+0x1e75/0x43e0 kernel/fork.c:2307
 kernel_clone+0x2d7/0x940 kernel/fork.c:2766
 __do_sys_clone kernel/fork.c:2908 [inline]
 __se_sys_clone kernel/fork.c:2892 [inline]
 __x64_sys_clone+0x1b6/0x230 kernel/fork.c:2892
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x166/0x520 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f
RIP: 0033:0x7f28f26f1636
Code: 89 df e8 6d e8 f6 ff 45 31 c0 31 d2 31 f6 64 48 8b 04 25 10 00 00 00 bf 11 00 20 01 4c 8d 90 d0 02 00 00 b8 38 00 00 00 0f 05 <48> 3d 00 f0 ff ff 77 52 89 c5 85 c0 75 31 64 48 8b 04 25 10 00 00
RSP: 002b:00007fff76bbb760 EFLAGS: 00000246 ORIG_RAX: 0000000000000038
RAX: ffffffffffffffda RBX: 00007fff76bbb768 RCX: 00007f28f26f1636
RDX: 0000000000000000 RSI: 0000000000000000 RDI: 0000000001200011
RBP: 000055a08aeb4910 R08: 0000000000000000 R09: 000055a08aebc8e0
R10: 00007f28f2dbdb50 R11: 0000000000000246 R12: 00007fff76bbbb20
R13: 0000000000000000 R14: 0000000000000000 R15: 0000000000000000
 </TASK>
```
