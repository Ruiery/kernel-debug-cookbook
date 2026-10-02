---
title: linux-next test error: WARNING: locking bug in change_page_attr_set_clr
subsystems: kernel
extid: ee7ecfcd0e3f185e835a
link: https://syzkaller.appspot.com/bug?extid=ee7ecfcd0e3f185e835a
source: syzbot-dashboard
---

# linux-next test error: WARNING: locking bug in change_page_attr_set_clr

来源：[https://syzkaller.appspot.com/bug?extid=ee7ecfcd0e3f185e835a](https://syzkaller.appspot.com/bug?extid=ee7ecfcd0e3f185e835a)

## 崩溃报告

```
clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 19112604462750000 ns
kfence: initialized - using 2097152 bytes for 255 objects at 0xffff88823be00000-0xffff88823c000000
Console: colour VGA+ 80x25
printk: legacy console [ttyS0] enabled
printk: legacy console [ttyS0] enabled
printk: legacy bootconsole [earlyser0] disabled
printk: legacy bootconsole [earlyser0] disabled
Lock dependency validator: Copyright (c) 2006 Red Hat, Inc., Ingo Molnar
... MAX_LOCKDEP_SUBCLASSES:  8
... MAX_LOCK_DEPTH:          48
... MAX_LOCKDEP_KEYS:        8192
... CLASSHASH_SIZE:          4096
... MAX_LOCKDEP_ENTRIES:     1048576
... MAX_LOCKDEP_CHAINS:      1048576
... CHAINHASH_SIZE:          524288
 memory used by lock dependency info: 106625 kB
 memory used for stack traces: 8320 kB
 per task-struct memory footprint: 1920 bytes
mempolicy: Enabling automatic NUMA balancing. Configure with numa_balancing= or the kernel.numa_balancing sysctl
ACPI: Core revision 20260408
APIC: Switch to symmetric I/O mode setup
x2apic enabled
APIC: Switched APIC routing to: physical x2apic
..TIMER: vector=0x30 apic1=0 pin1=0 apic2=-1 pin2=-1
clocksource: tsc-early: mask: 0xffffffffffffffff max_cycles: 0x1fb63109b96, max_idle_ns: 440795265316 ns
Calibrating delay loop (skipped) preset value.. 4399.99 BogoMIPS (lpj=21999980)
Last level iTLB entries: 4KB 64, 2MB 8, 4MB 8
Last level dTLB entries: 4KB 64, 2MB 32, 4MB 32, 1GB 4
mitigations: Enabled attack vectors: user_kernel, user_user, guest_host, guest_guest, SMT mitigations: auto
Speculative Store Bypass: Mitigation: Speculative Store Bypass disabled via prctl
Spectre V2 : Mitigation: IBRS
RETBleed: Mitigation: IBRS
ITS: Mitigation: Aligned branch/return thunks
Spectre V2 : User space: Mitigation: STIBP via prctl
MDS: Mitigation: Clear CPU buffers
TAA: Mitigation: Clear CPU buffers
MMIO Stale Data: Vulnerable: Clear CPU buffers attempted, no microcode
Spectre V1 : Mitigation: usercopy/swapgs barriers and __user pointer sanitization
Spectre V2 : Spectre v2 / SpectreRSB: Filling RSB on context switch and VMEXIT
Spectre V2 : Enabling IBPB for BPF
Spectre V2 : mitigation: Enabling conditional Indirect Branch Prediction Barrier
active return thunk: its_return_thunk
Spectre V2 : Spectre BHI mitigation: SW BHB clearing on syscall and VM exit
x86/fpu: Supporting XSAVE feature 0x001: 'x87 floating point registers'
x86/fpu: Supporting XSAVE feature 0x002: 'SSE registers'
x86/fpu: Supporting XSAVE feature 0x004: 'AVX registers'
x86/fpu: xstate_offset[2]:  576, xstate_sizes[2]:  256
x86/fpu: Enabled xstate features 0x7, context size is 832 bytes, using 'standard' format.

=============================
[ BUG: Invalid wait context ]
syzkaller #0 Not tainted
-----------------------------
swapper/0/0 is trying to lock:
ffffffff8f088c78 ((init_mm).mmap_lock){....}-{4:4}, at: mmap_read_lock include/linux/mmap_lock.h:600 [inline]
ffffffff8f088c78 ((init_mm).mmap_lock){....}-{4:4}, at: class_mmap_read_lock_constructor include/linux/mmap_lock.h:631 [inline]
ffffffff8f088c78 ((init_mm).mmap_lock){....}-{4:4}, at: cpa_collapse_large_pages arch/x86/mm/pat/set_memory.c:448 [inline]
ffffffff8f088c78 ((init_mm).mmap_lock){....}-{4:4}, at: cpa_flush arch/x86/mm/pat/set_memory.c:494 [inline]
ffffffff8f088c78 ((init_mm).mmap_lock){....}-{4:4}, at: change_page_attr_set_clr+0xc2c/0x1010 arch/x86/mm/pat/set_memory.c:2142
other info that might help us debug this:
context-{5:5}
locks held by swapper/0/0: 1, last CPU#0:
 #0: ffffffff8edc2078 (cpa_lock){+.+.}-{3:3}, at: spin_lock include/linux/spinlock.h:342 [inline]
 #0: ffffffff8edc2078 (cpa_lock){+.+.}-{3:3}, at: cpa_collapse_large_pages arch/x86/mm/pat/set_memory.c:421 [inline]
 #0: ffffffff8edc2078 (cpa_lock){+.+.}-{3:3}, at: cpa_flush arch/x86/mm/pat/set_memory.c:494 [inline]
 #0: ffffffff8edc2078 (cpa_lock){+.+.}-{3:3}, at: change_page_attr_set_clr+0x967/0x1010 arch/x86/mm/pat/set_memory.c:2142
stack backtrace:
CPU: 0 UID: 0 PID: 0 Comm: swapper/0 Not tainted syzkaller #0 PREEMPT(full) 
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 06/25/2026
Call Trace:
 <TASK>
 dump_stack_lvl+0xe8/0x150 lib/dump_stack.c:120
 print_lock_invalid_wait_context kernel/locking/lockdep.c:4846 [inline]
 check_wait_context kernel/locking/lockdep.c:4918 [inline]
 __lock_acquire+0xef0/0x2e50 kernel/locking/lockdep.c:5204
 lock_acquire+0x115/0x350 kernel/locking/lockdep.c:5906
 down_read+0x4a/0x330 kernel/locking/rwsem.c:1574
 mmap_read_lock include/linux/mmap_lock.h:600 [inline]
 class_mmap_read_lock_constructor include/linux/mmap_lock.h:631 [inline]
 cpa_collapse_large_pages arch/x86/mm/pat/set_memory.c:448 [inline]
 cpa_flush arch/x86/mm/pat/set_memory.c:494 [inline]
 change_page_attr_set_clr+0xc2c/0x1010 arch/x86/mm/pat/set_memory.c:2142
 set_memory_rox+0xbe/0x100 arch/x86/mm/pat/set_memory.c:2341
 its_pages_protect arch/x86/kernel/alternative.c:168 [inline]
 its_fini_core arch/x86/kernel/alternative.c:175 [inline]
 alternative_instructions+0x95/0x100 arch/x86/kernel/alternative.c:2264
 arch_cpu_finalize_init+0xb2/0x1f0 arch/x86/kernel/cpu/common.c:2633
 start_kernel+0x310/0x3e0 init/main.c:1153
 x86_64_start_reservations+0x24/0x30 arch/x86/kernel/head64.c:310
 x86_64_start_kernel+0x137/0x1b0 arch/x86/kernel/head64.c:291
 common_startup_64+0x13e/0x157
 </TASK>
pid_max: default: 32768 minimum: 301
landlock: Up and running.
Yama: becoming mindful.
TOMOYO Linux initialized
AppArmor: AppArmor initialized
LSM support for eBPF active
Dentry cache hash table entries: 1048576 (order: 11, 8388608 bytes, vmalloc hugepage)
Inode-cache hash table entries: 524288 (order: 10, 4194304 bytes, vmalloc hugepage)
Mount-cache hash table entries: 16384 (order: 5, 131072 bytes, vmalloc)
Mountpoint-cache hash table entries: 16384 (order: 5, 131072 bytes, vmalloc)
VFS: Finished mounting rootfs on nullfs
Running RCU synchronous self tests
Running RCU synchronous self tests
numa_add_cpu cpu 1 node 0: mask now 0-1
numa_add_cpu cpu 1 node 1: mask now 0-1
```
