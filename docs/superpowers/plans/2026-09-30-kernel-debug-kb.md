# kernel-debug-kb 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭起一个工具无关的「内核调试知识系统」——methodology（怎么查）+ kb（查过什么）+ scripts（动作），让任何 Agent 能按统一方法论定位根因、正确修复、并沉淀经验教训。

**Architecture:** 纯 markdown + shell 的 git 仓库，任何能读文件 + 跑 bash 的 Agent 都可用。AGENTS.md 是统一入口（含 AI 行为约束）；methodology/ 承载决策树与排查打法；kb/ 承载案例（经验教训必填）；scripts/ 承载 B 工作流与增长钩子。外部同步（GitHub）与 MCP 服务器留到后续计划。

**Tech Stack:** Markdown、Bash（内核脚本运行在远程 Linux）、Git。

**Spec:** `docs/superpowers/specs/2026-09-30-kernel-debug-kb-design.md`（本计划逐条从 spec 展开，执行时两份一起读）

## Global Constraints

- **工具无关**：核心只允许纯 markdown + bash，禁止绑定任何特定 Agent/IDE 格式。
- **引源强制**：methodology/ 里每条方法论必须标出处（官方文档 / LKML / syzbot / 研究论文），不引源不写。
- **合规**：魔改内核源码严禁进本仓库；仓库只放方法论/kb/脚本（均为公开或自研知识）。
- **记录两档**：kb 条目的 `lesson` 字段必填；「定位及解决总结文档」可选、不进本计划。
- **文档语言**：中文。
- **仓库根**：`D:\claude-workspace\kernel`（当前工作目录，git init 于此；位置是默认值，用户可改）。

---

## File Structure

```
D:\claude-workspace\kernel\
├── README.md                  ← 仓库是什么、怎么用
├── AGENTS.md                  ← 统一入口：怎么用 methodology/ + AI 行为约束（spec §8）
├── methodology/
│   ├── 00-决策树.md            ← 第0号原则 + 工具箱 + 上游/魔改 + 症状分型 + 崩溃细分（spec §4）
│   ├── 01-内存问题排查.md      ← KASAN/KMSAN/page_owner/slub_debug 打法（spec §4 崩溃细分展开）
│   ├── 02-搜相关patch.md       ← git log -S/--grep/blame/-L + lore [PATCH]（spec §5）
│   ├── 03-修复清单与流程.md    ← 修复流程5步 + 修复清单7条（spec §4 修复）
│   ├── 04-工具选型表.md        ← 9类通用定位手段（spec §4 工具箱）
│   └── 05-引源与出处.md        ← 引源白名单 + 骨架锚定 + 研究出处（spec §5 + §8.4）
├── kb/
│   └── _template.md           ← 条目模板（含必填 lesson）
├── scripts/
│   ├── validate.sh            ← 结构校验（实现"监测/证据门"）
│   ├── build-kasan.sh         ← 带 sanitizer 重编内核
│   ├── run-kselftest.sh       ← 跑自测
│   ├── run-syzkaller.sh       ← 跑模糊测试
│   └── git-to-kb-hook.sh      ← post-commit 钩子：commit → kb 候选条目
└── docs/                      ← 已有 spec + 本 plan
```

---

## Task 1: 仓库骨架 + README + AGENTS.md

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Run: `git init`、`.gitignore`

**Interfaces:**
- Produces: `AGENTS.md` 的固定结构（§1 这是什么、§2 怎么用 methodology/、§3 AI 行为约束、§4 记录纪律），后续所有任务都依赖它作为入口。

- [ ] **Step 1: 初始化 git 仓库**

```bash
cd /d/claude-workspace/kernel
git init
printf '.superpowers/\n' > .gitignore  # 只忽略 SDD 工作区；kb/ 本地版本化（Ruling 1）
```

- [ ] **Step 2: 写 README.md**

内容：仓库目的（内核调试知识系统）、三个目录各是什么、怎么和 Claude Code / VS Code / Cursor 等 Agent 配合（读 AGENTS.md 即可）。引用 spec §1、§3。

- [ ] **Step 3: 写 AGENTS.md（含 AI 行为约束，spec §8）**

结构必须包含以下四节，内容从 spec 对应节抄录（不要改写含义）：

```
# AGENTS.md
## 这是什么
  工具无关的内核调试知识库。定位根因时先读 methodology/00-决策树.md。
## 怎么用
  1. 先判断问题类型，走 methodology/00 的决策树
  2. 每个结论必须附证据（禁止裸断言）
  3. 每次定位完，按 kb/_template.md 记一条（lesson 必填）
## AI 行为约束（spec §8）
  - 证据门：根因/已修复声明必须附验证证据
  - 不信任自评分（progress mirage）
  - 卡住信号 + 死胡同恢复（同方向3-4次调用未质疑假设即换路，强制≥3个互斥假设）
## 记录纪律（spec §6）
  经验教训必记；总结文档可选
```

- [ ] **Step 4: 验证**

```bash
ls AGENTS.md README.md && git status --short
```

预期：两个文件存在，`.gitignore` 出现，`kb/` 目录待建。

- [ ] **Step 5: Commit**

```bash
git add README.md AGENTS.md .gitignore
git commit -m "chore: 仓库骨架 + AGENTS.md 入口 + AI 行为约束"
```

---

## Task 2: methodology/00-决策树.md（核心）

**Files:**
- Create: `methodology/00-决策树.md`

**Interfaces:**
- Produces: 决策树主文件，是其它 methodology 文件的上游入口；后续 01/02/03/04 都从这里的分支链出去。

- [ ] **Step 1: 写文件，含四部分（内容照抄 spec §4，保持结构）**

```
# 00 决策树
## 第 0 号原则：最小扰动优先（printk 排最后）
  （spec §4 第0号原则原文，含"先检测后 dump"技法 + Kletnieks/McKenney 出处）
## 第 0 步：上游 or 魔改（决定后面所有动作）
  （spec §4 第0步分叉，两条分支）
## 第 1 步：按症状分型（先定类型，再走分支）
  （spec §4 的 7 行分型表，含崩溃细分指引）
## 崩溃细分
  （direct vs 内存生命周期的代码块 + 关键认知）
```

- [ ] **Step 2: 结构验证**

检查：四节标题齐全；第 0 号原则含出处（LKML/McKenney 链接）；分型表含 7 类；崩溃细分指向 `01-内存问题排查.md`。

- [ ] **Step 3: Commit**

```bash
git add methodology/00-决策树.md
git commit -m "docs: 方法论决策树（最小扰动 + 上游/魔改 + 症状分型）"
```

---

## Task 3: methodology/01-内存问题排查.md + 04-工具选型表.md

**Files:**
- Create: `methodology/01-内存问题排查.md`
- Create: `methodology/04-工具选型表.md`

**Interfaces:**
- Consumes: 00-决策树.md 的「崩溃细分」「工具箱」分支
- Produces: 内存故障的 KASAN/KMSAN/page_owner/slub_debug 打法；9 类通用手段表

- [ ] **Step 1: 写 01-内存问题排查.md**

内容（spec §4 崩溃细分展开 + §5 知识源）：越界/UAF/double-free→KASAN、未初始化→KMSAN、谁分配→page_owner + mm tracepoints、邻居写坏→slub_debug。每个工具给出「识别什么症状 + 关键 config + 怎么读输出」，每条带出处（`Documentation/dev-tools/kasan.rst` 等）。

- [ ] **Step 2: 写 04-工具选型表.md**

内容：spec §4「通用定位手段」的 9 类（启动参数 / Kconfig / dyndbg / 追踪 / 事后分析 / 交互 / 静态分析 / 挂死检测 / SysRq），做成表。

- [ ] **Step 3: 结构验证**

两个文件都含「出处/引源」小节；01 的四个工具条目都能在 `Documentation/dev-tools/` 里找到对应文件。

- [ ] **Step 4: Commit**

```bash
git add methodology/01-内存问题排查.md methodology/04-工具选型表.md
git commit -m "docs: 内存排查打法 + 通用工具选型表"
```

---

## Task 4: methodology/02-搜相关patch.md + 03-修复清单与流程.md

**Files:**
- Create: `methodology/02-搜相关patch.md`
- Create: `methodology/03-修复清单与流程.md`

**Interfaces:**
- Consumes: 00-决策树.md 的「修复流程」
- Produces: patch 检索技法；修复流程 5 步 + 修复清单 7 条

- [ ] **Step 1: 写 02-搜相关patch.md**

内容（spec §5）：`git log -S` / `--grep` / `blame -L` / `-L` / 两棵树 `v5.10..v6.6` diff，每条附示例命令与适用场景；lore 上按函数名/子系统搜 `[PATCH]` 线程。

- [ ] **Step 2: 写 03-修复清单与流程.md**

内容（spec §4「修复流程」+「修复清单」）：流程 5 步（搞清不变量→最小改动→验证→补回归守卫→自查），清单 7 条（根因 vs 症状 / ABBA / 屏障 / unwind / refcount / 双树回填 / 跨 arch 内存序）。

- [ ] **Step 3: 结构验证**

两个文件都含「出处」；03 的流程与清单条数 = 5+7，不缺项。

- [ ] **Step 4: Commit**

```bash
git add methodology/02-搜相关patch.md methodology/03-修复清单与流程.md
git commit -m "docs: patch 检索技法 + 修复流程与清单"
```

---

## Task 5: methodology/05-引源与出处.md + kb/_template.md + scripts/validate.sh

**Files:**
- Create: `methodology/05-引源与出处.md`
- Create: `kb/_template.md`
- Create: `scripts/validate.sh`

**Interfaces:**
- Produces: 引源白名单（后续所有 methodology 引用它）；`kb/_template.md` 的 frontmatter 字段名（`title/subsystem/kind/symptom/root_cause/fix/verified_by/provenance/sources/lesson/date`）是 validate.sh 校验的契约；`validate.sh` 输出 0/1。

- [ ] **Step 1: 写 05-引源与出处.md**

内容（spec §5 引源白名单 + §8.4 研究出处）：白名单（内核 Documentation / Bootlin / McKenney / LKML / syzbot）+ 骨架锚定（testing-overview.rst + process/）+ 研究出处（Reflexion / ToT / EpiLock / progress mirage）。

- [ ] **Step 2: 写 kb/_template.md（含必填 lesson）**

frontmatter 字段严格用这些名字（validate.sh 依赖它们）：

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

## 详细过程（叙述）
```

- [ ] **Step 3: 写 scripts/validate.sh（走 TDD）**

先写一个"坏样例"验证脚本能抓错，再写脚本本体：

```bash
#!/usr/bin/env bash
# 校验 kb 条目必填字段 + methodology 引源（实现"监测/证据门"）
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fail=0
for f in "$REPO_ROOT"/kb/*.md; do
  [ -e "$f" ] || continue
  case "$f" in *_template.md) continue;; esac
  for field in title root_cause fix lesson; do
    grep -q "^$field:" "$f" || { echo "缺少字段 $field: $f"; fail=1; }
  done
done
for f in "$REPO_ROOT"/methodology/*.md; do
  [ -e "$f" ] || continue
  grep -qiE "出处|引源|source|参考" "$f" || { echo "缺引源: $f"; fail=1; }
done
[ "$fail" -eq 0 ] && echo "校验通过" || { echo "校验失败"; exit 1; }
```

- [ ] **Step 4: TDD 验证**

```bash
chmod +x scripts/validate.sh
# 造一个缺 lesson 的坏样例，应失败
printf -- '---\ntitle: x\nroot_cause: y\nfix: z\n---\n' > kb/bad-test.md
bash scripts/validate.sh; echo "exit=$?"   # 期望 exit=1 且报"缺少字段 lesson"
rm kb/bad-test.md
bash scripts/validate.sh                    # 期望输出"校验通过"
```

- [ ] **Step 5: Commit**

```bash
git add methodology/05-引源与出处.md kb/_template.md scripts/validate.sh
git commit -m "feat: 引源白名单 + kb 模板 + 结构校验脚本"
```

---

## Task 6: scripts/build-kasan.sh + run-kselftest.sh + run-syzkaller.sh

**Files:**
- Create: `scripts/build-kasan.sh`
- Create: `scripts/run-kselftest.sh`
- Create: `scripts/run-syzkaller.sh`

**Interfaces:**
- Consumes: 环境变量 `KERNEL_TREE`（内核树路径，必填）、`OUT`（构建目录，默认 `build-kasan`）、`JOBS`（默认 `nproc`）
- Produces: 三个脚本，远程 Linux 上可执行；本机只做 `bash -n` 语法校验

- [ ] **Step 1: 写 build-kasan.sh**

```bash
#!/usr/bin/env bash
# 远程 Linux 上：带 KASAN/KCSAN/lockdep 重编魔改内核
set -euo pipefail
KERNEL_TREE="${KERNEL_TREE:?请先 export KERNEL_TREE=/path/to/linux}"
OUT="${OUT:-$KERNEL_TREE/build-kasan}"
JOBS="${JOBS:-$(nproc)}"
cd "$KERNEL_TREE"
make O="$OUT" "${DEFCONFIG:-defconfig}"
./scripts/config --file "$OUT/.config" \
  -e KASAN -e KCSAN -e PROVE_LOCKING \
  -e DEBUG_KERNEL -e DEBUG_INFO -e FRAME_POINTER -e KALLSYMS
make O="$OUT" olddefconfig
make O="$OUT" -j"$JOBS"
echo "构建完成：$OUT/vmlinux"
```

- [ ] **Step 2: 写 run-kselftest.sh**

```bash
#!/usr/bin/env bash
# 远程 Linux 上：跑内核自测
set -euo pipefail
KERNEL_TREE="${KERNEL_TREE:?请先 export KERNEL_TREE=/path/to/linux}"
OUT="${OUT:-$KERNEL_TREE/build-kasan}"
cd "$KERNEL_TREE"
make O="$OUT" -C tools/testing/selftests run_tests
```

- [ ] **Step 3: 写 run-syzkaller.sh（流程骨架，值走环境变量）**

```bash
#!/usr/bin/env bash
# 远程 Linux 上：QEMU 里跑 syzkaller 模糊测试（前置：syzkaller 已编译、有镜像）
set -euo pipefail
SZK_BIN="${SZK_BIN:?请先 export SZK_BIN=/path/to/syz-manager}"
CFG="${CFG:?请先 export CFG=/path/to/syzkaller.cfg}"
"$SZK_BIN" -config "$CFG"
```

- [ ] **Step 4: 语法校验（本机唯一能做且该做的验证）**

```bash
for s in scripts/build-kasan.sh scripts/run-kselftest.sh scripts/run-syzkaller.sh; do
  bash -n "$s" && echo "OK $s"
done
```

真实运行验证需在远程 Linux 内核树上执行（不在本机）。执行时按「先 build-kasan → 再 kselftest → 最后 syzkaller」的顺序。

- [ ] **Step 5: Commit**

```bash
git add scripts/build-kasan.sh scripts/run-kselftest.sh scripts/run-syzkaller.sh
git commit -m "feat: B 工作流脚本（sanitizer 构建 / 自测 / 模糊测试）"
```

---

## Task 7: scripts/git-to-kb-hook.sh

**Files:**
- Create: `scripts/git-to-kb-hook.sh`

**Interfaces:**
- Consumes: `kb/_template.md` 的字段名
- Produces: post-commit 钩子，把最新 commit 提取成 kb 候选条目（`<待定>` 字段留给人工补）

- [ ] **Step 1: 写脚本**

```bash
#!/usr/bin/env bash
# post-commit 钩子：commit → kb 候选条目（增长触发源之一，spec §6）
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
DATE="$(date +%F)"
SUBJECT="$(git log -1 --pretty=%s)"
BODY="$(git log -1 --pretty=%b)"
SLUG="$(printf '%s' "$SUBJECT" | tr ' /' '__' | cut -c1-60)"
OUT="$REPO_ROOT/kb/$DATE-$SLUG.md"
cat > "$OUT" <<EOF
---
title: $SUBJECT
subsystem: <待定>
kind: <待定>
symptom: <从 commit 推断>
root_cause: <从 commit 推断>
fix: $SUBJECT
verified_by: <待定>
provenance: <待定>
sources: $(git rev-parse --short HEAD)
lesson: <必填：这次修 bug 的教训>
date: $DATE
---

$BODY

## 详细过程（补充）
EOF
echo "已生成 kb 候选条目：$OUT（请补 <待定> 字段，尤其 lesson）"
```

- [ ] **Step 2: 语法校验 + 冒烟测试**

```bash
bash -n scripts/git-to-kb-hook.sh
# 冒烟：在临时提交上试跑，确认生成条目后删除
git commit --allow-empty -m "smoke: 测试钩子" 
bash scripts/git-to-kb-hook.sh
ls kb/ | grep smoke   # 期望出现一条
# 清理冒烟产物（保留脚本本身）
rm kb/*smoke*.md && git reset --soft HEAD~1
```

- [ ] **Step 3: 接入说明**

把安装方式写进 README 或钩子注释：`ln -s ../../scripts/git-to-kb-hook.sh .git/hooks/post-commit`（可选，用户自己决定要不要装）。

- [ ] **Step 4: Commit**

```bash
git add scripts/git-to-kb-hook.sh
git commit -m "feat: post-commit 钩子：commit 自动生成 kb 候选条目"
```

---

## 后续计划（本计划不包含，明确 defer）

- **外部同步**：GitHub Actions cron 拉 syzbot 报告 + 精选 LKML patch（spec §6 第二层），等网络/GitHub 通道确认后再做。
- **MCP 服务器**：把「查 kb / 搜 lore / 搜 patch」暴露成跨 Agent 原生工具（spec §3 可选升级）。
- **决策树其余分支展开**：挂死/死锁/性能回归/构建 API 的详细打法（spec §4 标注的实现阶段补齐）。
