---
title: general protection fault in regmap_get_i2c_bus
subsystems: kernel
extid: 6c7e68b141ebd3a2cadf
link: https://syzkaller.appspot.com/bug?extid=6c7e68b141ebd3a2cadf
source: syzbot-dashboard
---

# general protection fault in regmap_get_i2c_bus

来源：[https://syzkaller.appspot.com/bug?extid=6c7e68b141ebd3a2cadf](https://syzkaller.appspot.com/bug?extid=6c7e68b141ebd3a2cadf)

## 崩溃报告

```
Oops: general protection fault, probably for non-canonical address 0xdffffc0000000003: 0000 [#1] SMP KASAN NOPTI
KASAN: null-ptr-deref in range [0x0000000000000018-0x000000000000001f]
CPU: 0 UID: 0 PID: 5929 Comm: syz.0.17 Not tainted syzkaller #0 PREEMPT(full) 
Hardware name: QEMU Standard PC (Q35 + ICH9, 2009), BIOS 1.16.3-debian-1.16.3-2 04/01/2014
RIP: 0010:regmap_get_i2c_bus+0xbe/0xc60 drivers/base/regmap/regmap-i2c.c:360
Code: 89 c6 e8 f5 8b a3 fb 45 85 e4 0f 85 84 01 00 00 e8 77 91 a3 fb 4c 8d 73 1c 48 b8 00 00 00 00 00 fc ff df 4c 89 f2 48 c1 ea 03 <0f> b6 14 02 4c 89 f0 83 e0 07 83 c0 03 38 d0 7c 08 84 d2 0f 85 a2
RSP: 0018:ffffc900042ef568 EFLAGS: 00010207
RAX: dffffc0000000000 RBX: 0000000000000000 RCX: ffffffff8666d35b
RDX: 0000000000000003 RSI: ffffffff8666d369 RDI: ffff88802be1a540
RBP: ffff8880552ba000 R08: 0000000000000005 R09: 0000000000000000
R10: 0000000000000000 R11: 0000000000000000 R12: 0000000000000000
R13: ffff8880552ba018 R14: 000000000000001c R15: ffff8880552ba000
FS:  000055558b984500(0000) GS:ffff8880d5dd8000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 0000001b33263fff CR3: 000000004714c000 CR4: 0000000000352ef0
Call Trace:
 <TASK>
 __devm_regmap_init_i2c+0x28/0x80 drivers/base/regmap/regmap-i2c.c:439
 stusb160x_probe+0xe4/0x1ae0 drivers/usb/typec/stusb160x.c:649
 i2c_device_probe+0x658/0xd10 drivers/i2c/i2c-core-base.c:592
 call_driver_probe drivers/base/dd.c:628 [inline]
 really_probe+0x241/0xa60 drivers/base/dd.c:706
 __driver_probe_device+0x20e/0x450 drivers/base/dd.c:868
 driver_probe_device+0x4a/0x140 drivers/base/dd.c:898
 __device_attach_driver+0x1df/0x320 drivers/base/dd.c:1026
 bus_for_each_drv+0x159/0x1e0 drivers/base/bus.c:500
 __device_attach+0x1e4/0x4d0 drivers/base/dd.c:1098
 device_initial_probe+0xaf/0xd0 drivers/base/dd.c:1153
 bus_probe_device+0x64/0x160 drivers/base/bus.c:620
 device_add+0x121d/0x1970 drivers/base/core.c:3772
 i2c_new_client_device+0x660/0xd30 drivers/i2c/i2c-core-base.c:1019
 new_device_store+0x20f/0x420 drivers/i2c/i2c-core-base.c:1307
 dev_attr_store+0x58/0x80 drivers/base/core.c:2505
 sysfs_kf_write+0xf2/0x150 fs/sysfs/file.c:145
 kernfs_fop_write_iter+0x3e0/0x5f0 fs/kernfs/file.c:345
 new_sync_write fs/read_write.c:595 [inline]
 vfs_write+0x6ac/0x1050 fs/read_write.c:687
 ksys_write+0x12a/0x250 fs/read_write.c:739
 do_syscall_x64 arch/x86/entry/syscall_64.c:63 [inline]
 do_syscall_64+0x115/0x870 arch/x86/entry/syscall_64.c:94
 entry_SYSCALL_64_after_hwframe+0x77/0x7f
RIP: 0033:0x7f143eb9e019
Code: ff c3 66 2e 0f 1f 84 00 00 00 00 00 0f 1f 44 00 00 48 89 f8 48 89 f7 48 89 d6 48 89 ca 4d 89 c2 4d 89 c8 4c 8b 4c 24 08 0f 05 <48> 3d 01 f0 ff ff 73 01 c3 48 c7 c1 e8 ff ff ff f7 d8 64 89 01 48
RSP: 002b:00007ffc13e63168 EFLAGS: 00000246 ORIG_RAX: 0000000000000001
RAX: ffffffffffffffda RBX: 00007f143ee25fa0 RCX: 00007f143eb9e019
RDX: 000000000000000f RSI: 0000200000000300 RDI: 0000000000000003
RBP: 00007f143ec3500c R08: 0000000000000000 R09: 0000000000000000
R10: 0000000000000000 R11: 0000000000000246 R12: 0000000000000000
R13: 00007f143ee25fac R14: 00007f143ee25fa0 R15: 00007f143ee25fa0
 </TASK>
Modules linked in:
---[ end trace 0000000000000000 ]---
RIP: 0010:regmap_get_i2c_bus+0xbe/0xc60 drivers/base/regmap/regmap-i2c.c:360
Code: 89 c6 e8 f5 8b a3 fb 45 85 e4 0f 85 84 01 00 00 e8 77 91 a3 fb 4c 8d 73 1c 48 b8 00 00 00 00 00 fc ff df 4c 89 f2 48 c1 ea 03 <0f> b6 14 02 4c 89 f0 83 e0 07 83 c0 03 38 d0 7c 08 84 d2 0f 85 a2
RSP: 0018:ffffc900042ef568 EFLAGS: 00010207
RAX: dffffc0000000000 RBX: 0000000000000000 RCX: ffffffff8666d35b
RDX: 0000000000000003 RSI: ffffffff8666d369 RDI: ffff88802be1a540
RBP: ffff8880552ba000 R08: 0000000000000005 R09: 0000000000000000
R10: 0000000000000000 R11: 0000000000000000 R12: 0000000000000000
R13: ffff8880552ba018 R14: 000000000000001c R15: ffff8880552ba000
FS:  000055558b984500(0000) GS:ffff8880d5dd8000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 0000001b33263fff CR3: 000000004714c000 CR4: 0000000000352ef0
----------------
Code disassembly (best guess):
   0:	89 c6                	mov    %eax,%esi
   2:	e8 f5 8b a3 fb       	call   0xfba38bfc
   7:	45 85 e4             	test   %r12d,%r12d
   a:	0f 85 84 01 00 00    	jne    0x194
  10:	e8 77 91 a3 fb       	call   0xfba3918c
  15:	4c 8d 73 1c          	lea    0x1c(%rbx),%r14
  19:	48 b8 00 00 00 00 00 	movabs $0xdffffc0000000000,%rax
  20:	fc ff df
  23:	4c 89 f2             	mov    %r14,%rdx
  26:	48 c1 ea 03          	shr    $0x3,%rdx
* 2a:	0f b6 14 02          	movzbl (%rdx,%rax,1),%edx <-- trapping instruction
  2e:	4c 89 f0             	mov    %r14,%rax
  31:	83 e0 07             	and    $0x7,%eax
  34:	83 c0 03             	add    $0x3,%eax
  37:	38 d0                	cmp    %dl,%al
  39:	7c 08                	jl     0x43
  3b:	84 d2                	test   %dl,%dl
  3d:	0f                   	.byte 0xf
  3e:	85                   	.byte 0x85
  3f:	a2                   	.byte 0xa2
```
