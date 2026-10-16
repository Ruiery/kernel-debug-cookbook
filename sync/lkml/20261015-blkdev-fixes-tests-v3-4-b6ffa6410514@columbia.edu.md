---
title: [PATCH blktests v3 4/4] block/053: add a torn atomic write test for block devices
list: linux-block
message_id: 20261015-blkdev-fixes-tests-v3-4-b6ffa6410514@columbia.edu
link: https://lore.kernel.org/linux-block/20261015-blkdev-fixes-tests-v3-4-b6ffa6410514@columbia.edu/
---

# [PATCH blktests v3 4/4] block/053: add a torn atomic write test for block devices

来源：[https://lore.kernel.org/linux-block/20261015-blkdev-fixes-tests-v3-4-b6ffa6410514@columbia.edu/](https://lore.kernel.org/linux-block/20261015-blkdev-fixes-tests-v3-4-b6ffa6410514@columbia.edu/)

```
A block device atomic write is a hardware atomic write, submitted as a
single bio, so when its buffer can't be fully pinned, the direct I/O
path has to fail the write rather than submit the pinned part.
Otherwise, it submits what was pinned with REQ_ATOMIC set and leaves
the rest to the buffered fallback, tearing the write at the pin
boundary.

This is a regression test for that issue, fixed in the kernel patch
"block: fail a short atomic pin in bio_iov_iter_get_pages()" [1].

Issue a two-page pwritev2() with RWF_ATOMIC to a scsi_debug device with
atomic_wr=1 from a buffer whose last page is PROT_NONE, so that pinning
the buffer stops one page short. Check with statx() that the device
supports an atomic write of that size, then check that the write fails
with EINVAL and that the range still reads back as the old data.

Two pages is the smallest write that leaves one page unpinnable, and
atomic_wr_max_length=256 raises the atomic write unit max to 128K so
that two pages fit for any page size up to 64K.

[1]: https://lore.kernel.org/linux-block/20261009-blkdev-fixes-v6-5-307939c387df@columbia.edu/

Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 src/.gitignore          |   1 +
 src/Makefile            |   1 +
 src/atomic-write-torn.c | 233 ++++++++++++++++++++++++++++++++++++++++++++++++
 tests/block/053         |  60 +++++++++++++
 tests/block/053.out     |   2 +
 5 files changed, 297 insertions(+)

diff --git a/src/.gitignore b/src/.gitignore
index 92c08d1..76a1c5e 100644
--- a/src/.gitignore
+++ b/src/.gitignore
@@ -1,3 +1,4 @@
+/atomic-write-torn
 /bio-bounce-read
 /bio-full-trim
 /bio-trim-pin-leak
diff --git a/src/Makefile b/src/Makefile
index f3f338b..b244405 100644
--- a/src/Makefile
+++ b/src/Makefile
@@ -14,6 +14,7 @@ HAVE_C_DEF = $(shell if printf '$(H)include <%s>\n$(H)ifdef %s\nHAVE_%s\n$(H)end
 		then echo 1;else echo 0; fi)
 
 C_TARGETS := \
+	atomic-write-torn \
 	bio-bounce-read \
 	bio-full-trim \
 	bio-trim-pin-leak \
diff --git a/src/atomic-write-torn.c b/src/atomic-write-torn.c
new file mode 100644
index 0000000..f6f3ccf
--- /dev/null
+++ b/src/atomic-write-torn.c
@@ -0,0 +1,233 @@
+// SPDX-License-Identifier: GPL-3.0+
+/*
+ * Copyright (C) 2026 Tal Zussman
+ *
+ * Check that a RWF_ATOMIC direct write to a block device is all or nothing
+ * when only part of its buffer can be pinned.
+ *
+ * Fill two pages of the device with one byte value, then issue a pwritev2()
+ * with RWF_ATOMIC of a two-page buffer holding another value whose last page
+ * is PROT_NONE, so that pinning the buffer stops one page short. The direct
+ * I/O path must fail the write with EINVAL rather than submit what it pinned.
+ *
+ * Read the range back with O_DIRECT and count the bytes of each value, once
+ * before the atomic write to check the baseline and once after it. The write
+ * has to fail with EINVAL and leave only old bytes on the device.
+ *
+ * The device has to support atomic writes of two pages, which is checked
+ * with statx(). The first two pages of <blockdev> are overwritten.
+ *
+ * usage: atomic-write-torn <blockdev>
+ *
+ * exit:  0 = the write failed with EINVAL and the device is unchanged
+ *        1 = setup error
+ *        2 = the write was torn
+ *        3 = the write did not fail with EINVAL, or went through
+ */
+#define _GNU_SOURCE
+#include <errno.h>
+#include <fcntl.h>
+#include <stdbool.h>
+#include <stdint.h>
+#include <stdio.h>
+#include <stdlib.h>
+#include <string.h>
+#include <sys/mman.h>
+#include <sys/syscall.h>
+#include <sys/uio.h>
+#include <unistd.h>
+
+#ifndef RWF_ATOMIC
+#define RWF_ATOMIC	0x00000040
+#endif
+
+#ifndef STATX_WRITE_ATOMIC
+#define STATX_WRITE_ATOMIC	0x00010000U
+#endif
+#ifndef STATX_ATTR_WRITE_ATOMIC
+#define STATX_ATTR_WRITE_ATOMIC	0x00400000
+#endif
+
+/*
+ * The atomic write fields of struct statx are only in glibc 2.43 and later,
+ * so use a local copy of the kernel's layout and call the syscall directly.
+ */
+struct atomic_statx {
+	uint32_t stx_mask;
+	uint32_t stx_blksize;
+	uint64_t stx_attributes;
+	uint32_t stx_nlink;
+	uint32_t stx_uid;
+	uint32_t stx_gid;
+	uint16_t stx_mode;
+	uint16_t __spare0[1];
+	uint64_t stx_ino;
+	uint64_t stx_size;
+	uint64_t stx_blocks;
+	uint64_t stx_attributes_mask;
+	uint64_t stx_times[8];	/* stx_atime, stx_btime, stx_ctime, stx_mtime */
+	uint32_t stx_rdev_major;
+	uint32_t stx_rdev_minor;
+	uint32_t stx_dev_major;
+	uint32_t stx_dev_minor;
+	uint64_t stx_mnt_id;
+	uint32_t stx_dio_mem_align;
+	uint32_t stx_dio_offset_align;
+	uint64_t stx_subvol;
+	uint32_t stx_atomic_write_unit_min;
+	uint32_t stx_atomic_write_unit_max;
+	uint32_t stx_atomic_write_segments_max;
+	uint32_t stx_dio_read_offset_align;
+	uint32_t stx_atomic_write_unit_max_opt;
+	uint32_t __spare2[1];
+	uint64_t __spare3[8];
+};
+
+_Static_assert(sizeof(struct atomic_statx) == 256, "struct statx is 256 bytes");
+
+#define EXIT_TORN	2
+#define EXIT_UNEXPECTED	3
+
+#define OLD	'A'
+#define NEW	'B'
+
+/* Does the device support an atomic write of len bytes? */
+static bool can_write_atomically(int fd, size_t len)
+{
+	struct atomic_statx stx = { 0 };
+
+	if (syscall(SYS_statx, fd, "", AT_EMPTY_PATH, STATX_WRITE_ATOMIC,
+		    &stx)) {
+		perror("statx");
+		return false;
+	}
+	if (!(stx.stx_mask & STATX_WRITE_ATOMIC) ||
+	    !(stx.stx_attributes & STATX_ATTR_WRITE_ATOMIC)) {
+		fprintf(stderr, "device does not support atomic writes\n");
+		return false;
+	}
+	printf("atomic write unit min %u, max %u\n",
+	       stx.stx_atomic_write_unit_min, stx.stx_atomic_write_unit_max);
+	if (len < stx.stx_atomic_write_unit_min ||
+	    len > stx.stx_atomic_write_unit_max) {
+		fprintf(stderr, "device cannot write %zu bytes atomically\n",
+			len);
+		return false;
+	}
+	return true;
+}
+
+/* Read the range back past the page cache and count the bytes of each value. */
+static int count_bytes(int fd, char *buf, size_t len, size_t *old_bytes,
+		       size_t *new_bytes)
+{
+	size_t i;
+
+	if (pread(fd, buf, len, 0) != (ssize_t)len) {
+		perror("pread");
+		return -1;
+	}
+
+	*old_bytes = *new_bytes = 0;
+	for (i = 0; i < len; i++) {
+		if (buf[i] == OLD)
+			(*old_bytes)++;
+		else if (buf[i] == NEW)
+			(*new_bytes)++;
+	}
+	printf("on disk: %zu old bytes, %zu new bytes, %zu other\n",
+	       *old_bytes, *new_bytes, len - *old_bytes - *new_bytes);
+	return 0;
+}
+
+int main(int argc, char **argv)
+{
+	size_t old_bytes, new_bytes;
+	size_t len, pgsz;
+	struct iovec iov;
+	char *buf;
+	ssize_t ret;
+	int fd, err, status = 1;
+
+	if (argc != 2) {
+		fprintf(stderr, "usage: %s <blockdev>\n", argv[0]);
+		return 1;
+	}
+
+	pgsz = sysconf(_SC_PAGESIZE);
+	len = 2 * pgsz;
+
+	fd = open(argv[1], O_RDWR | O_DIRECT);
+	if (fd < 0) {
+		perror("open");
+		return 1;
+	}
+
+	if (!can_write_atomically(fd, len))
+		goto out_close;
+
+	buf = mmap(NULL, len, PROT_READ | PROT_WRITE,
+		   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
+	if (buf == MAP_FAILED) {
+		perror("mmap");
+		goto out_close;
+	}
+
+	/* Write the old contents and check that they read back. */
+	memset(buf, OLD, len);
+	if (pwrite(fd, buf, len, 0) != (ssize_t)len) {
+		perror("pwrite");
+		goto out_unmap;
+	}
+	if (count_bytes(fd, buf, len, &old_bytes, &new_bytes))
+		goto out_unmap;
+	if (old_bytes != len) {
+		fprintf(stderr, "old contents did not read back\n");
+		goto out_unmap;
+	}
+
+	/* Fill in the new contents and make the last page unreadable. */
+	memset(buf, NEW, len);
+	if (mprotect(buf + len - pgsz, pgsz, PROT_NONE)) {
+		perror("mprotect");
+		goto out_unmap;
+	}
+
+	iov.iov_base = buf;
+	iov.iov_len = len;
+	ret = pwritev2(fd, &iov, 1, 0, RWF_ATOMIC);
+	err = errno;
+	if (ret < 0)
+		printf("pwritev2(RWF_ATOMIC) failed: %s\n", strerror(err));
+	else
+		printf("pwritev2(RWF_ATOMIC) returned %zd of %zu\n", ret, len);
+
+	/* Make the last page readable again and reuse the buffer. */
+	if (mprotect(buf + len - pgsz, pgsz, PROT_READ | PROT_WRITE)) {
+		perror("mprotect");
+		goto out_unmap;
+	}
+	if (count_bytes(fd, buf, len, &old_bytes, &n
```
