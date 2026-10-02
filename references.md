# 外部参考资料清单

静态参考（不天天变，作为方法论「引源」的延伸）。周期性同步的活数据源（LKML patch）由 `scripts/sync-external.py` 处理，不在此列。

## 内核官方文档（在本地源码树内）

- `Documentation/dev-tools/` — sanitizer / 检测器总索引（kasan / kcsan / kmsan / kmemleak / kfence / kunit / kselftest / sparse / smatch / coccinelle / gdb-kernel-debugging / kgdb / ubsan / testing-overview）
- `Documentation/trace/` — ftrace / kprobes / tracepoints / osnoise / timerlat / hwlat
- `Documentation/admin-guide/` — kernel-parameters / oops-tracing / sysrq / lockup-watchdogs / dynamic-debug-howto / ramoops / pstore
- `Documentation/locking/` — lockdep-design / lockstat / ww-mutex-design
- `Documentation/RCU/` — stallwarn / checklist / rcu_dereference
- `Documentation/process/` — coding-style / submitting-patches / stable-kernel-rules

## 培训与书籍

- Bootlin 内核调试培训（slides / 视频）— https://bootlin.com/doc/training/
- Paul McKenney《Is Parallel Programming Hard, And, If So, What Can You Do About It?》（perfbook）— https://kernel.org/pub/linux/kernel/people/paulmck/perfbook/
- Paul McKenney「Debug still hides heisenbug」LPC 2023 演讲

## 性能与追踪方法论

- Brendan Gregg：perf 工具、火焰图、USE 方法
  - 火焰图：https://github.com/brendangregg/FlameGraph
  - 博客：https://www.brendangregg.com/
- bpftrace（独立工具，基于内核 tracepoint/kprobe）：https://github.com/bpftrace/bpftrace

## 期刊 / 深度文章

- LWN（Linux Weekly News，内核子系统深度文章）：https://lwn.net/

## 研究论文（AI 行为约束的依据，见 methodology/05-引源与出处.md）

- Reflexion: Language Agents with Verbal Reinforcement Learning — arXiv:2303.11366
- Tree of Thoughts — Yao et al. 2023
- Epistemic Lock-in（EpiLoop）— https://openreview.net/pdf?id=hMptycsA60
- progress mirage / loop engineering — https://zenodo.org/records/21672574

## 数据源（活数据）

- lore.kernel.org（public-inbox，git 协议）— LKML patch + 子系统列表里的 [syzbot] 邮件；由 `scripts/sync-external.py` 每日同步（CI，免代理）
- syzbot dashboard（syzkaller.appspot.com）— 结构化全量 bug 报告；由 `scripts/sync-syzbot-dashboard.py` 按子系统抓取（本地 + 代理，跑不了 CI）
