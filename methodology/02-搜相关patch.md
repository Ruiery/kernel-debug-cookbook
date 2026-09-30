# 02 搜相关 patch

> 上游 patch 是"已解过一遍"的同类问题：优先查上游历史，而不是从零推。spec §5：patch 中心，不是文档中心。
> 本文转录自 spec §5「知识源与优先级」。

## git log -S —— 按代码内容搜（增删了某字符串的提交）

**适用场景**：想知道某个函数名 / 变量 / 字符串是哪个提交引入或删除的，尤其排查"某个行为是何时变的"。

**示例**：
```bash
git log -S 'spin_unlock_wait' --oneline -- mm/
git log -S 'page_owner=on' --oneline
```

## git log --grep —— 按 commit message 搜

**适用场景**：按提交说明里的关键词（如 `fix`、`use-after-free`、`refcount`、某子系统名）找相关修复提交。

**示例**：
```bash
git log --grep='use-after-free' --oneline -- mm/
git log --grep='refcount' --oneline -- kernel/
```

## git blame -L —— 定位某几行是谁写的

**适用场景**：看到可疑代码，想知道最后改动者/提交，作为"溯源"起点（上游树 blame 可信；魔改树 blame 只当线索）。

**示例**：
```bash
git blame -L 120,160 mm/page_alloc.c
```

## git log -L —— 跟踪某函数/某段代码的演变历史

**适用场景**：追一个函数从诞生到现在的每次改动，看清不变量是什么时候被打破的。

**示例**：
```bash
git log -L :__alloc_pages_nodemask:mm/page_alloc.c
```

## 两棵树 diff（v5.10..v6.6）

**适用场景**：代码跨版本搬（本仓库有 v5.10 与 v6.6 两棵树），看某段代码在两个版本间的差异，判断行为/API 变化是否引入回归。

**示例**：
```bash
git diff v5.10..v6.6 -- mm/slub.c
git log v5.10..v6.6 --oneline -- mm/
```

## lore 上搜 [PATCH] 线程

**适用场景**：上游还没合、或想找公开讨论与复现，按函数名/子系统在 lore 邮件列表搜 patch 线程。

**做法**：用 lore 搜索，按函数名（如 `kmem_cache_alloc`）或子系统（如 `mm`、`locking`）搜 `[PATCH]`，找到对应线程与 message-id；syzbot 报告标题同样可搜。

> 提示：`methodology/02` 的检索结果应作为"证据"挂到结论上（对应 AI 行为约束的「证据门」）。

## 出处/引源

- spec §5「知识源与优先级」（patch 中心原则 + git/provenance 优先级）为本文唯一内容来源。
- lore / LKML：https://lore.kernel.org/
- syzbot 报告：https://syzkaller.appspot.com/
- git 命令文档：`git help log`、`git help blame`、`git help diff`。
