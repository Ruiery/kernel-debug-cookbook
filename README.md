# kernel-debug-kb

工具无关的 Linux 内核调试知识库。纯 markdown 方法论 + shell 脚本，任何 AI Agent 都能读、能用、能持续更新。

## 这个仓库解决什么

对 Linux 内核魔改（主要集中在 CPU、内存管理子系统）时，会碰到大量难以定位的问题：不明 oops / 崩溃、跨子系统污染、"加打印问题就消失"的 Heisenbug。这个知识库服务于两个共享同一底座的场景：

- **A 定位（reactive）**：出 oops / 崩溃后，系统地把症状追到根因，并正确修复。
- **B 防问题（proactive）**：在魔改后、上生产前，用 sanitizer / 测试 / 模糊测试把内存、竞态类 bug 挡下来。

核心诉求：知识库**可增长、不是写死**；跨工具可用；能持续更新。

## 三个目录各是什么

| 目录 | 承载什么 | 怎么用 |
|------|---------|--------|
| `methodology/` | 程序性知识（**怎么查**、怎么修）：决策树、排查打法、修复清单、工具选型表、引源 | 调试开始即加载，塑造推理 |
| `kb/` | 陈述性知识（**查过什么**）：一条一案，症状 → 根因 → 修复 → 验证 → 出处 → 教训 | 调试中按需查询 |
| `scripts/` | **动作**（shell 脚本）：构建 KASAN、跑 kselftest、跑 syzkaller、git-to-kb 钩子、外部同步 | 直接执行 |

增长节奏：`methodology/` 慢（发现新 bug 类别时补清单），`kb/` 快（每次 commit/debug 加一条），`scripts/` 按需。

## 与任何 Agent 配合

本仓库**工具无关**——不绑定 Claude Code、Cursor、VS Code 或任何特定 Agent。任何能「读文件 + 跑 bash」的 Agent 都能直接使用：

1. 读仓库根目录的 **`AGENTS.md`**（统一入口），即知道上面三样东西怎么配合。
2. 按需读 `methodology/` 里的决策树与清单，按需查 `kb/` 里的历史案例。
3. 需要动作时直接跑 `scripts/` 下的 shell 脚本。

可选升级：把「查 kb / 搜 lore / 搜 patch」包成 MCP 服务器，任何支持 MCP 的 Agent 都能原生调用；同一份 markdown 和脚本直接复用，第一步零服务即可跑起来。

## 合规

**本仓库保持无 remote；如需加 remote，先 gitignore kb/ 以保护敏感条目。**
