---
title: [PATCH blktests v4] block/053: add a torn atomic write test for block devices
list: linux-block
message_id: 20261030-blkdev-fixes-tests-v4-1-d8d18808e965@columbia.edu
link: https://lore.kernel.org/linux-block/20261030-blkdev-fixes-tests-v4-1-d8d18808e965@columbia.edu/
---

# [PATCH blktests v4] block/053: add a torn atomic write test for block devices

来源：[https://lore.kernel.org/linux-block/20261030-blkdev-fixes-tests-v4-1-d8d18808e965@columbia.edu/](https://lore.kernel.org/linux-block/20261030-blkdev-fixes-tests-v4-1-d8d18808e965@columbia.edu/)

```
A block device atomic write is a hardware atomic write, submitted as a
single bio, so when its buffer can't be fully pinned, the direct I/O
path has to fail the write rather than submit the pinned part.
Otherwise, it submits what was pinned with REQ_ATOMIC set and leaves
the rest to the buffered fallback, tearing the write at the pin
boundary.

This is a regression test for that issue, fixed by commit 73a0ff6030af
("block: fail a short atomic pin in bio_iov_iter_get_pages()").

Issue a two-page pwritev2() with RWF_ATOMIC to a scsi_debug device with
atomic_wr=1 from a buffer whose last page is PROT_NONE, so that pinning
the buffer stops one page short. Check with statx() that the device
supports an atomic write of that size, then check that the write fails
with EINVAL and that the range still reads back as the old data.

Two pages is the smallest write that leaves one page unpinnable, and
atomic_wr_max_length=256 raises the atomic write unit max to 128K so
that two pages fit for any page size up to 64K.

Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
A regression test for the block device atomic write fix, now upstream
as commit 73a0ff6030af ("block: fail a short atomic pin in
bio_iov_iter_get_pages()") from the fixes series [1]. block/050 to
block/052 from the earlier revisions of this series are merged.

block/053 issues a RWF_ATOMIC write from a buffer whose last page
cannot be pinned to a scsi_debug device with atomic_wr=1 and checks
that the device holds all of the new data or none of it.

[1] https://lore.kernel.org/linux-block/20261009-blkdev-fixes-v6-0-307939c387df@columbia.edu/
---
Changes in v4:
- Rebase on current master, and drop block/050 to block/052, which are
  merged.
- block/053: build the helper only when the kernel headers have the
  atomic write statx fields, checked in src/Makefile like the ublk
  interface, and drop the local copies of struct statx and the atomic
  write defines, per John Garry and Shin'ichiro Kawasaki.
- block/053: exit the helper with EXIT_SUCCESS or EXIT_FAILURE and let
  its messages say what went wrong, instead of separate exit codes for a
  torn write and an unexpected result, per John Garry.
- block/053: rename the helper to atomic-write-untorn, per John Garry.
- block/053: condense the comments in the helper and the test, per John
  Garry.
- block/053: rename the helper functions to
  bdev_can_atomic_write_for_length() and compare_bytes(), fold the
  readback check into compare_bytes(), and drop the informational
  messages, per John Garry.
- block/053: reword the messages for a write that went through and for
  the expected failure, per John Garry.
- block/053: refer to the kernel fix by its commit now that it is
  upstream.
- Link to v3: https://patch.msgid.link/20261015-blkdev-fixes-tests-v3-0-b6ffa6410514@columbia.edu

Changes in v3:
- Rebase on current master, and renumber the tests to block/050 to
  block/053 after the new block/049.
- block/050: release the mapping and the file descriptor on the helper's
  error paths, and the buffer and file descriptor of each writer and
  reader thread when it exits.
- block/050: fail on a write that returns less than its direct part.
- block/052: release the mapping and the file descriptor on the helper's
  error paths.
- block/053: check that the device supports atomic writes with statx()
  instead of reading the atomic write unit max from sysfs, per John
  Garry.
- block/053: always write two pages, and raise the scsi_debug atomic
  write unit max to 128K so that they fit for any page size, instead of
  skipping the test when they do not, per John Garry.
- block/053: check that the atomic write fails with EINVAL, and report a
  write that went through separately from a torn one, per John Garry.
- block/053: read the old contents back before the atomic write, per
  John Garry.
- block/053: reuse the write buffer for the readback, per John Garry.
- block/053: release the file descriptor and the mapping on error paths,
  per John Garry.
- block/053: report a missing scsi_debug module once.
- block/053: specify that it is hardware atomic writes that are
  submitted as a single bio, per John Garry.
- Link to v2: https://patch.msgid.link/20261009-blkdev-fixes-tests-v2-0-fcb3599e47f7@columbia.edu

Changes in v2:
- Rebase on current master.
- New block/052: test that a partially pinned RWF_ATOMIC write is not
  torn, as requested by John Garry.
- Change the kernel patch links to v6 of the series.
- Link to v1: https://patch.msgid.link/20260909-blkdev-fixes-tests-v1-0-1f8af8665d16@columbia.edu
---
 src/.gitignore            |   1 +
 src/Makefile              |   8 +++
 src/atomic-write-untorn.c | 160 ++++++++++++++++++++++++++++++++++++++++++++++
 tests/block/053           |  41 ++++++++++++
 tests/block/053.out       |   2 +
 5 files changed, 212 insertions(+)

diff --git a/src/.gitignore b/src/.gitignore
index d56d0fb..c299ecf 100644
--- a/src/.gitignore
+++ b/src/.gitignore
@@ -1,3 +1,4 @@
+/atomic-write-untorn
 /bio-bounce-read
 /bio-full-trim
 /bio-trim-pin-leak
diff --git a/src/Makefile b/src/Makefile
index da25842..5af0c9f 100644
--- a/src/Makefile
+++ b/src/Makefile
@@ -36,12 +36,14 @@ C_URING_TARGETS := metadata \
 	metadata-iopoll \
 	nvme-passthru-admin-uring
 C_UBLK_TARGETS := miniublk
+C_ATOMIC_WRITE_TARGETS := atomic-write-untorn
 C_THREAD_TARGETS := dio-fallback-race \
 	splice-race
 
 HAVE_LIBURING := $(call HAVE_C_MACRO,liburing.h,IORING_OP_URING_CMD)
 HAVE_UBLK_HEADER := $(call HAVE_C_HEADER,linux/ublk_cmd.h,1)
 HAVE_NEW_UBLK_INTF := $(call HAVE_C_DEF,linux/ublk_cmd.h,UBLK_U_CMD_START_DEV)
+HAVE_STATX_WRITE_ATOMIC := $(call HAVE_C_DEF,linux/stat.h,STATX_ATTR_WRITE_ATOMIC)
 
 CXX_TARGETS := \
 	discontiguous-io
@@ -49,6 +51,12 @@ CXX_TARGETS := \
 SYZKALLER_TARGETS := \
 	sg/syzkaller1
 
+ifeq ($(HAVE_STATX_WRITE_ATOMIC), 1)
+C_TARGETS += $(C_ATOMIC_WRITE_TARGETS)
+else
+$(info Skip $(C_ATOMIC_WRITE_TARGETS) build due to missing kernel header(v6.11+))
+endif
+
 TARGETS := $(C_TARGETS) $(C_THREAD_TARGETS) $(CXX_TARGETS) $(SYZKALLER_TARGETS)
 
 ifeq ($(HAVE_UBLK_HEADER), 1)
diff --git a/src/atomic-write-untorn.c b/src/atomic-write-untorn.c
new file mode 100644
index 0000000..2dfdd9c
--- /dev/null
+++ b/src/atomic-write-untorn.c
@@ -0,0 +1,160 @@
+// SPDX-License-Identifier: GPL-3.0+
+/*
+ * Copyright (C) 2026 Tal Zussman
+ *
+ * Check that a RWF_ATOMIC direct write to a block device is all or nothing
+ * when only part of its buffer can be pinned.
+ *
+ * Fill the first two pages of <blockdev> with one byte value, then write two
+ * pages of another value with RWF_ATOMIC from a buffer whose last page is
+ * PROT_NONE, so that pinning stops one page short. The write has to fail
+ * with EINVAL and leave the old bytes on the device. The device has to
+ * support an atomic write of two pages, which is checked with statx().
+ *
+ * usage: atomic-write-untorn <blockdev>
+ *
+ * exit:  0 = the write failed with EINVAL and the device is unchanged
+ *        1 = it did not, or a setup error
+ */
+#define _GNU_SOURCE
+#include <errno.h>
+#include <fcntl.h>
+#include <stdbool.h>
+#include <stdio.h>
+#include <stdlib.h>
+#include <string.h>
+#include <linux/fs.h>
+#include <sys/mman.h>
+#include <sys/stat.h>
+#include <sys/uio.h>
+#include <unistd.h>
+
+#define OLD	'A'
+#define NEW	'B'
+
+static bool bdev_can_atomic_write_for_length(int fd, size_t len)
+{
+	struct statx stx = { 0 };
+
+	if (statx(fd, "", AT_EMPTY_PATH, STATX_WRITE_ATOMIC, &stx)) {
+		perror("statx");
+		return false;
+	}
+	if (!(stx.stx_mask & STATX_WRITE_ATOMIC) ||
+	    !(stx.stx_attributes & STATX_ATTR_WRITE_ATOMIC)) {
+		fprintf(stderr, "device does not support atomic writes\n");
+		return false;
+	}
+	if (len < stx.stx_atomic_write_unit_min ||
+	    len > stx.stx_atomic_write_unit_max) {
+		fprintf(stderr, "device cannot write %zu bytes atomically\n",
+			len);
+		return false;
+	}
+	return true;
+}
+
+/*
+ * Read the range back past the page cache and return how many of its bytes
+ *
```
