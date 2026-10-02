---
title: general protection fault in __device_attach (2)
subsystems: kernel,kernel
extid: de42beb9ccc760a210ab
link: https://syzkaller.appspot.com/bug?extid=de42beb9ccc760a210ab
source: syzbot-dashboard
---

# general protection fault in __device_attach (2)

来源：[https://syzkaller.appspot.com/bug?extid=de42beb9ccc760a210ab](https://syzkaller.appspot.com/bug?extid=de42beb9ccc760a210ab)

## 崩溃报告

```
ret_from_fork_asm+0x1a/0x30 arch/x86/entry/entry_64.S:245
 </TASK>
serio serio2: device_add() failed for  (), error: -12
Oops: general protection fault, probably for non-canonical address 0xdffffc0000000021: 0000 [#1] SMP KASAN NOPTI
KASAN: null-ptr-deref in range [0x0000000000000108-0x000000000000010f]
CPU: 2 UID: 0 PID: 847 Comm: kworker/2:2 Not tainted syzkaller #0 PREEMPT(full) 
Hardware name: QEMU Standard PC (Q35 + ICH9, 2009), BIOS 1.16.3-debian-1.16.3-2 04/01/2014
Workqueue: events_long serio_handle_event
RIP: 0010:__device_attach+0xb0/0x4d0 drivers/base/dd.c:1074
Code: c1 e8 03 42 80 3c 28 00 0f 85 d1 03 00 00 48 ba 00 00 00 00 00 fc ff df 4c 8b 7b 48 49 8d bf 08 01 00 00 48 89 f9 48 c1 e9 03 <0f> b6 14 11 84 d2 74 06 0f 8e 9d 03 00 00 45 0f b6 af 08 01 00 00
RSP: 0018:ffffc90004ee7b40 EFLAGS: 00010206
RAX: 1ffff110068d6a48 RBX: ffff8880346b51f8 RCX: 0000000000000021
RDX: dffffc0000000000 RSI: ffffffff8c400400 RDI: 0000000000000108
RBP: 1ffff920009dcf69 R08: 0000000000000000 R09: fffffbfff224331a
R10: ffffc90004ee7b40 R11: 0000000000000000 R12: 0000000000000000
R13: dffffc0000000000 R14: ffff8880346b52c0 R15: 0000000000000000
FS:  0000000000000000(0000) GS:ffff8880d5fe9000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 00007fdf29b81d58 CR3: 000000000e994000 CR4: 0000000000352ef0
Call Trace:
 <TASK>
 serio_find_driver drivers/input/serio/serio.c:112 [inline]
 serio_handle_event+0x60a/0x990 drivers/input/serio/serio.c:206
 process_one_work+0xa23/0x1940 kernel/workqueue.c:3322
 process_scheduled_works kernel/workqueue.c:3405 [inline]
 worker_thread+0x5ef/0xe50 kernel/workqueue.c:3486
 kthread+0x370/0x450 kernel/kthread.c:436
 ret_from_fork+0x72b/0xd50 arch/x86/kernel/process.c:158
 ret_from_fork_asm+0x1a/0x30 arch/x86/entry/entry_64.S:245
 </TASK>
Modules linked in:
---[ end trace 0000000000000000 ]---
RIP: 0010:__device_attach+0xb0/0x4d0 drivers/base/dd.c:1074
Code: c1 e8 03 42 80 3c 28 00 0f 85 d1 03 00 00 48 ba 00 00 00 00 00 fc ff df 4c 8b 7b 48 49 8d bf 08 01 00 00 48 89 f9 48 c1 e9 03 <0f> b6 14 11 84 d2 74 06 0f 8e 9d 03 00 00 45 0f b6 af 08 01 00 00
RSP: 0018:ffffc90004ee7b40 EFLAGS: 00010206
RAX: 1ffff110068d6a48 RBX: ffff8880346b51f8 RCX: 0000000000000021
RDX: dffffc0000000000 RSI: ffffffff8c400400 RDI: 0000000000000108
RBP: 1ffff920009dcf69 R08: 0000000000000000 R09: fffffbfff224331a
R10: ffffc90004ee7b40 R11: 0000000000000000 R12: 0000000000000000
R13: dffffc0000000000 R14: ffff8880346b52c0 R15: 0000000000000000
FS:  0000000000000000(0000) GS:ffff8880d5fe9000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 00007fdf29b81d58 CR3: 000000000e994000 CR4: 0000000000352ef0
----------------
Code disassembly (best guess):
   0:	c1 e8 03             	shr    $0x3,%eax
   3:	42 80 3c 28 00       	cmpb   $0x0,(%rax,%r13,1)
   8:	0f 85 d1 03 00 00    	jne    0x3df
   e:	48 ba 00 00 00 00 00 	movabs $0xdffffc0000000000,%rdx
  15:	fc ff df
  18:	4c 8b 7b 48          	mov    0x48(%rbx),%r15
  1c:	49 8d bf 08 01 00 00 	lea    0x108(%r15),%rdi
  23:	48 89 f9             	mov    %rdi,%rcx
  26:	48 c1 e9 03          	shr    $0x3,%rcx
* 2a:	0f b6 14 11          	movzbl (%rcx,%rdx,1),%edx <-- trapping instruction
  2e:	84 d2                	test   %dl,%dl
  30:	74 06                	je     0x38
  32:	0f 8e 9d 03 00 00    	jle    0x3d5
  38:	45 0f b6 af 08 01 00 	movzbl 0x108(%r15),%r13d
  3f:	00
```
