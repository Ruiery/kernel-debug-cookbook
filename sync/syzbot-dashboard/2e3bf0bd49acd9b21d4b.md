---
title: BUG: unable to handle kernel paging request in blk_mq_complete_request_remote
subsystems: block
extid: 2e3bf0bd49acd9b21d4b
link: https://syzkaller.appspot.com/bug?extid=2e3bf0bd49acd9b21d4b
source: syzbot-dashboard
---

# BUG: unable to handle kernel paging request in blk_mq_complete_request_remote

来源：[https://syzkaller.appspot.com/bug?extid=2e3bf0bd49acd9b21d4b](https://syzkaller.appspot.com/bug?extid=2e3bf0bd49acd9b21d4b)

## 崩溃报告

```
nvme 0000:00:02.0: enabling device (0200 -> 0202)
nvme nvme0: Disabling device after reset failure: -19
Unable to handle kernel paging request at virtual address dfff800000000031
KASAN: null-ptr-deref in range [0x0000000000000188-0x000000000000018f]
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
[dfff800000000031] address between user and kernel address ranges
Internal error: Oops: 0000000096000005 [#1]  SMP
Modules linked in:
CPU: 0 UID: 0 PID: 14 Comm: kworker/u8:1 Tainted: G             L      syzkaller #0 PREEMPT 
Tainted: [L]=SOFTLOCKUP
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 08/14/2026
Workqueue: nvme-reset-wq nvme_reset_work
pstate: 83400005 (Nzcv daif +PAN -UAO +TCO +DIT -SSBS BTYPE=--)
pc : blk_mq_complete_request_remote+0xc4/0x858 block/blk-mq.c:1297
lr : blk_mq_complete_request_remote+0x88/0x858 block/blk-mq.c:1289
sp : ffff80008ebe7900
x29: ffff80008ebe7980 x28: ffff80008ebe7900 x27: 1fffe0001909aa4c
x26: 0000000000000001 x25: ffff0000c84d526e x24: dfff800000000000
x23: ffff700011d7cf20 x22: 1fffe000191b35e4 x21: ffff0000c8d9af24
x20: 000000000000018e x19: ffff0000c8d9ae00 x18: 00000000ffffffff
x17: 0000000000000003 x16: ffff800088a57000 x15: 0000000000000000
x14: 00000000002dd737 x13: 0000000000000001 x12: 0000000000000003
x11: ffff80008a506e28 x10: ffff8000883de072 x9 : 1fffe000191b35c2
x8 : 0000000000000031 x7 : 0000000000000000 x6 : 0000000000000000
x5 : 0000000000000001 x4 : 0000000000000008 x3 : ffff8000827e072c
x2 : 0000000000000000 x1 : ffff0000c1a23b00 x0 : 0000000000000000
Call trace:
 blk_mq_complete_request_remote+0xc4/0x858 block/blk-mq.c:1297 (P)
 nvme_try_complete_req drivers/nvme/host/nvme.h:838 [inline]
 nvme_handle_cqe drivers/nvme/host/pci.c:1601 [inline]
 nvme_poll_cq+0x544/0xfd8 drivers/nvme/host/pci.c:1632
 nvme_reap_pending_cqes drivers/nvme/host/pci.c:2090 [inline]
 nvme_dev_disable+0x384/0x540 drivers/nvme/host/pci.c:3344
 nvme_reset_work+0x510/0x69c drivers/nvme/host/pci.c:3506
 process_one_work kernel/workqueue.c:3396 [inline]
 process_scheduled_works+0x91c/0x1250 kernel/workqueue.c:3479
 worker_thread+0x798/0xbd0 kernel/workqueue.c:3560
 kthread+0x304/0x3d4 kernel/kthread.c:436
 ret_from_fork+0x10/0x20 arch/arm64/kernel/entry.S:854
Code: 97d03a43 f9400288 91063914 d343fe88 (38f86908) 
---[ end trace 0000000000000000 ]---
----------------
Code disassembly (best guess):
   0:	97d03a43 	bl	0xffffffffff40e90c
   4:	f9400288 	ldr	x8, [x20]
   8:	91063914 	add	x20, x8, #0x18e
   c:	d343fe88 	lsr	x8, x20, #3
* 10:	38f86908 	ldrsb	w8, [x8, x24] <-- trapping instruction
```
