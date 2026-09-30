# 13 内存泄漏（kmemleak）

> 「该释放的没释放」这类故障的定位打法。与 01 的 KASAN 互补：KASAN 抓「访问了不该访问的」（损坏），kmemleak 抓「该释放没释放」（泄漏）。
> 本文转录自 spec §4「崩溃细分」+ §5「知识源与优先级」。

**核心原则（先记住）**：泄漏不崩、不挂，但内存**单调上涨**、长跑才暴露。现场（`SUnreclaim` 持续涨、最终 OOM）同样是「结果」，根因是「某个对象被分配后，释放路径漏了」。kmemleak 的价值：它直接报出**「unreferenced object」+ 分配它的调用栈**，把「内存去哪了」翻译回「谁分配了没还」。

## 工具一：kmemleak 基本用法 —— 扫描并报告未释放对象

**识别什么症状**：系统长期运行内存持续上涨（`free` 的 `used` 单调增、`SUnreclaim` 涨），但重启后回落——典型的泄漏；怀疑内核模块/驱动/魔改代码漏 `kfree`/漏 refcount。

**关键 config / 参数**：

- `CONFIG_DEBUG_KMEMLEAK=y`（依赖 `CONFIG_DEBUG_FS`）。
- 启动参数 `kmemleak=on`（启动即开，默认关）；`kmemleak=off` 关。
- 运行时开关（debugfs 挂载后，`/sys/kernel/debug/kmemleak`）。

**关键命令**：

```bash
mount -t debugfs none /sys/kernel/debug   # 若未挂载
echo scan > /sys/kernel/debug/kmemleak     # 手动触发一次扫描
echo clear > /sys/kernel/debug/kmemleak    # 清空旧结果（排除启动期已存在的对象）
cat /sys/kernel/debug/kmemleak             # 读报告
```

**怎么读输出**：每条泄漏形如：

```
unreferenced object 0xffff8880... (size 64):
  comm "myproc", pid 1234, jiffies 4294...
  backtrace:
    [<ffffffff...>] my_alloc_func+0x1a/0x50
    [<ffffffff...>] my_call_site+0x...
```

- `unreferenced object 0x... (size N)` —— 一块 N 字节的对象已无人引用（泄漏）。
- `comm "..." pid ...` —— 分配它的进程。
- `backtrace:` —— **分配栈**，这就是「谁分配了但没释放」。把栈顶的 `my_alloc_func` 对照代码，找到它对应的释放路径是否漏了。

> 出处：`Documentation/dev-tools/kmemleak.rst`

## 工具二：区分「真泄漏」还是「误报 / 有意不释放」

**识别什么症状**：报告里某些对象其实是**有意缓存**（如全局 cache、一次性分配），不是泄漏，需要排除。

**怎么读输出**：

- **排除一次性/全局对象**：先 `echo clear` 清空，跑完一轮业务后再 `scan`，只在「稳定运行后仍持续新增」的对象里找真泄漏。
- **对照 `SUnreclaim` 走势**：`cat /proc/meminfo | grep SUnreclaim` 多测几次，确认它在涨、且与 kmemleak 新增对象量吻合。
- **`comm/pid` 异常**：若 `pid` 是 0 或 `comm` 是内核线程名，说明是内核态分配（initcall/工作队列），去内核代码找。

> 出处：`Documentation/dev-tools/kmemleak.rst`（scan/clear 语义、误报排除）；`Documentation/filesystems/proc.rst`（SUnreclaim）

## 工具三：refcount 泄漏（比 kfree 更隐蔽）

**识别什么症状**：对象被 `kref`/`refcount_t`/`atomic_t` 引用计数管理，漏了 `put`（没配对 `get`），对象永不释放——这类 kmemleak 也能抓，但根因是「引用计数不配对」，要单独看。

**关键手段**：

- kmemleak 报告同样给出分配栈；把分配栈里「拿引用（get）」的地方找出来，逐个核对是否有对应「放引用（put）」。
- 辅助：`refcount_t` 的 `CONFIG_REFCOUNT_FULL` 会在计数异常（溢出/下溢）时 `WARN`，抓「多 put 或少 put」。

**怎么读输出**：若泄漏对象大小固定、栈指向同一个「get 型」函数，且 `refcount_t` 有 warning，多半是**引用计数泄漏**而非单纯漏 `kfree`——修「get/put 配对」而不是加 `kfree`。

> 出处：`Documentation/core-api/refcount-vs-atomic.rst`（refcount_t 语义）；`lib/Kconfig.debug`（CONFIG_REFCOUNT_FULL）

## 常见根因 + 修复注意

**常见根因**：

- **错误路径漏 `kfree`**：`goto out` 链上某分支没释放已分配的内存（对应修复清单第 4 条「错误路径 unwind」）。
- **漏配对 refcount put**：`get` 了没 `put`，对象永不销毁。
- **循环引用**：两个对象互相持有对方引用（如链表/缓存节点），谁都不释放。
- **生命周期延长但未相应改释放**：魔改里把对象从「短生命周期」改成「长生命周期」，但释放时机没跟着改。
- **一次性 vs 长期缓存误判**：把「有意缓存」当泄漏修，越修越乱。

**修复注意**：

1. **先 `clear` 再 `scan`**，只对「稳定运行后持续新增」的对象下结论，排除启动期一次性对象。
2. 拿到分配栈后，**沿栈找到对应的释放路径**，确认「该路径是否存在、是否每个分支都覆盖」——漏释放通常出在错误路径（`goto out` 链）。
3. 补回归守卫：修复后长跑压测，用 `SUnreclaim` 走势 + kmemleak 报告确认不再涨。

## 出处/引源

- spec §4「崩溃细分」+ §5「知识源与优先级」为本文内容来源。
- 官方文档：
  - `Documentation/dev-tools/kmemleak.rst`（scan/clear、报告格式、误报排除）
  - `Documentation/filesystems/proc.rst`（`/proc/meminfo` SUnreclaim / `/proc/slabinfo`）
  - `Documentation/core-api/refcount-vs-atomic.rst`（refcount_t 泄漏判断）
  - `lib/Kconfig.debug`（CONFIG_REFCOUNT_FULL）
- 内存「去哪了」的总览交叉引用 `methodology/12-OOM与内存耗尽.md`；损坏型（越界/UAF）交叉引用 `methodology/01-内存问题排查.md`。
