---
name: kernel-debug
description: Use when 遇到 Linux 内核 oops、panic、崩溃、挂死（softlockup/hardlockup/hung_task/rcu stall）、死锁、数据竞态、性能回归、构建/API 破坏，重点在魔改的 CPU、内存管理子系统。
---

# kernel-debug

内核调试知识库的薄入口。方法论本体在本目录 `methodology/`（决策树 + 17 个 playbook），这里只放必须记住的原则和入口，不重复正文。

## 铁律

- **最小扰动优先**：读现场 → 最小活体观测 → 检测器（KASAN/KCSAN/lockdep）→ printk 最后
- **内存故障现场是受害者**：越界/UAF/double-free 的根因在生命周期历史，靠工具翻译「受害者地址 → 凶手地址」，别读代码猜
- **先判断上游 or 魔改**：决定 git 历史/文档可信度，魔改要跨版本跨 arch 溯源
- **结论必附证据，禁止裸断言**；卡住（同一方向 3~4 次没质疑假设）强制 ≥3 个互斥假设逐个证伪

## 用法

1. 读 `AGENTS.md`（AI 行为约束：证据门/审计轨迹/死胡同恢复）
2. 读 `methodology/00-决策树.md`，按「第 0 号原则 → 第 0 步（上游/魔改）→ 第 1 步（症状分型）」走
3. 跳 `methodology/01~17.md` 对应 playbook
4. 查历史案例 / syzbot 报告 / patch：`bash scripts/search-kb.sh <关键词>`
5. 修完按 `kb/_template.md` 记一条（lesson 必填）
