---
title: INFO: rcu detected stall in sys_socket (10)
subsystems: mm,fs,net,mm,cgroups,mm,kernel,mm,kasan,mm,mm
extid: de8e83db70e8beedd556
link: https://syzkaller.appspot.com/bug?extid=de8e83db70e8beedd556
source: syzbot-dashboard
---

# INFO: rcu detected stall in sys_socket (10)

来源：[https://syzkaller.appspot.com/bug?extid=de8e83db70e8beedd556](https://syzkaller.appspot.com/bug?extid=de8e83db70e8beedd556)

## 崩溃报告

```
ICMPv6: NA: aa:aa:aa:aa:aa:1c advertised our address fe80::1c on veth1_to_bridge!
ICMPv6: NA: aa:aa:aa:aa:aa:1c advertised our address fe80::1c on veth1_to_bridge!
rcu: INFO: rcu_preempt detected stalls on CPUs/tasks:
rcu: 	Tasks blocked on level-0 rcu_node (CPUs 0-1): P5851/1:b..l
rcu: 	(detected by 1, t=10503 jiffies, g=6461, q=2744 ncpus=2)
task:syz-executor415 state:R  running task     stack:19024 pid:5851  tgid:5851  ppid:5849   flags:0x00000002
Call Trace:
 <TASK>
 context_switch kernel/sched/core.c:5328 [inline]
 __schedule+0x184f/0x4c30 kernel/sched/core.c:6690
 preempt_schedule_irq+0xfb/0x1c0 kernel/sched/core.c:7012
 irqentry_exit+0x5e/0x90 kernel/entry/common.c:354
 asm_sysvec_apic_timer_interrupt+0x1a/0x20 arch/x86/include/asm/idtentry.h:702
RIP: 0010:lock_release+0x2d/0xa30 kernel/locking/lockdep.c:5833
Code: fa 55 48 89 e5 41 57 41 56 41 55 41 54 53 48 83 e4 e0 48 81 ec 00 01 00 00 49 89 f5 48 89 7c 24 18 65 48 8b 04 25 28 00 00 00 <48> 89 84 24 e0 00 00 00 49 bf 00 00 00 00 00 fc ff df 48 c7 44 24
RSP: 0018:ffffc90003e378a0 EFLAGS: 00000286
RAX: 7f79f333d4528e00 RBX: 0000000000000001 RCX: ffff888034890000
RDX: 0000000000000000 RSI: ffffffff820b74b7 RDI: ffffffff8e937da0
RBP: ffffc90003e379c8 R08: ffffffff820b7446 R09: 1ffff11003cca858
R10: dffffc0000000000 R11: ffffed1003cca859 R12: 0000000000000001
R13: ffffffff820b74b7 R14: ffff88801e654304 R15: ffff88801e654310
 rcu_lock_release include/linux/rcupdate.h:347 [inline]
 rcu_read_unlock include/linux/rcupdate.h:880 [inline]
 page_ext_put+0xa3/0xc0 mm/page_ext.c:550
 __reset_page_owner+0x2de/0x430 mm/page_owner.c:300
 reset_page_owner include/linux/page_owner.h:25 [inline]
 free_pages_prepare mm/page_alloc.c:1108 [inline]
 free_unref_page+0xcfb/0xf20 mm/page_alloc.c:2638
 discard_slab mm/slub.c:2677 [inline]
 __put_partials+0xeb/0x130 mm/slub.c:3145
 put_cpu_partial+0x17c/0x250 mm/slub.c:3220
 __slab_free+0x2ea/0x3d0 mm/slub.c:4449
 qlink_free mm/kasan/quarantine.c:163 [inline]
 qlist_free_all+0x9a/0x140 mm/kasan/quarantine.c:179
 kasan_quarantine_reduce+0x14f/0x170 mm/kasan/quarantine.c:286
 __kasan_slab_alloc+0x23/0x80 mm/kasan/common.c:329
 kasan_slab_alloc include/linux/kasan.h:247 [inline]
 slab_post_alloc_hook mm/slub.c:4085 [inline]
 slab_alloc_node mm/slub.c:4134 [inline]
 kmem_cache_alloc_noprof+0x135/0x2a0 mm/slub.c:4141
 lsm_inode_alloc security/security.c:756 [inline]
 security_inode_alloc+0x37/0x310 security/security.c:1692
 inode_init_always_gfp+0x988/0xcd0 fs/inode.c:235
 inode_init_always include/linux/fs.h:3088 [inline]
 alloc_inode+0x9f/0x1a0 fs/inode.c:272
 sock_alloc net/socket.c:633 [inline]
 __sock_create+0x123/0x940 net/socket.c:1540
 sock_create net/socket.c:1632 [inline]
 __sys_socket_create net/socket.c:1669 [inline]
 __sys_socket+0x150/0x3c0 net/socket.c:1716
 __do_sys_socket net/socket.c:1730 [inline]
 __se_sys_socket net/socket.c:1728 [inline]
 __x64_sys_socket+0x7a/0x90 net/socket.c:1728
 do_syscall_x64 arch/x86/entry/common.c:52 [inline]
 do_syscall_64+0xf3/0x230 arch/x86/entry/common.c:83
 entry_SYSCALL_64_after_hwframe+0x77/0x7f
RIP: 0033:0x7f3d665ebfd7
RSP: 002b:00007ffd90986748 EFLAGS: 00000206 ORIG_RAX: 0000000000000029
RAX: ffffffffffffffda RBX: 00007ffd90986770 RCX: 00007f3d665ebfd7
RDX: 0000000000000006 RSI: 0000000000000001 RDI: 000000000000000a
RBP: 0000000000000005 R08: 00000000000002d8 R09: 0079746972756365
R10: 00007f3d66665840 R11: 0000000000000206 R12: 00007f3d66661b80
R13: 00007f3d66663d40 R14: 00007ffd90986f50 R15: 0000000000000004
 </TASK>
rcu: rcu_preempt kthread starved for 7308 jiffies! g6461 f0x0 RCU_GP_WAIT_FQS(5) ->state=0x0 ->cpu=0
rcu: 	Unless rcu_preempt kthread gets sufficient CPU time, OOM is now expected behavior.
rcu: RCU grace-period kthread stack dump:
task:rcu_preempt     state:R  running task     stack:26112 pid:17    tgid:17    ppid:2      flags:0x00004000
Call Trace:
 <TASK>
 context_switch kernel/sched/core.c:5328 [inline]
 __schedule+0x184f/0x4c30 kernel/sched/core.c:6690
 __schedule_loop kernel/sched/core.c:6767 [inline]
 schedule+0x14b/0x320 kernel/sched/core.c:6782
 schedule_timeout+0x1be/0x310 kernel/time/timer.c:2615
 rcu_gp_fqs_loop+0x2df/0x1330 kernel/rcu/tree.c:2045
 rcu_gp_kthread+0xa7/0x3b0 kernel/rcu/tree.c:2247
 kthread+0x2f0/0x390 kernel/kthread.c:389
 ret_from_fork+0x4b/0x80 arch/x86/kernel/process.c:147
 ret_from_fork_asm+0x1a/0x30 arch/x86/entry/entry_64.S:244
 </TASK>
rcu: Stack dump where RCU GP kthread last ran:
Sending NMI from CPU 1 to CPUs 0:
NMI backtrace for cpu 0
CPU: 0 UID: 0 PID: 16 Comm: ksoftirqd/0 Not tainted 6.12.0-rc6-syzkaller-00077-g2e1b3cc9d7f7 #0
Hardware name: Google Google Compute Engine/Google Compute Engine, BIOS Google 09/13/2024
RIP: 0010:__lock_acquire+0x13b3/0x2050 kernel/locking/lockdep.c:5206
Code: 0f 84 81 00 00 00 48 ba 00 00 00 00 00 fc ff df 48 8b 44 24 20 0f b6 04 10 84 c0 0f 85 0a 08 00 00 48 8b 44 24 10 f6 40 02 10 <75> 55 48 8b 44 24 60 80 3c 10 00 48 8b 5c 24 08 74 12 48 89 df e8
RSP: 0018:ffffc90000156390 EFLAGS: 00000046
RAX: ffff88801ce8e5a0 RBX: ffffffff93c47190 RCX: 5a6ffc55d9fecf00
RDX: dffffc0000000000 RSI: ffff88801ce8e580 RDI: ffff88801ce8da00
RBP: b9b7830957eccbc7 R08: ffffffff942cd807 R09: 1ffffffff2859b00
R10: dffffc0000000000 R11: fffffbfff2859b01 R12: 0000000000000000
R13: ffff88801ce8e4d8 R14: 0000000000000000 R15: ffff88801ce8e5a0
FS:  0000000000000000(0000) GS:ffff8880b8600000(0000) knlGS:0000000000000000
CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
CR2: 00007ffce4f8dfa0 CR3: 000000002f2f6000 CR4: 00000000003526f0
DR0: 0000000000000000 DR1: 0000000000000000 DR2: 0000000000000000
DR3: 0000000000000000 DR6: 00000000fffe0ff0 DR7: 0000000000000400
Call Trace:
 <NMI>
 </NMI>
 <TASK>
 lock_acquire+0x1ed/0x550 kernel/locking/lockdep.c:5825
 rcu_lock_acquire include/linux/rcupdate.h:337 [inline]
 rcu_read_lock include/linux/rcupdate.h:849 [inline]
 ipv6_chk_mcast_addr+0x4b/0x840 net/ipv6/mcast.c:1022
 ip6_protocol_deliver_rcu+0x89e/0x1580 net/ipv6/ip6_input.c:421
 ip6_input_finish+0x187/0x2d0 net/ipv6/ip6_input.c:481
 NF_HOOK+0x3a4/0x450 include/linux/netfilter.h:314
 ip6_input net/ipv6/ip6_input.c:490 [inline]
 ip6_mc_input+0x9c5/0xc30 net/ipv6/ip6_input.c:584
 ip_sabotage_in+0x203/0x290 net/bridge/br_netfilter_hooks.c:1018
 nf_hook_entry_hookfn include/linux/netfilter.h:154 [inline]
 nf_hook_slow+0xc3/0x220 net/netfilter/core.c:626
 nf_hook include/linux/netfilter.h:269 [inline]
 NF_HOOK+0x29e/0x450 include/linux/netfilter.h:312
 __netif_receive_skb_one_core net/core/dev.c:5670 [inline]
 __netif_receive_skb+0x1ea/0x650 net/core/dev.c:5783
 netif_receive_skb_internal net/core/dev.c:5869 [inline]
 netif_receive_skb+0x1e8/0x890 net/core/dev.c:5928
 NF_HOOK+0x9e/0x400 include/linux/netfilter.h:314
 br_handle_frame_finish+0x18ed/0x1fe0
 br_nf_hook_thresh+0x472/0x590
 br_nf_pre_routing_finish_ipv6+0xaa0/0xdd0
 NF_HOOK include/linux/netfilter.h:314 [inline]
 br_nf_pre_routing_ipv6+0x379/0x770 net/bridge/br_netfilter_ipv6.c:184
 nf_hook_entry_hookfn include/linux/netfilter.h:154 [inline]
 nf_hook_bridge_pre net/bridge/br_input.c:277 [inline]
 br_handle_frame+0x9fd/0x1530 net/bridge/br_input.c:424
 __netif_receive_skb_core+0x13e8/0x4570 net/core/dev.c:5564
 __netif_receive_skb_one_core net/core/dev.c:5668 [inline]
 __netif_receive_skb+0x12f/0x650 net/core/dev.c:5783
 process_backlog+0x662/0x15b0 net/core/dev.c:6115
 __napi_poll+0xcb/0x490 net/core/dev.c:6779
 napi_poll net/core/dev.c:6848 [inline]
 net_rx_action+0x89b/0x1240 net/core/dev.c:6970
 handle_softirqs+0x2c5/0x980 kernel/softirq.c:554
 run_ksoftirqd+0xca/0x130 kernel/softirq.c:927
 smpboot_thread_fn+0x544/0xa30 kernel/smpboot.c:164
 kthread+0x2f0/0x390 kernel/kthread.c:389
 ret_from_fork+0x4b/0x80 arch/x86/kernel/process.c:147
 ret_from_fork_asm+0x1a/0x30 arch/x86/entry/entry_64.S:244
 </TASK>
net_ratelimit: 46676 callbacks suppressed
ICMPv6: NA: aa:aa:aa:aa:aa:0c advertised our address fe80::c on bridge0!
ICMPv6: NA: aa:aa:aa:aa:aa:1c advertised our address fe80::1c on veth1_to_bridge!
bridge0: r
```
