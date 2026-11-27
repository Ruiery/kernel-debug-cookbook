---
title: [PATCH v6 0/2] f2fs: enable buffered RWF_DONTCACHE
list: linux-block
message_id: cover.1795746008.git.qiwenjie@xiaomi.com
link: https://lore.kernel.org/linux-block/cover.1795746008.git.qiwenjie@xiaomi.com/
---

# [PATCH v6 0/2] f2fs: enable buffered RWF_DONTCACHE

来源：[https://lore.kernel.org/linux-block/cover.1795746008.git.qiwenjie@xiaomi.com/](https://lore.kernel.org/linux-block/cover.1795746008.git.qiwenjie@xiaomi.com/)

```
This series enables buffered RWF_DONTCACHE on F2FS for one-pass streaming
I/O, where retaining the transferred data can displace more useful cache.

Patch 1 marks dropbehind write bios with BIO_COMPLETE_IN_TASK. Normal and
dropbehind folios may share otherwise mergeable IPU and OPU bios; the flag
is set when a dropbehind folio joins a bio. The block layer handles
deferral from unsafe completion contexts.

Patch 2 passes FGP_DONTCACHE to the buffered write folio lookup and
advertises FOP_DONTCACHE, enabling buffered reads and writes. Internal
write_begin callers that pass a NULL kiocb remain supported.

Tests used x86-64 QEMU/KVM with two vCPUs, 2 GiB RAM, and an NVMe-backed
F2FS image. Each attempt transferred a 1-GiB file sequentially in a fresh
guest, with memory.max=255852544 (244 MiB) and memory.swap.max=0. Normal
and dontcache each ran ten counterbalanced rounds. Values below are
arithmetic means of the ten runs per mode. Write throughput excludes the
final fdatasync().

Throughput was:

 Operation  I/O       Normal MiB/s  Dontcache MiB/s  Change
 Read       1 MiB         4137.96          5869.38  +41.84%
 Write      8 KiB          686.09          1752.24 +155.39%
 Write      1 MiB          714.91          2161.02 +202.28%

Average memory.current was:

 Operation  I/O       Normal MiB  Dontcache MiB  Change
 Read       1 MiB         197.26          13.70 -93.06%
 Write      8 KiB         214.22          13.15 -93.86%
 Write      1 MiB         215.20          19.52 -90.93%

Mean reclaim counters per run were:

 Operation  I/O       pgscan normal/DC   pgsteal normal/DC
 Read       1 MiB          200999.7/0          200888.4/0
 Write      8 KiB          201136.8/0          201120.8/0
 Write      1 MiB          200899.3/0          200883.3/0

Scan counts pages examined by reclaim; steal counts pages reclaimed.
memory.current includes all memory charged to the workload, not only
file-cache pages.

Dontcache left zero target pages resident after reads and one 4-KiB page
after write synchronization.

Changes since v5:

- Rebase onto the F2FS dev branch, adapting the bio tagging to the
  sub-folio merge paths and excluding metadata-cache I/O.
- Drop the Android 6.12 backport results, as its dropbehind implementation
  differs substantially from that in the current dev branch.
- Add memory-limited read results and update the write results,
  reporting arithmetic means of ten runs per mode.

Wenjie Qi (2):
  f2fs: complete dropbehind write bios in task context
  f2fs: enable buffered RWF_DONTCACHE

 fs/f2fs/data.c | 10 ++++++++++
 fs/f2fs/file.c |  2 +-
 2 files changed, 11 insertions(+), 1 deletion(-)


base-commit: b61a029304bb5531312ebc133b2a895d14dc3fee
-- 
2.43.0
```
