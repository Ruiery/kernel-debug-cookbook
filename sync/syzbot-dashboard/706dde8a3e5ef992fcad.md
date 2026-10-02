---
title: KCSAN: data-race in shmem_file_splice_read / shmem_file_splice_read
subsystems: mm
extid: 706dde8a3e5ef992fcad
link: https://syzkaller.appspot.com/bug?extid=706dde8a3e5ef992fcad
source: syzbot-dashboard
---

# KCSAN: data-race in shmem_file_splice_read / shmem_file_splice_read

来源：[https://syzkaller.appspot.com/bug?extid=706dde8a3e5ef992fcad](https://syzkaller.appspot.com/bug?extid=706dde8a3e5ef992fcad)

## 崩溃报告

```
==================================================================
BUG: KCSAN: data-race in shmem_file_splice_read / shmem_file_splice_read

write to 0xffff88810b2e6d60 of 8 bytes by task 10298 on cpu 0:
 shmem_file_splice_read+0x401/0x590 mm/shmem.c:3592
 do_splice_read fs/splice.c:980 [inline]
 splice_direct_to_actor+0x261/0x680 fs/splice.c:1084
 do_splice_direct_actor fs/splice.c:1202 [inline]
 do_splice_direct+0x119/0x1a0 fs/splice.c:1228
 do_sendfile+0x37d/0x640 fs/read_write.c:1371
 __do_sys_sendfile64 fs/read_write.c:1432 [inline]
 __se_sys_sendfile64 fs/read_write.c:1418 [inline]
 __x64_sys_sendfile64+0x105/0x150 fs/read_write.c:1418
 x64_sys_call+0x1015/0x2550 arch/x86/include/generated/asm/syscalls_64.h:41
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x112/0x360 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f

write to 0xffff88810b2e6d60 of 8 bytes by task 10297 on cpu 1:
 shmem_file_splice_read+0x401/0x590 mm/shmem.c:3592
 do_splice_read fs/splice.c:980 [inline]
 splice_direct_to_actor+0x261/0x680 fs/splice.c:1084
 do_splice_direct_actor fs/splice.c:1202 [inline]
 do_splice_direct+0x119/0x1a0 fs/splice.c:1228
 do_sendfile+0x37d/0x640 fs/read_write.c:1371
 __do_sys_sendfile64 fs/read_write.c:1432 [inline]
 __se_sys_sendfile64 fs/read_write.c:1418 [inline]
 __x64_sys_sendfile64+0x105/0x150 fs/read_write.c:1418
 x64_sys_call+0x1015/0x2550 arch/x86/include/generated/asm/syscalls_64.h:41
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x112/0x360 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f

value changed: 0x000000000000550f -> 0x0000000000005510

Reported by Kernel Concurrency Sanitizer on:
CPU: 1 UID: 0 PID: 10297 Comm: syz.5.2752 Not tainted syzkaller #0 PREEMPT(lazy) 
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 09/16/2026
==================================================================
```
