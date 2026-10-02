---
title: KCSAN: data-race in shmem_fallocate / shmem_writeout
subsystems: mm
extid: aae8bd56cc1c38d50ec4
link: https://syzkaller.appspot.com/bug?extid=aae8bd56cc1c38d50ec4
source: syzbot-dashboard
---

# KCSAN: data-race in shmem_fallocate / shmem_writeout

来源：[https://syzkaller.appspot.com/bug?extid=aae8bd56cc1c38d50ec4](https://syzkaller.appspot.com/bug?extid=aae8bd56cc1c38d50ec4)

## 崩溃报告

```
==================================================================
BUG: KCSAN: data-race in shmem_fallocate / shmem_writeout

write to 0xffffc90002fcbcb0 of 8 bytes by task 13428 on cpu 1:
 shmem_fallocate+0x72e/0x8d0 mm/shmem.c:3768
 vfs_fallocate+0x3ac/0x400 fs/open.c:338
 ioctl_preallocate fs/ioctl.c:289 [inline]
 file_ioctl+0x4e1/0x5b0 fs/ioctl.c:-1
 do_vfs_ioctl+0x7c4/0xe50 fs/ioctl.c:576
 __do_sys_ioctl fs/ioctl.c:595 [inline]
 __se_sys_ioctl+0x82/0x140 fs/ioctl.c:583
 __x64_sys_ioctl+0x43/0x50 fs/ioctl.c:583
 x64_sys_call+0x239d/0x2550 arch/x86/include/generated/asm/syscalls_64.h:17
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x112/0x360 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f

read to 0xffffc90002fcbcb0 of 8 bytes by task 13434 on cpu 0:
 shmem_writeout+0x2b6/0x8f0 mm/shmem.c:1683
 pageout mm/vmscan.c:658 [inline]
 shrink_folio_list+0x1a81/0x26f0 mm/vmscan.c:1397
 evict_folios+0x1c6e/0x2830 mm/vmscan.c:4910
 try_to_shrink_lruvec+0x8fd/0xb30 mm/vmscan.c:5076
 lru_gen_shrink_lruvec mm/vmscan.c:5221 [inline]
 shrink_lruvec+0x252/0x1d40 mm/vmscan.c:5981
 shrink_node_memcgs mm/vmscan.c:6220 [inline]
 shrink_node+0x67c/0x2000 mm/vmscan.c:6264
 shrink_zones mm/vmscan.c:6503 [inline]
 do_try_to_free_pages+0x408/0xca0 mm/vmscan.c:6565
 try_to_free_mem_cgroup_pages+0x201/0x420 mm/vmscan.c:6887
 mem_cgroup_resize_max+0x13d/0x290 mm/memcontrol-v1.c:1816
 mem_cgroup_write+0x132/0x1c0 mm/memcontrol-v1.c:-1
 cgroup_file_write+0x197/0x350 kernel/cgroup/cgroup.c:4412
 kernfs_fop_write_iter+0x1d2/0x2e0 fs/kernfs/file.c:345
 new_sync_write fs/read_write.c:595 [inline]
 vfs_write+0x57f/0x9a0 fs/read_write.c:687
 ksys_write+0xdc/0x1a0 fs/read_write.c:739
 __do_sys_write fs/read_write.c:750 [inline]
 __se_sys_write fs/read_write.c:747 [inline]
 __x64_sys_write+0x40/0x50 fs/read_write.c:747
 x64_sys_call+0x154e/0x2550 arch/x86/include/generated/asm/syscalls_64.h:2
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x112/0x360 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f

value changed: 0x0000000000000fad -> 0x0000000000000fae

Reported by Kernel Concurrency Sanitizer on:
CPU: 0 UID: 0 PID: 13434 Comm: syz.4.2166 Not tainted syzkaller #0 PREEMPT(lazy) 
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 07/24/2026
==================================================================
```
