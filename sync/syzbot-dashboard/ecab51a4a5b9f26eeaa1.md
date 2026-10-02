---
title: WARNING in ext4_dirty_folio
subsystems: mm,mm
extid: ecab51a4a5b9f26eeaa1
link: https://syzkaller.appspot.com/bug?extid=ecab51a4a5b9f26eeaa1
source: syzbot-dashboard
---

# WARNING in ext4_dirty_folio

来源：[https://syzkaller.appspot.com/bug?extid=ecab51a4a5b9f26eeaa1](https://syzkaller.appspot.com/bug?extid=ecab51a4a5b9f26eeaa1)

## 崩溃报告

```
------------[ cut here ]------------
!folio_buffers(folio)
WARNING: fs/ext4/inode.c:3938 at ext4_dirty_folio+0x17e/0x1e0 fs/ext4/inode.c:3938, CPU#1: syz.0.18/5892
Modules linked in:
CPU: 1 UID: 0 PID: 5892 Comm: syz.0.18 Not tainted syzkaller #0 PREEMPT(full) 
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 04/18/2026
RIP: 0010:ext4_dirty_folio+0x17e/0x1e0 fs/ext4/inode.c:3938
Code: f8 ad 39 ff 90 0f 0b 90 e9 2e ff ff ff e8 ea ad 39 ff 48 c7 c6 e0 1e cd 8b 48 89 df e8 6b d9 87 ff 90 0f 0b e8 d3 ad 39 ff 90 <0f> 0b 90 e9 38 ff ff ff e8 c5 ad 39 ff 48 c7 c6 e0 1e cd 8b 48 89
RSP: 0018:ffffc900035df9f0 EFLAGS: 00010293
RAX: 0000000000000000 RBX: ffffea0001b36e00 RCX: ffffffff82cee0ba
RDX: ffff8880305a9ec0 RSI: ffffffff82cee1ad RDI: ffffea0001b36e28
RBP: 0000000000000001 R08: 0000000000000001 R09: 0000000000000000
R10: 0000000000000001 R11: 0000000000000000 R12: ffff88806d7c6210
R13: ffffea0001b36e08 R14: ffff888077107d20 R15: 0000000000000068
FS:  00007f6ec7a5a6c0(0000) GS:ffff88812446b000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 0000200000003000 CR3: 00000000334d9000 CR4: 0000000000350ef0
Call Trace:
 <TASK>
 folio_mark_dirty+0x10a/0x200 mm/page-writeback.c:2792
 folio_mark_dirty_lock+0x90/0xe0 mm/page-writeback.c:2814
 set_page_dirty_lock+0x44/0x60 mm/folio-compat.c:52
 fuse_copy_finish+0x2e7/0x3a0 fs/fuse/dev.c:866
 fuse_dev_do_read+0x1640/0x2420 fs/fuse/dev.c:1509
 fuse_dev_read+0x15e/0x1e0 fs/fuse/dev.c:1586
 new_sync_read fs/read_write.c:493 [inline]
 vfs_read+0x825/0xb30 fs/read_write.c:574
 ksys_read+0x12a/0x250 fs/read_write.c:717
 do_syscall_x64 arch/x86/entry/syscall_64.c:63 [inline]
 do_syscall_64+0x10b/0xf80 arch/x86/entry/syscall_64.c:94
 entry_SYSCALL_64_after_hwframe+0x77/0x7f
RIP: 0033:0x7f6ec6b9ce59
Code: ff c3 66 2e 0f 1f 84 00 00 00 00 00 0f 1f 44 00 00 48 89 f8 48 89 f7 48 89 d6 48 89 ca 4d 89 c2 4d 89 c8 4c 8b 4c 24 08 0f 05 <48> 3d 01 f0 ff ff 73 01 c3 48 c7 c1 e8 ff ff ff f7 d8 64 89 01 48
RSP: 002b:00007f6ec7a5a028 EFLAGS: 00000246 ORIG_RAX: 0000000000000000
RAX: ffffffffffffffda RBX: 00007f6ec6e16090 RCX: 00007f6ec6b9ce59
RDX: 0000000000002020 RSI: 00002000000021c0 RDI: 0000000000000006
RBP: 00007f6ec6c32d6f R08: 0000000000000000 R09: 0000000000000000
R10: 0000000000000000 R11: 0000000000000246 R12: 0000000000000000
R13: 00007f6ec6e16128 R14: 00007f6ec6e16090 R15: 00007ffef6a15f58
 </TASK>
```
