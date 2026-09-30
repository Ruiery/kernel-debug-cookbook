---
title: <一句话症状>
subsystem: mm | sched | locking | ...
kind: UAF | 越界 | 竞态 | 死锁 | 未初始化 | ...
symptom: <oops 签名 / 现象>
root_cause: <真正的根因>
fix: <怎么修的>
verified_by: KASAN | KCSAN | kselftest | ...
provenance: <疑似来源：从 v6.10 commit X 回填 / ARM 改写 x86>
sources: <syzbot id / LKML message-id / 自己的 commit>
lesson: <经验教训：走了什么弯路、下次怎么避免、该被哪个工具提前抓到>  ← 必填
date: 2026-09-30
---

## 详细过程（叙述）
