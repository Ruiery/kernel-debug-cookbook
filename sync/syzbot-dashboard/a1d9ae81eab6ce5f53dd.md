---
title: KCSAN: data-race in ktime_get_coarse_real_ts64_mg / timekeeping_update_from_shadow
subsystems: kernel
extid: a1d9ae81eab6ce5f53dd
link: https://syzkaller.appspot.com/bug?extid=a1d9ae81eab6ce5f53dd
source: syzbot-dashboard
---

# KCSAN: data-race in ktime_get_coarse_real_ts64_mg / timekeeping_update_from_shadow

来源：[https://syzkaller.appspot.com/bug?extid=a1d9ae81eab6ce5f53dd](https://syzkaller.appspot.com/bug?extid=a1d9ae81eab6ce5f53dd)

## 崩溃报告

```
==================================================================
BUG: KCSAN: data-race in ktime_get_coarse_real_ts64_mg / timekeeping_update_from_shadow

write to 0xffffffff895f6508 of 320 bytes by interrupt on cpu 0:
 timekeeping_update_from_shadow+0x448/0x480 kernel/time/timekeeping.c:866
 __timekeeping_advance+0xb36/0xcf0 kernel/time/timekeeping.c:2663
 timekeeping_advance kernel/time/timekeeping.c:2671 [inline]
 update_wall_time+0x21/0x50 kernel/time/timekeeping.c:2681
 tick_do_update_jiffies64+0x169/0x1c0 kernel/time/tick-sched.c:149
 tick_sched_do_timer kernel/time/tick-sched.c:253 [inline]
 tick_nohz_handler+0x88/0x380 kernel/time/tick-sched.c:310
 __run_hrtimer kernel/time/hrtimer.c:2074 [inline]
 __hrtimer_run_queues+0x1f8/0x510 kernel/time/hrtimer.c:2131
 hrtimer_interrupt+0x27b/0x860 kernel/time/hrtimer.c:2250
 local_apic_timer_interrupt arch/x86/kernel/apic/apic.c:1051 [inline]
 __sysvec_apic_timer_interrupt+0x5f/0x1c0 arch/x86/kernel/apic/apic.c:1068
 instr_sysvec_apic_timer_interrupt arch/x86/kernel/apic/apic.c:1062 [inline]
 sysvec_apic_timer_interrupt+0x6f/0x80 arch/x86/kernel/apic/apic.c:1062
 asm_sysvec_apic_timer_interrupt+0x1a/0x20 arch/x86/include/asm/idtentry.h:674
 kcsan_setup_watchpoint+0x42b/0x4a0 kernel/kcsan/core.c:713
 __import_iovec+0x321/0x530 lib/iov_iter.c:-1
 import_iovec+0x60/0x80 lib/iov_iter.c:1440
 copy_msghdr_from_user net/socket.c:2650 [inline]
 recvmsg_copy_msghdr net/socket.c:2899 [inline]
 ___sys_recvmsg+0x385/0x3a0 net/socket.c:2971
 do_recvmmsg+0x1e5/0x560 net/socket.c:3070
 __sys_recvmmsg net/socket.c:3144 [inline]
 __do_sys_recvmmsg net/socket.c:3167 [inline]
 __se_sys_recvmmsg net/socket.c:3160 [inline]
 __x64_sys_recvmmsg+0xe5/0x170 net/socket.c:3160
 x64_sys_call+0x77f/0x2550 arch/x86/include/generated/asm/syscalls_64.h:300
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x112/0x360 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f

read to 0xffffffff895f6578 of 4 bytes by task 19476 on cpu 1:
 tk_xtime_coarse kernel/time/timekeeping.c:217 [inline]
 ktime_get_coarse_real_ts64_mg+0x89/0x1a0 kernel/time/timekeeping.c:2737
 inode_set_ctime_current+0x55/0x8f0 fs/inode.c:2890
 simple_inode_init_ts fs/libfs.c:2127 [inline]
 prepare_anon_dentry fs/libfs.c:2167 [inline]
 path_from_stashed+0x12d/0x330 fs/libfs.c:2246
 ns_get_path_cb fs/nsfs.c:76 [inline]
 ns_get_path+0x62/0x80 fs/nsfs.c:99
 proc_ns_get_link+0xdd/0x1c0 fs/proc/namespaces.c:66
 pick_link+0x4b1/0x8e0 fs/namei.c:-1
 step_into_slowpath+0x36a/0x4c0 fs/namei.c:2127
 step_into fs/namei.c:2152 [inline]
 open_last_lookups fs/namei.c:4780 [inline]
 path_openat+0x665/0x10d0 fs/namei.c:4997
 do_file_open+0x16c/0x290 fs/namei.c:5029
 do_sys_openat2+0xa0/0x130 fs/open.c:1417
 do_sys_open fs/open.c:1423 [inline]
 __do_sys_openat fs/open.c:1439 [inline]
 __se_sys_openat fs/open.c:1434 [inline]
 __x64_sys_openat+0xf2/0x120 fs/open.c:1434
 x64_sys_call+0x1f72/0x2550 arch/x86/include/generated/asm/syscalls_64.h:258
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x112/0x360 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f

value changed: 0x1c7e9d05 -> 0x1d0b779c

Reported by Kernel Concurrency Sanitizer on:
CPU: 1 UID: 0 PID: 19476 Comm: syz.6.3334 Not tainted syzkaller #0 PREEMPT(lazy) 
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 07/24/2026
==================================================================
vfat: Unknown parameter '0xffffffffffffffff'
```
