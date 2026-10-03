# kernel-debug-cookbook

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
| `scripts/` | **动作**（shell 脚本）：构建 KASAN、跑 kselftest、跑 syzkaller、git-to-kb 钩子、校验（validate） | 直接执行 |

增长节奏：`methodology/` 慢（发现新 bug 类别时补清单），`kb/` 快（每次 commit/debug 加一条），`scripts/` 按需。

## 安装（Claude Code skill）

别人安装，一条命令：把仓库 clone 到 skills 目录。

```bash
git clone git@github.com:Ruiery/kernel-debug-cookbook.git ~/.claude/skills/kernel-debug
```

装好后，在任何目录：

- 敲 `/kernel-debug`，或
- 直接说「这个 oops 怎么定位」（description 匹配自动触发）。

更新：`cd ~/.claude/skills/kernel-debug && git pull`。

> 原理：仓库根目录的 `SKILL.md` 就是 skill 入口，`methodology/`、`kb/`、`scripts/` 都在同一目录、全相对路径，所以 clone 到任何路径（任何盘、任何机器）都能用，零配置、零硬编码。

## 怎么使用（人）

**A 定位（出 oops / 崩溃后追根因）**

1. 读 `methodology/00-决策树.md`：先定症状类型，判断「上游原生还是魔改」。
2. 按症状跳到对应 playbook（`01`~`17`），照「工具 → 读输出」执行。
3. 定位根因 → 最小改动 → 按 `03-修复清单与流程.md` 逐条自查 → 用 sanitizer / 测试验证。
4. 按 `kb/_template.md` 记一条（`lesson` 必填，不记＝白 debug）。

**B 防问题（改完代码、上生产前）**

```bash
export KERNEL_TREE=/path/to/linux    # 你的内核源码树（远程 Linux）
bash scripts/build-kasan.sh          # 编 KASAN/KCSAN/lockdep 内核
bash scripts/run-kselftest.sh        # 跑 kselftest
bash scripts/run-syzkaller.sh        # 跑 syzkaller fuzz（需先配好 QEMU 镜像）
```

**外部数据**

- LKML patch：CI 每日自动同步，本地 `git pull` 取最新。
- syzbot 仪表盘全量（需代理，本地手动）：

```bash
python3 scripts/sync-syzbot-dashboard.py --subsystems mm,block,kernel,cgroups --proxy http://127.0.0.1:7890
```

**自动记经验（可选）**：把 `scripts/git-to-kb-hook.sh` 挂成 `post-commit`，每次 commit 生成 kb 候选条目。

## 与任何 Agent 配合

本仓库**工具无关**——不绑定 Claude Code、Cursor、VS Code 或任何特定 Agent。任何能「读文件 + 跑 bash」的 Agent 都能直接使用：

1. 读仓库根目录的 **`AGENTS.md`**（统一入口），即知道上面三样东西怎么配合。
2. 按需读 `methodology/` 里的决策树与清单，按需查 `kb/` 里的历史案例。
3. 需要动作时直接跑 `scripts/` 下的 shell 脚本。

可选升级：把「查 kb / 搜 lore / 搜 patch」包成 MCP 服务器，任何支持 MCP 的 Agent 都能原生调用；同一份 markdown 和脚本直接复用，第一步零服务即可跑起来。

## 合规

**kb/ 案例条目（可能含内网敏感信息）已 gitignore、不进 GitHub；仓库只共享方法论、脚本和模板。如需本地版本化案例，另建私有仓库。**
