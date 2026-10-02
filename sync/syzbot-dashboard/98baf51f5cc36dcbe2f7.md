---
title: KCSAN: data-race in __set_task_comm / strlen (2)
subsystems: fs,mm,fs,mm
extid: 98baf51f5cc36dcbe2f7
link: https://syzkaller.appspot.com/bug?extid=98baf51f5cc36dcbe2f7
source: syzbot-dashboard
---

# KCSAN: data-race in __set_task_comm / strlen (2)

来源：[https://syzkaller.appspot.com/bug?extid=98baf51f5cc36dcbe2f7](https://syzkaller.appspot.com/bug?extid=98baf51f5cc36dcbe2f7)

## 崩溃报告

```
==================================================================
BUG: KCSAN: data-race in __set_task_comm / strlen

write to 0xffff88810dddccda of 14 bytes by task 22117 on cpu 0:
 __set_task_comm+0x92/0x180 fs/exec.c:1104
 begin_new_exec+0xee8/0x12b0 fs/exec.c:1297
 load_elf_binary+0x5e2/0x18f0 fs/binfmt_elf.c:1010
 search_binary_handler fs/exec.c:1779 [inline]
 exec_binprm fs/exec.c:1811 [inline]
 bprm_execve+0x46b/0xa50 fs/exec.c:1867
 do_execveat_common+0x7a4/0x8a0 fs/exec.c:1965
 __do_sys_execve fs/exec.c:2038 [inline]
 __se_sys_execve fs/exec.c:2032 [inline]
 __x64_sys_execve+0x5f/0x80 fs/exec.c:2032
 x64_sys_call+0x1cd2/0x2550 arch/x86/include/generated/asm/syscalls_64.h:60
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x112/0x360 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f

read to 0xffff88810dddccda of 1 bytes by task 22105 on cpu 1:
 strlen+0x19/0x40 lib/string.c:402
 __fortify_strlen include/linux/fortify-string.h:218 [inline]
 trace_event_get_offsets_sched_stat_runtime include/trace/events/sched.h:560 [inline]
 do_trace_event_raw_event_sched_stat_runtime include/trace/events/sched.h:553 [inline]
 trace_event_raw_event_sched_stat_runtime+0x5a/0x150 include/trace/events/sched.h:553
 __do_trace_sched_stat_runtime include/trace/events/sched.h:576 [inline]
 trace_sched_stat_runtime include/trace/events/sched.h:576 [inline]
 update_se+0x14f/0x3b0 kernel/sched/fair.c:1425
 update_curr+0x1e/0x210 kernel/sched/fair.c:2239
 update_curr_eevdf kernel/sched/fair.c:8196 [inline]
 enqueue_task_fair+0x77/0x850 kernel/sched/fair.c:8226
 enqueue_task kernel/sched/core.c:2194 [inline]
 activate_task kernel/sched/core.c:2234 [inline]
 ttwu_do_activate+0xa7/0x230 kernel/sched/core.c:3847
 ttwu_queue kernel/sched/core.c:4100 [inline]
 try_to_wake_up+0x44f/0x6d0 kernel/sched/core.c:4438
 kthread_insert_work+0xce/0x180 kernel/kthread.c:1184
 kthread_queue_work+0x78/0xa0 kernel/kthread.c:1207
 synchronize_rcu_expedited_queue_work kernel/rcu/tree_exp.h:498 [inline]
 synchronize_rcu_expedited+0x56e/0x770 kernel/rcu/tree_exp.h:976
 namespace_unlock+0x39a/0x4c0 fs/namespace.c:1724
 class_namespace_excl_destructor fs/namespace.c:90 [inline]
 dissolve_on_fput+0x191/0x1a0 fs/namespace.c:2316
 __fput+0x5df/0x630 fs/file_table.c:522
 ____fput+0x1c/0x30 fs/file_table.c:540
 task_work_run+0x130/0x1a0 kernel/task_work.c:233
 exit_task_work include/linux/task_work.h:40 [inline]
 do_exit+0x4a4/0x1510 kernel/exit.c:986
 __do_sys_exit kernel/exit.c:1096 [inline]
 __se_sys_exit kernel/exit.c:1094 [inline]
 __x64_sys_exit+0x1f/0x20 kernel/exit.c:1094
 x64_sys_call+0x254a/0x2550 arch/x86/include/generated/asm/syscalls_64.h:61
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x112/0x360 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f

value changed: 0x63 -> 0x00

Reported by Kernel Concurrency Sanitizer on:
CPU: 1 UID: 0 PID: 22105 Comm: syz.7.2980 Not tainted syzkaller #0 PREEMPT(lazy) 
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 07/24/2026
==================================================================
```
