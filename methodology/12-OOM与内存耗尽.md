# 12 OOM 与内存耗尽

> 内存问题的另一半。01 覆盖的是「写坏内存」（越界/UAF/double-free/未初始化），本文件覆盖「用光内存」——OOM、内存压力、水位线、cgroup 限制。
> 本文转录自 spec §4「崩溃细分」+ §5「知识源与优先级」，是内存子系统「耗尽/压力」分支的展开。

**核心原则（先记住）**：OOM 的现场是**受害者**——被 `OOM killer` 杀掉的那个进程往往无辜，真正的凶手是「谁在疯狂申请内存 / 内存被谁占着不放」。所以先回答两个问题：**内存总量去哪了**（`/proc/meminfo` 分项），**谁在申请**（OOM 报告 + tracepoint）。别一上来就改 `overcommit_memory`，那是治标。

## 工具一：读 OOM killer 报告 —— 谁被杀了、谁在申请

**识别什么症状**：dmesg 出现 `Out of memory: Killed process ...`，或某进程莫名消失、`oom-kill` 事件；或系统卡死（内存耗尽 + 无 swap 时）。

**关键命令**：

```bash
# 找 OOM 记录
journalctl -k | grep -i "out of memory"
dmesg | grep -i "oom\|killed process"
# 触发时的完整报告（谁在申请、各进程 rss 排行、内存水位）
```

**怎么读输出**：OOM 报告分几段，按顺序读：

1. `Out of memory: Killed process 1234 (foo) total-vm:... anon-rss:... file-rss:...` —— 被杀进程及其内存占用（`anon-rss`=匿名页、`file-rss`=文件映射页）。
2. 紧跟的 `Memory cgroup out of memory` 或 `Killed process ... (foo)` 下是**各进程 rss 从高到低的排行**（`Tasks state (memory values in pages):` 段）—— 排前面的就是内存大户，通常真正的「申请者」在此。
3. 若带 `Mem-Info:` 段，给出触发瞬间的 `DMA/DMA32/Normal` 各 zone 的 `free/active/file/slab` 等水位快照。

> 出处：OOM 报告格式见 `Documentation/admin-guide/sysctl/vm.rst`（`oom_dump_tasks` / `oom_kill_allocating_task` 等开关）；进程内存字段见 `Documentation/filesystems/proc.rst`（`/proc/<pid>/status` 的 VmRSS/VmSize）

## 工具二：`/proc/meminfo` —— 内存总量去哪了

**识别什么症状**：想知道「内存都被什么占了」——是 page cache、slab、匿名页还是 shmem。

**关键命令**：

```bash
cat /proc/meminfo
free -h          # 快速总览（buff/cache 会被计入 used，注意看 available）
```

**怎么读输出**（关键字段）：

| 字段 | 含义 | 判断 |
|------|------|------|
| `MemTotal` / `MemFree` | 总量 / 空闲 | 基线 |
| `MemAvailable` | **真正可分配**的内存（估算） | 这是「还够不够用」的正确指标，不是 MemFree |
| `Buffers` / `Cached` | 块设备 / 页缓存 | `Cached` 高 = 内存被 page cache 占，可回收，未必是泄漏 |
| `Slab` / `SUnreclaim` | slab 总量 / 不可回收 slab | **`SUnreclaim` 持续涨 = 内核对象泄漏**（→ 13 kmemleak） |
| `Shmem` | 共享内存（含 tmpfs） | `Shmem` 高 = tmpfs/共享内存占着 |
| `PageTables` / `KernelStack` | 页表 / 内核栈 | 高 = 进程多或每进程占用高 |
| `CommitLimit` / `Committed_AS` | overcommit 上限 / 已承诺 | `Committed_AS > CommitLimit` 且 overcommit 严格时分配失败 |

**判断口径**：`MemAvailable` 趋近 0 才是「真缺内存」；`Cached` 高但 `MemAvailable` 充足 = 只是缓存，不用管；`SUnreclaim` 单调上涨才是危险信号（内核泄漏）。

> 出处：`Documentation/filesystems/proc.rst`（`/proc/meminfo` 逐字段说明）

## 工具三：`/proc/slabinfo` + `/proc/vmstat` —— 谁在增长、回收是否运转

**识别什么症状**：`SUnreclaim` 在涨，想知道是哪个 slab 缓存泄漏；或怀疑内存回收（reclaim）没触发/触发无效。

**关键命令**：

```bash
slabtop -s c              # 按 cache 大小排序，实时看哪个 slab 在涨
cat /proc/slabinfo        # 全量 slab：<name> <active_objs> <num_objs> <objsize> ...
cat /proc/vmstat | grep -E 'pgalloc|pgfree|pgsteal|pgscan|oom_kill|allocstall'
cat /proc/zoneinfo        # 各 zone 水位 min/low/high、free、nr_inactive 等
```

**怎么读输出**：

- `slabtop -s c`：`CACHE SIZE` 最大的 slab 项 + `OBJS ACTIVE` 列，若某 slab 的 `num_objs` 持续涨且 `active_objs` 不回落 = 该对象类型在泄漏（对照 kmemleak 报告确认是哪个调用栈）。
- `vmstat`：`oom_kill` 计数=触发过几次 OOM；`pgsteal_*`/`pgscan_*` 比 = 回收效率（scan 高 steal 低 = 回收在空转，页不可回收或 LRU 有问题）；`allocstall` = 直接回收（direct reclaim）被卡住的次数。

> 出处：`Documentation/filesystems/proc.rst`（`/proc/slabinfo`、`/proc/vmstat`、`/proc/zoneinfo`）

## 工具四：水位线与回收 —— 为什么没及时回收

**识别什么症状**：内存没到 `MemTotal` 就 OOM（回收不触发或触发晚了）；或改了 allocator/reclaim 后，某 zone 水位错导致过早/过晚 OOM。

**关键 config / 参数**：

- `/proc/zoneinfo` 里每 zone 的 `min / low / high` 三档水位：低于 `low` 触发后台回收（kswapd），低于 `min` 触发直接回收（direct reclaim）或 OOM。
- `vm.min_free_kbytes`（sysctl）—— 直接影响 `min` 水位；调小会推迟回收但可能碎片化/OOM 更晚，调大保留更多紧急内存。
- `vm.swappiness`（0-100）—— 回收时匿名页 vs 页缓存的偏好；`vm.vfs_cache_pressure`、`vm.dirty_ratio/dirty_background_ratio`。

**怎么读输出**：对比 `zoneinfo` 的 `free` 与 `min`：若 `free` 已低于 `min` 却还没触发回收/OOM，说明回收路径有问题（魔改 reclaim 的常见症状）；若 `min` 被调得过大，内存还没用满就 OOM。

> 出处：`Documentation/admin-guide/sysctl/vm.rst`（min_free_kbytes / swappiness / dirty_*）；水位与回收概念见 `Documentation/admin-guide/mm/concepts.rst`

## 工具五：cgroup 限制 + overcommit —— 是「真缺内存」还是「被限额」

**识别什么症状**：单机物理内存充足，但容器/进程还是 OOM——往往是 cgroup `memory.max` 限额，或 overcommit 策略卡住。

**关键命令**：

```bash
# cgroup v2 内存限额与使用
cat /sys/fs/cgroup/<group>/memory.max     # 上限
cat /sys/fs/cgroup/<group>/memory.current # 当前使用
cat /sys/fs/cgroup/<group>/memory.events  # oom / oom_kill 计数

# overcommit 策略
cat /proc/sys/vm/overcommit_memory   # 0=启发式 1=永远允许 2=严格按 CommitLimit
cat /proc/sys/vm/overcommit_ratio
cat /proc/sys/vm/panic_on_oom        # 1=OOM 直接 panic（抓现场用）
```

**怎么读输出**：`memory.events` 里 `oom` 计数 > 0 说明「在 cgroup 层面被限额 OOM」，而非整机缺内存——去查限额配得对不对，别去改全局内存。`overcommit_memory=2` 时 `Committed_AS > CommitLimit` 会拒绝分配，即使物理内存有空。

> 出处：`Documentation/admin-guide/cgroup-v2.rst`（memory.max/current/events）；`Documentation/admin-guide/sysctl/vm.rst`（overcommit_memory/overcommit_ratio/panic_on_oom）

## 常见根因 + 修复注意

**常见根因**：

- **内核对象泄漏**：`SUnreclaim` 单调上涨，某 slab 增长不回落 → 转 13 kmemleak 拿分配栈。
- **大阶分配失败 / 内存碎片化**：单次要 `order` 过大的连续页，虽总 free 够但无连续块 → 查 `/proc/buddyinfo` 看高阶块是否耗尽；修法是拆大分配、或调 `vm.min_free_kbytes`。
- **cgroup 限额过小**：`memory.events` 有 oom，物理内存却充足。
- **回收不触发/无效**：魔改 reclaim/allocator 后，`pgscan` 高 `pgsteal` 低，或水位配错。
- **页缓存不回收**：`Cached` 高 + `MemAvailable` 低，回收调参（swappiness / vfs_cache_pressure）或确认是否锁了内存（mlock）。
- **shmem/tmpfs 占死**：`Shmem` 高，tmpfs 文件不被回收。

**修复注意**：

1. **先分型再动手**：`MemAvailable` 低 → 真缺内存（查谁在申请）；`SUnreclaim` 涨 → 内核泄漏（kmemleak）；`Cached` 高 → 缓存/回收调参；`memory.events` oom → cgroup 限额。
2. 别急着 `overcommit_memory=1` 掩盖问题——它只是「假装内存够」，真正的申请者还在涨。
3. 需要抓现场时 `vm.panic_on_oom=1` 配合 kdump，OOM 瞬间直接 panic 留 vmcore。

## 出处/引源

- spec §4「崩溃细分」+ §5「知识源与优先级」为本文内容来源。
- 官方文档：
  - `Documentation/admin-guide/sysctl/vm.rst`（overcommit_memory / min_free_kbytes / swappiness / oom_dump_tasks / panic_on_oom）
  - `Documentation/filesystems/proc.rst`（`/proc/meminfo`、`/proc/slabinfo`、`/proc/vmstat`、`/proc/zoneinfo`、`/proc/buddyinfo`、进程 VmRSS/VmSize）
  - `Documentation/admin-guide/cgroup-v2.rst`（memory.max / memory.current / memory.events）
  - `Documentation/admin-guide/mm/concepts.rst`（水位线、回收概念）
- 泄漏下钻交叉引用 `methodology/13-内存泄漏kmemleak.md`。
