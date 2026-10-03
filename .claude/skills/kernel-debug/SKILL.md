---
name: kernel-debug
description: Linux 内核问题定位与根因排查。当用户遇到内核 oops、panic、崩溃、挂死/锁死、死锁、数据竞态、性能回归、构建/API 破坏，或需要科学定位内核根因并正确修复时使用。重点覆盖魔改的 CPU、内存管理子系统。
---

# 内核调试（kernel-debug）

按 `D:\claude-workspace\kernel` 知识库定位 Linux 内核问题根因并正确修复。本 skill 是薄入口，具体方法论都在该仓库里，不要在这里复制方法论正文。

## 启动

1. 读 `D:\claude-workspace\kernel\AGENTS.md` —— 先内化 AI 行为约束（证据门 / 审计轨迹 / 不信任自评分 / 死胡同恢复）。
2. 读 `D:\claude-workspace\kernel\methodology\00-决策树.md` —— 定位主入口，按「第 0 号原则 → 第 0 步（上游/魔改）→ 第 1 步（症状分型）」走。
3. 按分型结果跳到 `methodology/` 下 `01`~`17` 对应的 playbook，照「工具 → 读输出」执行。

## 铁律

- **最小扰动优先**：零扰动（读 oops/源码/git）→ 最小活体观测 → 专抓现行的检测器（KASAN/KCSAN/lockdep）→ printk 排最后。
- **内存类故障现场是受害者**：越界/UAF/double-free 的根因在生命周期历史里，靠工具把「受害者地址」翻译成「凶手地址」，别读代码猜。
- **先判断上游 or 魔改**：决定 git 历史 / 文档可信度；魔改要跨版本跨 arch 溯源。
- **结论必附证据，禁止裸断言**；卡住（同一方向 3~4 次工具调用还没质疑假设）就强制生成 ≥3 个互斥假设逐个证伪、换工具换方向。

## 收尾

- 定位并修复后，按 `kb/_template.md` 记一条经验（`lesson` 必填，不记＝白 debug）。
- 需要正式复盘时用 `kb/_summary-template.md`。
