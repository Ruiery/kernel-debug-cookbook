# 11 构建与 API 破坏

> 决策树第 1 步「构建/API 破坏」分型的展开打法：编译/链接错误、或两个内核版本间（v5.10 ↔ v6.6）行为/接口突然变了的识别、定位与根因。
> 本文转录自 spec §4「按症状分型（构建/API 破坏）」+ §5「知识源与优先级」。

**核心原则（先记住）**：这类问题没有运行时现场，根因藏在**两棵树（两个版本）的差异**里。定位就是「把旧代码依赖的符号/结构/接口，在上游历史里找出它是什么时候、怎么变的」。先用 `git log` 缩小到文件，再用 `-S` pickaxe 精确到改动某符号的那个 commit。

## 工具一：git log 看上游改了什么

**何时用**：代码从 v5.10 搬到 v6.6 后编不过/行为变，先看「这条路径在区间内被谁改过」。

**关键命令**（在两棵树所在的 git 仓库里，v5.10 / v6.6 均是有 tag 的基线）：

```bash
# 列出 v5.10..v6.6 区间内动过 <path> 的所有 commit
git log --oneline v5.10..v6.6 -- <path>
# 只看某目录（如某个子系统）
git log --oneline v5.10..v6.6 -- drivers/foo/
# 带 diff 看具体改动
git log -p v5.10..v6.6 -- <path>
```

**怎么读结果**：按时间倒序的 commit 列表；`--oneline` 先扫 commit message（含 `Fixes:`/重构说明），锁定嫌疑 commit 后 `git show <sha>` 看它改了什么，或进下一步 diff 精确到行。

> 出处：两棵树 git 历史本身（`D:\interview-file\github\linux-v6.6\` 与 `D:\interview-file\github\linux-v5.10\`，均含 `v5.10`/`v6.6` tag）

## 工具二：git diff 两版本精确对比

**何时用**：已锁定具体文件，要逐行看「这文件在两个版本间差了什么」。

**关键命令**：

```bash
# 两个 tag 之间的完整文件 diff
git diff v5.10 v6.6 -- <file>
# 只看函数声明/结构体定义相关行
git diff v5.10 v6.6 -- include/linux/foo.h
```

**怎么读结果**：`-`（v5.10 侧）与 `+`（v6.6 侧）逐行对照；重点找三类变化——**函数签名**（参数个数/类型/返回变）、**结构体字段**（增删/移位/类型变）、**宏/枚举值**（改值或删除）。任何一处旧代码还在用的东西在 `+` 侧消失或变样，就是编译错/行为变的直接来源。

> 出处：两棵树 git 历史本身

## 工具三：git log -S（pickaxe）找 API 改动的 commit

**何时用**：只知道某个「符号/字段名/函数名」，要反查「它是什么时候被引入/删除/改写的」。

**关键命令**：

```bash
# 找出改动过 <符号> 出现次数的 commit（改名/删除/新增都能抓到）
git log --oneline -S "<符号>" -- <path>
# 带 patch，直接看符号是怎么变的
git log -p -S "old_func_name" -- include/linux/foo.h
# 不指定 path，全树搜（慢，但彻底）
git log --oneline -S "struct_member_name"
```

**怎么读结果**：pickaxe 返回「使该字符串出现次数发生变化的每个 commit」——改名场景会看到删掉旧名、加入新名的相邻两个 commit，把新名字记下来即可对照改调用点。

> 出处：两棵树 git 历史本身（`git log -S` 为 git pickaxe 标准用法）

## 工具四：看 include/ 头文件与 config 项变更

**何时用**：编译错报在「某符号未声明 / 某结构体字段不存在 / 某 config 项不认识」，直接查头文件和 Kconfig 的变更。

**关键命令**：

```bash
# 结构体/函数声明源头在 include/，看它变了没有
git log --oneline v5.10..v6.6 -- include/linux/<相关头文件>.h
git diff v5.10 v6.6 -- include/linux/<相关头文件>.h
# config 项改名/删除，查 Kconfig
git log -p -S "CONFIG_FOO" -- drivers/foo/Kconfig
```

**怎么读结果**：结构体字段增删直接对 diff 上的 `struct foo { ... }` 块；config 项改名/删除看 Kconfig 里 `config FOO` 的增删。旧代码里 `CONFIG_FOO` 还挂着而新树已改名，会静默变 `n` 或直接报未知符号。

> 出处：两棵树 git 历史本身；Kconfig 语义见 `Documentation/kbuild/kconfig-language.rst`

## 常见根因 + 修复注意

**常见根因**：

- **内核内部 API 改名/改签名**：函数参数个数/类型/返回值变（如加 `gfp_t`、改返回 `int`），旧调用点编译错或行为变。
- **结构体字段增删**：依赖的字段被删除/改名/移位（`container_of` 偏移假设失效），旧代码访问到错位置。
- **函数从 `EXPORT_SYMBOL` 变 `EXPORT_SYMBOL_GPL`**：外部模块（非 GPL 声明）链接时直接 `Unknown symbol`，license 不匹配。
- **config 项改名/删除**：旧 `.config` 里的 `CONFIG_FOO` 在新树不存在，静默失效或报错。
- **`__init`/`__exit` 段释放（通用 bug，非跨版本 API 变化）**：初始化/清理函数被标记 `__init` 后，`__init` 段在 init 后释放，若在运行时仍被引用则悬空。这是通用 bug，只是版本升级时（调用路径/时序变化）更容易暴露，不属于两版本间的接口差异。

**修复注意**：

1. **回填要同时适配两棵树**：若你的代码要在 v5.10 和 v6.6 都跑，改动得做 `#if LINUX_VERSION_CODE` 或两套兼容路径，不能只按新树写。
2. **注意 stable backport 的差异**：某 API 在 v6.6 主线的改法，回填到 v5.10 stable 分支时可能已被 backport 了部分（或没 backport），先查 `git log v5.10..v6.6 -- <path>` 确认改动在不在，别假设「主线怎么改 stable 就怎么改」。
3. **别盲改签名**：确认旧调用点全量后统一改，避免「改一半、新旧签名混用」。

> 出处：`Documentation/process/submitting-patches.rst`（backport / `Fixes:` / stable）；`Documentation/process/stable-kernel-rules.rst`（stable backport 规则）

## 出处/引源

- spec §4「按症状分型（构建/API 破坏）」+ §5「知识源与优先级」为本文内容来源。
- 两棵树 git 历史本身（`D:\interview-file\github\linux-v6.6\` 与 `D:\interview-file\github\linux-v5.10\`，均含 `v5.10`/`v6.6` tag）：`git log` / `git diff` / `git log -S`（pickaxe）。
- 官方文档：
  - `Documentation/process/changes.rst`（编译环境/工具链最低版本要求）
  - `Documentation/process/submitting-patches.rst`（`Fixes:` 标签、backport、`Cc: stable`）
  - `Documentation/process/stable-kernel-rules.rst`（stable backport 规则）
  - `Documentation/process/deprecated.rst`（被弃用的接口/特性，改名/移除的清单入口）
  - `Documentation/core-api/symbol-namespaces.rst`（`EXPORT_SYMBOL` / `EXPORT_SYMBOL_GPL` / `EXPORT_SYMBOL_NS`）
  - `Documentation/process/license-rules.rst`（`EXPORT_SYMBOL_GPL` 的 license 约束）
  - `include/linux/init.h`（`__init`/`__exit` 宏）；`scripts/Makefile.extrawarn`（`-Werror=implicit-function-declaration`，隐式声明即编译错）
  - `Documentation/kbuild/kconfig-language.rst`（Kconfig 项语义）
