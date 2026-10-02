---
title: INFO: rcu detected stall in sendfile64
subsystems: mm,mm,net,fs,mm,lsm,mm,fs
extid: 8b65a69dedebce19fd11
link: https://syzkaller.appspot.com/bug?extid=8b65a69dedebce19fd11
source: syzbot-dashboard
---

# INFO: rcu detected stall in sendfile64

来源：[https://syzkaller.appspot.com/bug?extid=8b65a69dedebce19fd11](https://syzkaller.appspot.com/bug?extid=8b65a69dedebce19fd11)

## 崩溃报告

```
rcu: INFO: rcu_preempt detected stalls on CPUs/tasks:
rcu: 	Tasks blocked on level-0 rcu_node (CPUs 0-1): P5900/1:b..l
rcu: 	(detected by 0, t=10503 jiffies, g=391357, q=541076 ncpus=2)
task:syz.2.9749      state:R  running task     stack:23704 pid:5900  tgid:5899  ppid:918    task_flags:0x400140 flags:0x00080002
Call Trace:
 <TASK>
 context_switch kernel/sched/core.c:5526 [inline]
 __schedule+0x17db/0x58f0 kernel/sched/core.c:7276
 preempt_schedule_irq+0x4b/0x90 kernel/sched/core.c:7598
 irqentry_exit_to_kernel_mode include/linux/irq-entry-common.h:539 [inline]
 irqentry_exit+0x14f/0x910 kernel/entry/common.c:167
 asm_sysvec_apic_timer_interrupt+0x1a/0x20 arch/x86/include/asm/idtentry.h:674
RIP: 0010:lock_release+0x2e1/0x3c0 kernel/locking/lockdep.c:5968
Code: 8b f1 11 00 00 00 00 eb b5 e8 db 4b 41 0a f7 c3 00 02 00 00 74 b9 65 48 8b 05 33 47 f1 11 48 3b 44 24 28 75 48 fb 48 83 c4 30 <5b> 41 5c 41 5d 41 5e 41 5f 5d e9 50 50 44 0a cc 48 8d 3d 68 02 da
RSP: 0018:ffffc90004b7ec28 EFLAGS: 00000286
RAX: a5509ec7935bc000 RBX: 0000000000000206 RCX: 0000000000000046
RDX: ffffc90004b7ed01 RSI: ffffffff8e6fd6d4 RDI: ffffffff8c6d9480
RBP: ffff8880311b8c00 R08: ffffc90004b7f7a0 R09: 0000000000000000
R10: ffffc90004b7ed58 R11: fffff5200096fdad R12: 0000000000000002
R13: 0000000000000002 R14: ffffffff8ed5c760 R15: ffff8880311b8000
 rcu_lock_release include/linux/rcupdate.h:319 [inline]
 rcu_read_unlock include/linux/rcupdate.h:880 [inline]
 class_rcu_destructor include/linux/rcupdate.h:1216 [inline]
 unwind_next_frame+0x1baa/0x2550 arch/x86/kernel/unwind_orc.c:709
 arch_stack_walk+0x11b/0x150 arch/x86/kernel/stacktrace.c:25
 stack_trace_save+0xa9/0x100 kernel/stacktrace.c:122
 save_stack+0x122/0x230 mm/page_owner.c:183
 __reset_page_owner+0x71/0x1f0 mm/page_owner.c:338
 reset_page_owner include/linux/page_owner.h:26 [inline]
 __free_pages_prepare mm/page_alloc.c:1418 [inline]
 __free_frozen_pages+0xc93/0xd90 mm/page_alloc.c:2962
 __slab_free+0x274/0x2c0 mm/slub.c:5815
 qlink_free mm/kasan/quarantine.c:163 [inline]
 qlist_free_all+0x99/0x100 mm/kasan/quarantine.c:179
 kasan_quarantine_reduce+0x148/0x160 mm/kasan/quarantine.c:286
 __kasan_slab_alloc+0x22/0x80 mm/kasan/common.c:350
 kasan_slab_alloc include/linux/kasan.h:253 [inline]
 slab_post_alloc_hook mm/slub.c:4683 [inline]
 slab_alloc_node mm/slub.c:4996 [inline]
 kmem_cache_alloc_noprof+0x2b9/0x600 mm/slub.c:5010
 alloc_buffer_head+0x2a/0x280 fs/buffer.c:2872
 folio_alloc_buffers+0x1a4/0x630 fs/buffer.c:743
 create_empty_buffers+0x3a/0x520 fs/buffer.c:1576
 __block_write_begin_int+0x3b6/0x1900 fs/buffer.c:2011
 iomap_write_begin+0x107a/0x1540 fs/iomap/buffered-io.c:1104
 iomap_write_iter fs/iomap/buffered-io.c:1232 [inline]
 iomap_file_buffered_write+0x470/0xb90 fs/iomap/buffered-io.c:1313
 blkdev_buffered_write block/fops.c:712 [inline]
 blkdev_write_iter+0x50d/0x700 block/fops.c:778
 iter_file_splice_write+0xa31/0x1240 fs/splice.c:736
 do_splice_from fs/splice.c:936 [inline]
 direct_splice_actor+0x101/0x160 fs/splice.c:1159
 splice_direct_to_actor+0x57b/0xcb0 fs/splice.c:1103
 do_splice_direct_actor fs/splice.c:1202 [inline]
 do_splice_direct+0x195/0x290 fs/splice.c:1228
 do_sendfile+0x52e/0x7c0 fs/read_write.c:1371
 __do_sys_sendfile64 fs/read_write.c:1432 [inline]
 __se_sys_sendfile64+0x144/0x1a0 fs/read_write.c:1418
 do_syscall_x64 arch/x86/entry/syscall_64.c:61 [inline]
 do_syscall_64+0x166/0x520 arch/x86/entry/syscall_64.c:84
 entry_SYSCALL_64_after_hwframe+0x77/0x7f
RIP: 0033:0x7f0fc9b9e159
RSP: 002b:00007f0fcab50028 EFLAGS: 00000246 ORIG_RAX: 0000000000000028
RAX: ffffffffffffffda RBX: 00007f0fc9e25fa0 RCX: 00007f0fc9b9e159
RDX: 0000000000000000 RSI: 0000000000000006 RDI: 0000000000000006
RBP: 00007f0fc9c3503b R08: 0000000000000000 R09: 0000000000000000
R10: 0000000020000005 R11: 0000000000000246 R12: 0000000000000000
R13: 00007f0fc9e26038 R14: 00007f0fc9e25fa0 R15: 00007f0fc9f4fa48
 </TASK>
rcu: rcu_preempt kthread starved for 277 jiffies! g391357 f0x0 RCU_GP_WAIT_FQS(5) ->state=R ->cpu=1
rcu: 	Unless rcu_preempt kthread gets sufficient CPU time, OOM is now expected behavior.
rcu: RCU grace-period kthread stack dump:
task:rcu_preempt     state:R  running task     stack:27656 pid:17    tgid:17    ppid:2      task_flags:0x208040 flags:0x00080000
Call Trace:
 <TASK>
 context_switch kernel/sched/core.c:5526 [inline]
 __schedule+0x17db/0x58f0 kernel/sched/core.c:7276
 __schedule_loop kernel/sched/core.c:7353 [inline]
 schedule+0x164/0x2b0 kernel/sched/core.c:7368
 schedule_timeout+0x152/0x2c0 kernel/time/sleep_timeout.c:99
 rcu_gp_fqs_loop+0x30c/0x11f0 kernel/rcu/tree.c:2122
 rcu_gp_kthread+0x9e/0x2b0 kernel/rcu/tree.c:2330
 kthread+0x38b/0x480 kernel/kthread.c:436
 ret_from_fork+0x514/0xb70 arch/x86/kernel/process.c:158
 ret_from_fork_asm+0x1a/0x30 arch/x86/entry/entry_64.S:245
 </TASK>
rcu: Stack dump where RCU GP kthread last ran:
Sending NMI from CPU 0 to CPUs 1:
NMI backtrace for cpu 1
CPU: 1 UID: 0 PID: 5602 Comm: syz-executor Tainted: G             L      syzkaller #0 PREEMPT(full) 
Tainted: [L]=SOFTLOCKUP
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 07/24/2026
RIP: 0010:__lock_acquire+0x362/0x2de0 kernel/locking/lockdep.c:5223
Code: c7 c2 00 e0 ff ff 49 23 54 c5 20 48 09 ca 49 89 54 c5 20 4d 89 44 c5 08 48 8b 54 24 18 49 89 54 c5 10 48 8b 94 24 20 01 00 00 <49> 89 54 c5 18 65 8b 15 de b4 f1 11 31 f6 85 d2 40 0f 95 c6 31 d2
RSP: 0018:ffffc90000a17cb8 EFLAGS: 00000002
RAX: 0000000000000014 RBX: 0000000000000000 RCX: 0000000000000007
RDX: 0000000000000000 RSI: 0000000000000007 RDI: 00000000028f6702
RBP: 0000000000000000 R08: ffffffff8177f1df R09: 0000000000000000
R10: ffffc90000a17f98 R11: ffffffff81b28090 R12: 0000000000000000
R13: ffff888034f96970 R14: 0000000000000004 R15: ffff888034f95dc0
FS:  000055558649d540(0000) GS:ffff888124dd6000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 00007f9570cf3190 CR3: 0000000074456000 CR4: 00000000003526f0
DR0: 0000000000000000 DR1: 0000000000000000 DR2: 0000000063235cd5
DR3: 0000000000000000 DR6: 00000000ffff0ff0 DR7: 0000000000000400
Call Trace:
 <IRQ>
 lock_acquire+0x115/0x350 kernel/locking/lockdep.c:5942
 rcu_lock_acquire include/linux/rcupdate.h:309 [inline]
 rcu_read_lock include/linux/rcupdate.h:849 [inline]
 class_rcu_constructor include/linux/rcupdate.h:1216 [inline]
 unwind_next_frame+0xac/0x2550 arch/x86/kernel/unwind_orc.c:495
 arch_stack_walk+0x11b/0x150 arch/x86/kernel/stacktrace.c:25
 stack_trace_save+0xa9/0x100 kernel/stacktrace.c:122
 kasan_save_stack mm/kasan/common.c:57 [inline]
 kasan_save_track+0x3e/0x80 mm/kasan/common.c:78
 kasan_save_free_info+0x40/0x50 mm/kasan/generic.c:584
 poison_slab_object mm/kasan/common.c:253 [inline]
 __kasan_slab_free+0x5c/0x80 mm/kasan/common.c:285
 kasan_slab_free include/linux/kasan.h:235 [inline]
 slab_free_hook mm/slub.c:2748 [inline]
 slab_free mm/slub.c:6499 [inline]
 kfree+0x1c5/0x650 mm/slub.c:6792
 skb_kfree_head net/core/skbuff.c:1083 [inline]
 skb_free_head net/core/skbuff.c:1095 [inline]
 skb_release_data+0x85e/0xab0 net/core/skbuff.c:1122
 skb_release_all net/core/skbuff.c:1197 [inline]
 __kfree_skb+0x5d/0x210 net/core/skbuff.c:1211
 nft_synproxy_eval_v4+0x36a/0x4e0 net/netfilter/nft_synproxy.c:-1
 nft_synproxy_do_eval+0x335/0x550 net/netfilter/nft_synproxy.c:141
 expr_call_ops_eval net/netfilter/nf_tables_core.c:237 [inline]
 nft_do_chain+0x48d/0x1b10 net/netfilter/nf_tables_core.c:285
 nft_do_chain_inet+0x360/0x4b0 net/netfilter/nft_chain_filter.c:162
 nf_hook_entry_hookfn include/linux/netfilter.h:165 [inline]
 nf_hook_slow+0xc5/0x220 net/netfilter/core.c:619
 nf_hook include/linux/netfilter.h:280 [inline]
 NF_HOOK+0x21f/0x3c0 include/linux/netfilter.h:323
 NF_HOOK+0x336/0x3c0 include/linux/netfilter.h:325
 __netif_receive_skb_one_core net/core/dev.c:6264 [inline]
 __netif_receive_skb net/core/dev.c:6377 [inline]
 process_backlog+0xa6b/0x18b0 net/core/dev.c:6728
 __napi_poll+0xaa/0x330 net/core/dev.c:7787
 napi_poll net/
```
