---
title: BUG: unable to handle kernel paging request in netdev_unregister_kobject (2)
subsystems: kernel,kernel,pm,pm,kernel
extid: be6bbcdae3e70335dfa2
link: https://syzkaller.appspot.com/bug?extid=be6bbcdae3e70335dfa2
source: syzbot-dashboard
---

# BUG: unable to handle kernel paging request in netdev_unregister_kobject (2)

来源：[https://syzkaller.appspot.com/bug?extid=be6bbcdae3e70335dfa2](https://syzkaller.appspot.com/bug?extid=be6bbcdae3e70335dfa2)

## 崩溃报告

```
Unable to handle kernel paging request at virtual address dfff80000000000b
KASAN: null-ptr-deref in range [0x0000000000000058-0x000000000000005f]
Mem abort info:
  ESR = 0x0000000096000005
  EC = 0x25: DABT (current EL), IL = 32 bits
  SET = 0, FnV = 0
  EA = 0, S1PTW = 0
  FSC = 0x05: level 1 translation fault
Data abort info:
  ISV = 0, ISS = 0x00000005, ISS2 = 0x00000000
  CM = 0, WnR = 0, TnD = 0, TagAccess = 0
  GCS = 0, Overlay = 0, DirtyBit = 0
[dfff80000000000b] address between user and kernel address ranges
Internal error: Oops: 0000000096000005 [#1]  SMP
Modules linked in:
CPU: 1 UID: 0 PID: 9966 Comm: kbnepd �7v��K�� Tainted: G             L      syzkaller #0 PREEMPT 
Tainted: [L]=SOFTLOCKUP
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 08/14/2026
pstate: 83400005 (Nzcv daif +PAN -UAO +TCO +DIT -SSBS BTYPE=--)
pc : klist_put+0x50/0x11c lib/klist.c:212
lr : klist_put+0x2c/0x11c lib/klist.c:210
sp : ffff800093c87800
x29: ffff800093c87800 x28: 1fffe0001ad891c2 x27: ffff0000d6c48008
x26: 1fffe0001ad89005 x25: dfff800000000000 x24: 1fffe0001e76558c
x23: dfff800000000000 x22: ffff0000d6c48800 x21: 0000000000000001
x20: 0000000000000000 x19: ffff0000f3b2ac60 x18: 00000000ffffffff
x17: ffff800084de6844 x16: ffff80008252a5b0 x15: ffff80008255c804
x14: ffff800080f3cfd4 x13: 0000000000000001 x12: 0000000000000000
x11: 0000000000000000 x10: ffff60001b266d69 x9 : 0000000000000000
x8 : 000000000000000b x7 : 0000000000000000 x6 : ffff800080bb9bb0
x5 : ffff000106b04710 x4 : 0000000000000008 x3 : ffff800080f2cf0c
x2 : 0000000000000001 x1 : ffff0000d7cb1d80 x0 : 0000000000000000
Call trace:
 klist_put+0x50/0x11c lib/klist.c:212 (P)
 klist_del+0x24/0x34 lib/klist.c:230
 device_del+0x188/0x71c drivers/base/core.c:3942
 netdev_unregister_kobject+0x2a8/0x39c net/core/net-sysfs.c:2308
 unregister_netdevice_many_notify+0x123c/0x1760 net/core/dev.c:12551
 unregister_netdevice_many net/core/dev.c:12589 [inline]
 unregister_netdevice_queue+0x274/0x30c net/core/dev.c:12390
 unregister_netdevice include/linux/netdevice.h:3487 [inline]
 unregister_netdev+0x2c/0x70 net/core/dev.c:12697
 bnep_session+0x21b8/0x239c net/bluetooth/bnep/core.c:544
 kthread+0x304/0x3d4 kernel/kthread.c:436
 ret_from_fork+0x10/0x20 arch/arm64/kernel/entry.S:838
Code: f9400268 927ff914 91016288 d343fd08 (38776908) 
---[ end trace 0000000000000000 ]---
----------------
Code disassembly (best guess):
   0:	f9400268 	ldr	x8, [x19]
   4:	927ff914 	and	x20, x8, #0xfffffffffffffffe
   8:	91016288 	add	x8, x20, #0x58
   c:	d343fd08 	lsr	x8, x8, #3
* 10:	38776908 	ldrb	w8, [x8, x23] <-- trapping instruction
```
