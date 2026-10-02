---
title: WARNING in null_report_zones
subsystems: block
extid: 67f80b67c0cfaa3bb3bb
link: https://syzkaller.appspot.com/bug?extid=67f80b67c0cfaa3bb3bb
source: syzbot-dashboard
---

# WARNING in null_report_zones

来源：[https://syzkaller.appspot.com/bug?extid=67f80b67c0cfaa3bb3bb](https://syzkaller.appspot.com/bug?extid=67f80b67c0cfaa3bb3bb)

## 崩溃报告

```
null_blk: nullb1: using native zone append
------------[ cut here ]------------
DEBUG_LOCKS_WARN_ON(lock->magic != lock)
WARNING: kernel/locking/mutex.c:625 at __mutex_lock_common kernel/locking/mutex.c:625 [inline], CPU#0: syz.0.17/5967
WARNING: kernel/locking/mutex.c:625 at __mutex_lock+0x944/0x1bc0 kernel/locking/mutex.c:821, CPU#0: syz.0.17/5967
Modules linked in:
CPU: 0 UID: 0 PID: 5967 Comm: syz.0.17 Not tainted syzkaller #0 PREEMPT(full) 
Hardware name: QEMU Standard PC (Q35 + ICH9, 2009), BIOS 1.16.3-debian-1.16.3-2 04/01/2014
RIP: 0010:__mutex_lock_common kernel/locking/mutex.c:625 [inline]
RIP: 0010:__mutex_lock+0x94b/0x1bc0 kernel/locking/mutex.c:821
Code: 0f b6 14 11 38 d0 7c 08 84 d2 0f 85 b4 10 00 00 44 8b 05 08 bf 81 05 45 85 c0 75 13 48 8d 3d 5c 1d 85 05 48 c7 c6 a0 df ef 8b <67> 48 0f b9 3a 90 e9 1b f8 ff ff 4d 8d a7 f0 0a 00 00 4c 89 e7 e8
RSP: 0018:ffffc9000634f680 EFLAGS: 00010246
RAX: 0000000000000003 RBX: ffff888047c00000 RCX: 1ffffffff2284a30
RDX: 0000000000000000 RSI: ffffffff8befdfa0 RDI: ffffffff9145afe0
RBP: ffffc9000634f7f0 R08: 0000000000000000 R09: 0000000000000000
R10: 0000000000000000 R11: 0000000000000000 R12: 0000000000000000
R13: 0000000000000000 R14: dffffc0000000000 R15: ffffed100ab768d4
FS:  00007fd5599d66c0(0000) GS:ffff8880d5bd4000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 0000000000000000 CR3: 0000000059f3c000 CR4: 0000000000352ef0
Call Trace:
 <TASK>
 null_lock_zone drivers/block/null_blk/zoned.c:39 [inline]
 null_lock_zone drivers/block/null_blk/zoned.c:33 [inline]
 null_report_zones+0x4af/0x6f0 drivers/block/null_blk/zoned.c:219
 blk_revalidate_disk_zones+0x492/0xce0 block/blk-zoned.c:2384
 null_add_dev+0x125f/0x1df0 drivers/block/null_blk/main.c:2047
 nullb_device_power_store+0x29d/0x350 drivers/block/null_blk/main.c:501
 flush_write_buffer fs/configfs/file.c:207 [inline]
 configfs_write_iter+0x302/0x4e0 fs/configfs/file.c:229
 new_sync_write fs/read_write.c:595 [inline]
 vfs_write+0x6af/0x1050 fs/read_write.c:687
 ksys_write+0x12a/0x250 fs/read_write.c:739
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x123/0x790 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f
RIP: 0033:0x7fd558b9e0d9
Code: ff c3 66 2e 0f 1f 84 00 00 00 00 00 0f 1f 44 00 00 48 89 f8 48 89 f7 48 89 d6 48 89 ca 4d 89 c2 4d 89 c8 4c 8b 4c 24 08 0f 05 <48> 3d 01 f0 ff ff 73 01 c3 48 c7 c1 e8 ff ff ff f7 d8 64 89 01 48
RSP: 002b:00007fd5599d6028 EFLAGS: 00000246 ORIG_RAX: 0000000000000001
RAX: ffffffffffffffda RBX: 00007fd558e25fa0 RCX: 00007fd558b9e0d9
RDX: 0000000000000001 RSI: 0000200000000700 RDI: 0000000000000004
RBP: 00007fd558c35024 R08: 0000000000000000 R09: 0000000000000000
R10: 0000000000000000 R11: 0000000000000246 R12: 0000000000000000
R13: 00007fd558e26038 R14: 00007fd558e25fa0 R15: 00007fffab806348
 </TASK>
----------------
Code disassembly (best guess):
   0:	0f b6 14 11          	movzbl (%rcx,%rdx,1),%edx
   4:	38 d0                	cmp    %dl,%al
   6:	7c 08                	jl     0x10
   8:	84 d2                	test   %dl,%dl
   a:	0f 85 b4 10 00 00    	jne    0x10c4
  10:	44 8b 05 08 bf 81 05 	mov    0x581bf08(%rip),%r8d        # 0x581bf1f
  17:	45 85 c0             	test   %r8d,%r8d
  1a:	75 13                	jne    0x2f
  1c:	48 8d 3d 5c 1d 85 05 	lea    0x5851d5c(%rip),%rdi        # 0x5851d7f
  23:	48 c7 c6 a0 df ef 8b 	mov    $0xffffffff8befdfa0,%rsi
* 2a:	67 48 0f b9 3a       	ud1    (%edx),%rdi <-- trapping instruction
  2f:	90                   	nop
  30:	e9 1b f8 ff ff       	jmp    0xfffff850
  35:	4d 8d a7 f0 0a 00 00 	lea    0xaf0(%r15),%r12
  3c:	4c 89 e7             	mov    %r12,%rdi
  3f:	e8                   	.byte 0xe8
```
