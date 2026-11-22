---
title: [PATCH RFC 0/3] zram: avoid copying spanning LZ4 objects before decompression
list: linux-block
message_id: 20261122-zram-split-decomp-mm-rfc-v1-0-4e69b08c0fed@gmail.com
link: https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-0-4e69b08c0fed@gmail.com/
---

# [PATCH RFC 0/3] zram: avoid copying spanning LZ4 objects before decompression

来源：[https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-0-4e69b08c0fed@gmail.com/](https://lore.kernel.org/linux-block/20261122-zram-split-decomp-mm-rfc-v1-0-4e69b08c0fed@gmail.com/)

```
When a compressed object spans two zsmalloc pages, zram copies it into
a contiguous buffer before decompression. This series lets the LZ4 and
LZ4HC backends decode dictionary-free blocks directly from the two
fragments.

I measured the time to swap in 1 GiB of synthetic data on arm64 with
4 KiB pages. Each page started with pseudorandom data of one of 16
lengths, followed by zeros. On this workload, 32.6% of compressed
reads spanned two pages with LZ4 and 34.4% with LZ4HC.

The table shows median swap-in times over seven pairs. The last two
columns summarize the percentage change within each pair.

  Codec  Workers  Baseline (ms)  Patched (ms)   Median   Range
  LZ4          1        1403.81       1344.45   -4.21%   -4.64% to -1.61%
  LZ4          8         222.57        216.36   -2.73%   -4.19% to -1.97%
  LZ4HC        1        1403.35       1336.99   -4.74%   -5.07% to -2.90%
  LZ4HC        8         222.10        215.77   -3.16%   -4.39% to -1.27%

These timings include both skipping the copy and switching decoders.

I used Codex to help implement this series.
Do you think the swap-in improvement justifies maintaining a second
LZ4 decoder?

Assisted-by: LLM
Signed-off-by: Xueyuan Chen <xueyuan.chen21@gmail.com>
---
Xueyuan Chen (3):
      zram: allow backends to decompress from two input buffers
      lib/lz4: add safe decompression from two input buffers
      zram: use split-input decompression for LZ4 and LZ4HC

 drivers/block/zram/backend_lz4.c   |   1 +
 drivers/block/zram/backend_lz4.h   |  19 +++++
 drivers/block/zram/backend_lz4hc.c |   2 +
 drivers/block/zram/zcomp.c         |  28 +++++++
 drivers/block/zram/zcomp.h         |   8 ++
 include/linux/lz4.h                |  18 ++++
 lib/lz4/lz4_decompress.c           | 163 +++++++++++++++++++++++++++++++++++++
 7 files changed, 239 insertions(+)
---
base-commit: b95f8bb86713c860ce8536d22a988b949b884d5f

--  
Best regards,
Xueyuan
```
