# 内核调试知识系统（kernel-debug-kb）设计文档

日期：2026-09-30
状态：待评审

---

## 1. 背景与目标

**场景**：对 Linux 内核进行魔改（主要集中在 CPU、内存管理子系统），遇到大量难以定位的问题——不明 oops / 崩溃、跨子系统污染、"加打印问题就消失"的 Heisenbug。接触内核时间不长，对调试方法论和测试/质量手段了解有限。

**两个目标（共享一个知识底座）**：

- **A 定位（reactive）**：出 oops / 崩溃后，系统地把症状追到根因，并正确修复。
- **B 防问题（proactive）**：在魔改后、上生产前，用 sanitizer / 测试 / 模糊测试把内存、竞态类 bug 挡下来。

**核心诉求**：知识库**可增长、不是写死**；跨工具可用；能持续更新。

---

## 2. 环境与约束

| 项 | 现状 | 对设计的影响 |
|----|------|-------------|
| 内核源码 | `D:\interview-file\github` 下有 `linux-v5.10`、`linux-v6.6` 两棵树 + AI 基础设施栈 | 两棵树可用于交叉 diff |
| 分析环境 | Claude Code 跑在 Windows | 只能读源码 + 编排，不能本地跑内核 |
| 执行环境 | 编译/运行/复现在**远程 Linux 服务器**（ssh） | 诊断命令需 ssh，做成薄适配层 |
| 网络 | **公司可能不开放网络** | 知识库改成**离线优先**，外部知识走定时同步 |
| 魔改代码 | git 历史不可靠（message 空、有未提交改动）、代码跨版本/跨 arch 搬 | 需要"溯源"步骤，运行时事实优先 |
| 合规 | 魔改内核是公司资产 | **严禁上传 GitHub**（哪怕是私有仓库） |

---

## 3. 总体架构

交付物是一个**工具无关的 git 仓库**，纯文本 + 脚本，任何 Agent 都能读：

```
kernel-debug-kb/
├── methodology/              ← 方法论（纯 markdown，"怎么查"）
│   ├── 00-决策树.md            上游/魔改分叉 → direct/内存生命周期分叉
│   ├── 01-内存问题排查.md      KASAN/KMSAN/page_owner 打法
│   ├── 02-搜相关patch.md       git log -S / --grep / lore [PATCH]
│   ├── 03-修复清单.md          锁序/屏障/refcount/unwind/跨arch
│   ├── 04-工具选型表.md
│   └── 05-引源与出处.md        每条方法论标注出处
├── kb/                       ← 案例库（纯 markdown，一条一案，"查过什么"）
│   └── mm-2026-09-30-<slug>.md
├── scripts/                  ← shell 脚本（本来就工具无关）
│   ├── build-kasan.sh
│   ├── run-kselftest.sh
│   ├── run-syzkaller.sh
│   ├── git-to-kb-hook.sh
│   └── sync-external.sh
└── AGENTS.md                 ← 薄入口，告诉任何 Agent 怎么用上面这些
```

**组件职责**（对应最初"Agent / Skill / 知识库"的困惑）：

| 组件 | 承载什么 | 怎么用 | 增长节奏 |
|------|---------|--------|---------|
| methodology/ | 程序性知识（怎么查、怎么修） | 调试开始即加载，塑造推理 | 慢（发现新 bug 类别时补清单） |
| kb/ | 陈述性知识（发生过什么、怎么修） | 调试中按需查询 | 快（每次 commit/debug 加一条） |
| scripts/ | 动作（构建/测试/同步） | 直接执行 | 按需 |
| AGENTS.md | 入口 | 让任何工具知道怎么用上面三样 | — |

**可选升级**：把"查 kb / 搜 lore / 搜 patch"包成 **MCP 服务器**，任何支持 MCP 的 Agent（Claude Code / VS Code / Cursor）都能原生调用。第一步先做 markdown + AGENTS.md，零服务；有需要再套 MCP，同一份 markdown 和脚本直接复用。

---

## 4. 方法论（决策树）

### 第 0 号原则：最小扰动优先

按对系统的扰动从低到高选手段，**printk 排最后**：

1. 零扰动：读已有 oops/dmesg/vmcore、读源码、查 git
2. 最小活体观测：单个 tracepoint / kprobe / ftrace 单函数
3. 专抓现行的检测器：KASAN / KCSAN / lockdep（在污染发生点确定性抓现行）
4. 最后才 printk（会改时序、掩盖竞态；且 printk 自身可能死锁，见 CVE-2022-49441）

> 出处：LKML Valdis Kletnieks（lkml.org/lkml/2009/4/28/644）；Paul McKenney perfbook / LPC 2023。补一条技法：**先检测、后 dump**——埋检测逻辑，异常条件已满足才 dump，而非持续 printk。

### 通用定位手段（工具选型工具箱）

这是"有什么可用"的全景；下面的第 0 步 / 第 1 步决策树告诉你"按症状该抓哪一个"。

**1. 内核启动/调试参数**（`内核参数debug` 等）：

| 参数 | 作用 |
|------|------|
| `debug` | 开启内核调试输出 |
| `panic_on_oops=1` / `oops=panic` | oops 直接 panic（配合 kdump 抓现场） |
| `softlockup_panic=1` / `hung_task_panic=1` | 挂死时 panic |
| `nmi_watchdog=1` | NMI 看门狗，抓硬锁死 |
| `earlycon` / `earlyprintk` | 早期启动输出（early boot 崩溃用） |
| `initcall_debug` | 打印每个 initcall 耗时，定位启动挂死 |
| `slub_debug=...` / `page_poison=1` / `slab_nomerge` | 内存调试参数 |
| `no_console_suspend` | 挂起时保留控制台 |
| `nokaslr` | 关 KASLR，便于地址映射 |
| `crashkernel=...` | 预留 kdump 内存 |

**2. 编译期调试选项（Kconfig）**：

| 选项 | 作用 |
|------|------|
| `CONFIG_DEBUG_KERNEL` / `DEBUG_INFO` / `FRAME_POINTER` | 调试信息基础 |
| `CONFIG_KALLSYMS` | oops 里能解析符号名 |
| `CONFIG_DYNAMIC_DEBUG` | 运行时按模块/文件开关 printk（dyndbg） |
| `CONFIG_PROVE_LOCKING`(lockdep) / `DEBUG_ATOMIC_SLEEP` / `DEBUG_SPINLOCK` | 锁正确性 |
| `CONFIG_DEBUG_LIST` / `DEBUG_VM` / `DEBUG_SG` | 数据结构完整性 |
| KASAN / KCSAN / KMSAN / UBSAN / KFENCE / PAGE_OWNER / KMEMLEAK / SLUB_DEBUG | 内存/竞态检测（详见第 1 步） |
| `CONFIG_RCU_CPU_STALL_TIMEOUT` | RCU stall 检测 |

**3. 动态调试（dyndbg）**：开 `CONFIG_DYNAMIC_DEBUG` 后，运行时 `echo 'module foo +p' > /sys/kernel/debug/dynamic_debug/control` 按模块/文件/行开关 printk，不用重编。

**4. 追踪设施**：
- **ftrace**（function / function_graph tracer，配 `trace-cmd`）
- **tracepoints / events**（`/sys/kernel/tracing/events/`）
- **kprobes / kretprobes**（动态插桩任意函数）
- **eBPF / bpftrace**（低开销动态追踪）
- **perf**（`perf record` / `perf probe`）

**5. 事后分析**：
- oops 解码：`scripts/decode_stacktrace.sh`、`scripts/faddr2line`
- `crash vmlinux vmcore`、`drgn`（分析 vmcore）
- `pstore`（重启后保留崩溃日志）
- kdump / kexec

**6. 交互调试**：`kgdb`（gdb over serial）、`kdb`（内核内置调试器）

**7. 静态分析**：Sparse、Smatch、Coccinelle、clang analyzer、`checkpatch.pl`

**8. 挂死检测**：softlockup / hardlockup detector、hung_task、RCU stall、NMI watchdog

**9. SysRq 魔术键**（系统挂死时的保命手段）：`t`(dump 任务)、`w`(dump 阻塞任务)、`m`(内存信息)、`l`(所有 CPU backtrace)

### 第 0 步：上游 or 魔改（决定后面所有动作）

```
这段代码是上游原生，还是魔改过？
├─ 上游原生 → 标准流程
│    · git blame / git log 可信（message 详细）
│    · Documentation 可用
│    · "搜相关 patch" 直接有效
└─ 魔改 → 叠加"特定条件"（只此分支）
     · git 历史当线索、不当真相
     · 溯源：拿特征行当指纹，跨版本+跨arch搜真实出身
     · 跨 arch 内存序检查（x86 强序 vs ARM 弱序，屏障假设是否变）
     · 运行时事实是唯一真相（KASAN/crash/tracepoint）
     · 找清相对哪个 baseline（版本+arch）分叉的
```

### 第 1 步：按症状分型（先定类型，再走分支）

| 症状类型 | 识别信号 | 定位手段 |
|---------|---------|---------|
| 崩溃（oops/panic/BUG/WARN） | oops 栈、panic 日志 | 见下方「崩溃细分」 |
| 挂死/锁死 | softlockup/hardlockup/hung_task/rcu stall 告警 | watchdog + sysrq(`w`/`t`/`l`) + ftrace 找卡点 |
| 死锁 | 进程 D 状态、lockdep 告警 | lockdep（`CONFIG_PROVE_LOCKING`） |
| 数据竞态 | 「加打印就消失」、偶发 | KCSAN |
| 行为错误（不崩但结果错） | 逻辑对不上 | git bisect + KUnit 单测 + 关键状态打印 |
| 性能回归 | 延迟/吞吐劣化 | ftrace / perf / bpftrace |
| 构建/API 破坏 | 编译错、v5.10↔v6.6 行为变 | 两棵树 diff + 上游 API 变更记录 |

**崩溃细分**（你最常遇到的类型，已展开）：

```
oops 现场是凶手还是受害者？
├─ direct 故障（null 解引用/死锁/明显逻辑错）→ 缩到 50 行读代码
└─ 内存生命周期（越界/UAF/double-free/未初始化/流动转化）
     → 立刻上工具，别再读代码猜：
        · 越界/UAF/double-free  → KASAN（报真正的坏访问+凶手栈）
        · 初始化没做干净        → KMSAN
        · 谁分配的/什么状态     → page_owner + mm tracepoints
        · slab 邻居写坏         → slub_debug / SLAB poisoning
```

**关键认知**：内存类故障的 oops 现场是受害者，根因在内存生命周期历史里，代码阅读在原理上找不到，必须靠运行时工具把"受害者地址"翻译回"凶手地址"。

> 分型骨架如上；除「崩溃」已展开外，其余类型的详细打法在实现阶段逐一展开并引源。

### 修复流程（怎么改才算「高效简单正确」）

1. **先搞清不变量**：这段代码/数据结构本该满足什么约束（锁序、refcount、状态机、屏障）
2. **最小改动**：只改根因那一点，别顺手重构
3. **验证**：用 sanitizer / 测试证实「改完真的好了」，不是「看起来好了」
4. **补回归守卫**：每个修复补一个测试或断言（KUnit / kselftest / `WARN_ON`），让它无法无声复发 ← 保证质量的核心
5. **自查**：走一遍下面的清单 + `checkpatch.pl` + coding-style

### 修复清单（逐条过）

1. 修的是根因还是症状？（跨子系统污染要修源头）
2. 引入新竞态了吗？锁序会不会 ABBA 死锁？
3. 内存屏障够不够？
4. 错误路径有没有正确 unwind（goto out 释放锁/内存）？
5. `atomic_t` 该不该换 `refcount_t`？RCU 读者侧有没有睡眠？
6. v5.10 和 v6.6 是否都要回填？差异在哪？
7. 跨 arch 搬代码：内存序假设是否随架构变化？

---

## 5. 知识源与优先级

**patch 中心，不是文档中心**（魔改树文档滞后、不覆盖改动）。

| 优先级 | 源 | 说明 |
|--------|----|----|
| 1（最高） | 运行时客观事实 | KASAN 报告、crash dump、tracepoint 数据；无出身歧义 |
| 2 | 当下代码本身 | 唯一确定在跑的；但"为什么"不在代码里 |
| 3 | git / provenance（当线索） | 上游可信；魔改不可靠 |
| 4（最低） | Documentation | 过时、不覆盖魔改，可能误导 |

**引源白名单**：内核 `Documentation/`（dev-tools、trace）+ Bootlin 调试培训 + McKenney perfbook/LPC 演讲 + LKML/lore + syzbot 报告。方法论每条标出处，不引源不写。

**方法论骨架锚定内核官方文档**：`Documentation/dev-tools/testing-overview.rst`（官方「找 bug / 测内核」总索引）+ `Documentation/process/`（coding-style、submitting-patches、写 commit message）。以官方文档为脊柱，避免重造轮子、保证「科学」。

---

## 6. 知识库结构与增长机制

### kb/ 条目格式（一条一案）

```markdown
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

<详细过程：怎么定位的、走了哪些弯路（叙述）>
```

**记录分两档（关键区分）**：

- **经验教训（`lesson` 字段）——必填**：每条案例的「教训」必须写进 kb，这是 debug 流程不可跳过的最后一步；不记 = 白 debug。
- **定位及解决总结文档——可选**：需要正式复盘、分享、给他人看时才生成。因为 kb 条目已含全部事实，总结文档只是把结构化字段 + 详细过程渲染成叙述，几乎零额外成本（可脚本化生成到 `reports/`）。

### 三个增长触发源

1. **git-commit 驱动（主，纯离线）**：post-commit 钩子自动提取 commit message + diff，生成 kb 候选条目。喂两个来源——(a) 自己魔改树的 commit；(b) 上游 v5.10/v6.6 的 commit（seed 已知 bug 模式）。
2. **每次 debug 会话收尾**：方法论最后一步强制"记录一条"，症状→根因→修复→验证→出处。
3. **外部同步（定时）**：见下节 GitHub 聚合。

### 外部知识同步（解决封闭网络）

内网可能不开放网络，改成**离线优先 + 定时同步**：

- **第一层（纯本地，零网络）**：源码树、树内文档、git 历史、kb 笔记——占调试知识大头。
- **第二层（定时同步）**：建一个 GitHub 仓库 + Actions cron，每天从开源源拉增量：
  - **syzbot 报告**（bug 标题 + reproducer + fix commit + 子系统标签）——小、结构化、最值钱
  - **精选 LKML 线程**（lore 搜索 API，按子系统/关键词筛，非全量）
  - **多个内核版本树**（用于交叉溯源）
  - 内网侧 `git pull` 这个仓库即可。
- "实时"在封闭网络里退化为"定时同步"是物理限制；**自己的数据**（git commit、kb、debug 记录）是真·实时。

---

## 7. 防问题工作流（B）：保证代码质量

**运行时检测**（远程跑，先手动、成熟后上 CI）：

- `build-kasan.sh`：带 KASAN/KCSAN/lockdep 重编魔改内核
- `run-kselftest.sh`：跑相关子系统自测
- `run-syzkaller.sh`：QEMU 里跑 syzkaller 模糊测试

**静态质量门**（每次提交前 / CI）：

- `checkpatch.pl`（风格 + 常见错误）
- Sparse / Smatch / Coccinelle（静态分析，抓锁/API 误用）
- clang analyzer + 编译 `-Werror`、warning 清零

**新代码/新功能**：写 KUnit 单测覆盖不变量

**回归纪律（质量的核心）**：每次修 bug 补一个测试或 `WARN_ON` 断言，让它无法无声复发

升级路径：远程 CI 持续跑以上全部 + 结果回写 kb

对接点：syzbot 已有成熟工作流（Discover→Report→Triage→Debug→Fix），公开报告可直接作为 B 的种子来源。

---

## 8. AI 行为约束（防偷懒 / 监测 / 死胡同恢复）

一层"元方法"，约束执行调试的 AI（不管哪个工具）怎么干活，独立于具体调试技法。**核心原则：靠结构门，不靠施压话术**（话术对正确性提升不可靠，可靠的是强制证据、强制替代假设、强制验证）。

### 8.1 防偷懒：证据门（Evidence Gate）

- 每个"根因"结论必须附可验证证据：KASAN 报告、崩溃栈、git commit、测试输出——**禁止裸断言**
- 每个"已修复"声明必须附验证输出（sanitizer 干净 / 测试通过），否则视为未完成
- 每步必须产出具体产物（解码后的栈、grep 命中、diff），不是"我看了下大致是 X"
- 必须先穷尽零扰动手段，才允许升级到重编/插桩（防"懒得查就猜"）

### 8.2 监测：独立检查清单 + 审计轨迹

- 一份**固定完成清单**，在 AI 回答之后、独立于它自己运行：
  - 有没有附证据？有没有引源？有没有排除替代假设？有没有跑验证？
- **审计轨迹**：AI 记录每个假设 + 证据 + 当前走到决策树哪一步，人（或复审 agent）能看出它跳没跳步
- **不信任自评分（progress mirage）**：进展必须以真实测试 / sanitizer 输出为准，不能用"我改对了"这种自我评估当证据；实证里 AI 自评进步有 56% 实际无变化甚至倒退
- 可选：一个复审 agent 二次检查主 agent 结论（对应 code-review 模式）

### 8.3 死胡同恢复：显式重启信号（有研究依据）

**卡住的可观测信号**（Epistemic Lock-in 研究）：
- 信息视野缩小：反复重读同一批文件（写读比 > 3:1 却不发散）
- 失败解释同质化：每次失败都用同一个假设解释，从不回头质疑假设本身
- 停止生成新假设
- **阈值：朝同一方向连续 3–4 次工具调用还没质疑自己的假设，就该强制干预**

**触发后结构化重启（ToT 式多假设 + 换路）**：
1. **强制多假设**：一次性生成 ≥3 个互斥候选根因（不要只从一个换到另一个），逐个用客观证据证伪
2. 换工具（读代码 → 运行时插桩）
3. 换方向（竞态 → 内存污染；direct → 内存生命周期）
4. 回决策树第 0 步，明确问"我做了什么可能错的假设？"

**关键依据**：靠模型自己"反思"常是把错方向**合理化**而非纠正（progress mirage）。「死胡同」的判断必须基于客观信号（真实测试 / KASAN / 复审），而非 AI 自己的信心。决策树本身要有回边：某分支不收敛就上浮一级走兄弟分支。

### 8.4 出处与关联

- superpowers：`systematic-debugging`（先根因后修复、不猜）、`verification-before-completion`（证据先于结论）、`test-driven-development`（先测试后修复）
- 研究：**Reflexion**（arXiv:2303.11366，失败转具体可执行反思 + 客观验证器）、**Tree of Thoughts**（多路径 + 显式回溯）、**Epistemic Lock-in**（openreview.net/pdf?id=hMptycsA60）、**progress mirage / loop engineering**（自评分不可信）
- 这条元方法同样工具无关，写进 AGENTS.md 让任何 Agent 都遵守。

## 9. 工具接入

- **Claude Code**：读 `AGENTS.md`（或几行 Skill shim 指向 `methodology/`）
- **VS Code / Copilot / Cursor**：读 `AGENTS.md`（跨工具约定）
- **其他 Agent**：能读文件 + 跑 bash 即可，零依赖
- **远程执行薄适配层**：Skill/方法论只写"意图 + 标准命令"（如 `dmesg -T`、`scripts/decode_stacktrace.sh`），连接方式留给用户一个 `kr "<命令>"` 占位符——背后是 `ssh -J 跳板机`、`kubectl exec`、还是合规受控通道，用户自己定义一次。

---

## 10. 合规红线

- **魔改内核源码严禁上传 GitHub**（哪怕私有仓库）。
- GitHub 仓库只放公开的开源知识聚合（syzbot、公开 LKML、公开文档）。
- 含敏感信息的 kb 笔记留在内网。

---

## 11. 实现时决定的事项（问或试，非前置阻塞）

这些不用现在拍板，实现到对应步骤时「问用户」或「先试一种」即可：

1. **网络 / GitHub 通道**：默认按「离线优先」先做核心（源码 / git / kb 本就零网络），能跑起来再说；确认有通道后再补第二层同步，没有就不做。
2. **子系统优先级**：默认从内存管理开始（你的主要痛点），想换随时说。
3. **仓库落点**：实现到「搭仓库」那一步时直接问你，不写死。
