---
title: [PATCH 0/5] allow dma-buf-io ctx reuse across files
list: linux-block
message_id: cover.1793751001.git.asml.silence@gmail.com
link: https://lore.kernel.org/linux-block/cover.1793751001.git.asml.silence@gmail.com/
---

# [PATCH 0/5] allow dma-buf-io ctx reuse across files

来源：[https://lore.kernel.org/linux-block/cover.1793751001.git.asml.silence@gmail.com/](https://lore.kernel.org/linux-block/cover.1793751001.git.asml.silence@gmail.com/)

```
Currently, dma-buf maps can only be used by the file they were
registered with. This means that we can't open a new file, even if it
comes from the same subsystem and point to the same block device and
use it with an old dma-buf registration. That would be too restrictive
for upcoming filsystem support, so lift it now and allow reusing
contexts between files pointing to the same NVMe, even if they refer
to different partitions.

To do that, we add a tag representing for each file, save it from
the file passed during registration and use it to reject files
which tags don't match it. Tags are set by subsystems creating
files, should be unique and represent the instance of the
subsystem.

Pavel Begunkov (5):
  dma-buf-io: add tags for sharing ctx b/w files
  block: set dma-buf-io tag to block files
  io_uring: add data to dma-buf convertion helpers
  io_uring/dma-buf: switch to tag file filtering
  io_uring/dma-buf: get rid of struct io_buf_dma

 block/fops.c                 |  1 +
 drivers/dma-buf/dma-buf-io.c |  3 +++
 include/linux/dma-buf-io.h   | 22 ++++++++++++++++++++++
 include/linux/fs.h           |  6 ++++++
 io_uring/dma-buf.c           | 19 +++++--------------
 io_uring/dma-buf.h           | 24 ++++++++++++++----------
 6 files changed, 51 insertions(+), 24 deletions(-)

-- 
2.54.0
```
