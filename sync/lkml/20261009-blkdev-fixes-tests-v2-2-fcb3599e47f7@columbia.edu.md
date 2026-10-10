---
title: [PATCH blktests v2 2/4] block/050: add a splice read race test for block devices
list: linux-block
message_id: 20261009-blkdev-fixes-tests-v2-2-fcb3599e47f7@columbia.edu
link: https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-2-fcb3599e47f7@columbia.edu/
---

# [PATCH blktests v2 2/4] block/050: add a splice read race test for block devices

来源：[https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-2-fcb3599e47f7@columbia.edu/](https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-2-fcb3599e47f7@columbia.edu/)

```
The block device splice read path has to hold i_rwsem like the plain
read path, so that it does not race set_blocksize() raising the
mapping's minimum folio order and add a folio that is too small for the
mapping.

This is a regression test for that issue, fixed in the kernel patch
"block: take i_rwsem for the splice read path" [1].

splice() from a memory-backed null_blk device into a pipe while toggling
the block size between 512 bytes and 64K with BLKBSZSET. A
CONFIG_DEBUG_VM kernel reports the folio order mismatch as a BUG, which
blktests picks up from dmesg.

The minimum folio order only moves with block sizes above the page size,
i.e. with CONFIG_TRANSPARENT_HUGEPAGE raising BLK_MAX_BLOCK_SIZE to 64K.

[1]: https://lore.kernel.org/linux-block/20261009-blkdev-fixes-v6-3-307939c387df@columbia.edu/

Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 src/.gitignore      |   1 +
 src/Makefile        |   3 +-
 src/splice-race.c   | 171 ++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/block/050     |  54 +++++++++++++++++
 tests/block/050.out |   2 +
 5 files changed, 230 insertions(+), 1 deletion(-)

diff --git a/src/.gitignore b/src/.gitignore
index 754beef..dbebc22 100644
--- a/src/.gitignore
+++ b/src/.gitignore
@@ -11,6 +11,7 @@
 /mount_clear_sock
 /nbdsetsize
 /openclose
+/splice-race
 /sg/dxfer-from-dev
 /sg/syzkaller1
 /zbdioctl
diff --git a/src/Makefile b/src/Makefile
index 4590639..b7e8ca9 100644
--- a/src/Makefile
+++ b/src/Makefile
@@ -33,7 +33,8 @@ C_TARGETS := \
 C_URING_TARGETS := metadata \
 	nvme-passthru-admin-uring
 C_UBLK_TARGETS := miniublk
-C_THREAD_TARGETS := dio-fallback-race
+C_THREAD_TARGETS := dio-fallback-race \
+	splice-race
 
 HAVE_LIBURING := $(call HAVE_C_MACRO,liburing.h,IORING_OP_URING_CMD)
 HAVE_UBLK_HEADER := $(call HAVE_C_HEADER,linux/ublk_cmd.h,1)
diff --git a/src/splice-race.c b/src/splice-race.c
new file mode 100644
index 0000000..e411752
--- /dev/null
+++ b/src/splice-race.c
@@ -0,0 +1,171 @@
+// SPDX-License-Identifier: GPL-3.0+
+/*
+ * Copyright (C) 2026 Tal Zussman
+ *
+ * Race splice() from a block device against BLKBSZSET.
+ *
+ * Splicer threads splice from the device into a pipe while another thread
+ * toggles the block size between 512 bytes and 64K with BLKBSZSET.
+ *
+ * The splice read path has to run under i_rwsem like the plain read path.
+ * If it does not, it races set_blocksize() raising the mapping's minimum
+ * folio order and adds a folio that is too small for the mapping, which a
+ * CONFIG_DEBUG_VM kernel reports as a BUG. The caller checks dmesg.
+ *
+ * usage: splice-race <blockdev> <seconds>
+ *
+ * exit:  0 = ran for <seconds>
+ *        1 = setup error
+ */
+#define _GNU_SOURCE
+#include <fcntl.h>
+#include <pthread.h>
+#include <stdio.h>
+#include <stdlib.h>
+#include <string.h>
+#include <sys/ioctl.h>
+#include <unistd.h>
+
+#include <linux/fs.h>
+
+#define CHUNK		(64 * 1024)
+#define RANGE		(2 * 1024 * 1024)	/* keep the race on a few folios */
+#define NR_SPLICERS	4
+
+#define SMALL_BS	512
+#define LARGE_BS	(64 * 1024)
+
+static const char *dev;
+static int bszfd;
+static volatile int stop;
+static int failed;
+
+/* filemap_splice_read() from the device */
+static void *splicer(void *arg)
+{
+	int pipefd[2];
+	loff_t off = 0;
+	char *sink;
+	int fd;
+
+	fd = open(dev, O_RDONLY);
+	if (fd < 0) {
+		perror("open");
+		failed = 1;
+		return NULL;
+	}
+
+	if (pipe(pipefd)) {
+		perror("pipe");
+		failed = 1;
+		return NULL;
+	}
+
+	sink = malloc(CHUNK);
+	if (!sink) {
+		perror("malloc");
+		failed = 1;
+		return NULL;
+	}
+
+	while (!stop) {
+		ssize_t n = splice(fd, &off, pipefd[1], NULL, CHUNK, 0);
+
+		if (n < 0) {
+			perror("splice");
+			failed = 1;
+			break;
+		}
+
+		/* drain the pipe so the next splice does not block on it */
+		while (n > 0) {
+			ssize_t d = read(pipefd[0], sink, n);
+
+			if (d <= 0) {
+				perror("read");
+				failed = 1;
+				return NULL;
+			}
+			n -= d;
+		}
+
+		if (off >= RANGE)
+			off = 0;
+	}
+
+	return NULL;
+}
+
+/* change i_blkbits and the mapping's minimum folio order underneath them */
+static void *resizer(void *arg)
+{
+	int bs = SMALL_BS;
+
+	while (!stop) {
+		if (ioctl(bszfd, BLKBSZSET, &bs)) {
+			perror("BLKBSZSET");
+			failed = 1;
+			break;
+		}
+		bs = bs == SMALL_BS ? LARGE_BS : SMALL_BS;
+	}
+
+	return NULL;
+}
+
+static int spawn(pthread_t *t, void *(*fn)(void *))
+{
+	int err = pthread_create(t, NULL, fn, NULL);
+
+	if (err)
+		fprintf(stderr, "pthread_create: %s\n", strerror(err));
+
+	return err;
+}
+
+int main(int argc, char **argv)
+{
+	pthread_t splicers[NR_SPLICERS];
+	pthread_t resizer_t;
+	int bs = LARGE_BS;
+	int i;
+
+	if (argc != 3) {
+		fprintf(stderr, "usage: %s <blockdev> <seconds>\n", argv[0]);
+		return EXIT_FAILURE;
+	}
+
+	dev = argv[1];
+
+	bszfd = open(dev, O_RDONLY);
+	if (bszfd < 0) {
+		perror("open");
+		return EXIT_FAILURE;
+	}
+
+	/*
+	 * The minimum folio order only moves with block sizes above the page
+	 * size, which needs BLK_MAX_BLOCK_SIZE above PAGE_SIZE, i.e.
+	 * CONFIG_TRANSPARENT_HUGEPAGE.
+	 */
+	if (ioctl(bszfd, BLKBSZSET, &bs)) {
+		perror("BLKBSZSET");
+		return EXIT_FAILURE;
+	}
+
+	for (i = 0; i < NR_SPLICERS; i++) {
+		if (spawn(&splicers[i], splicer))
+			return EXIT_FAILURE;
+	}
+	if (spawn(&resizer_t, resizer))
+		return EXIT_FAILURE;
+
+	sleep(atoi(argv[2]));
+	stop = 1;
+
+	for (i = 0; i < NR_SPLICERS; i++)
+		pthread_join(splicers[i], NULL);
+	pthread_join(resizer_t, NULL);
+
+	return failed ? EXIT_FAILURE : EXIT_SUCCESS;
+}
diff --git a/tests/block/050 b/tests/block/050
new file mode 100755
index 0000000..64c0406
--- /dev/null
+++ b/tests/block/050
@@ -0,0 +1,54 @@
+#!/bin/bash
+# SPDX-License-Identifier: GPL-3.0+
+# Copyright (C) 2026 Tal Zussman
+#
+# Race splice() from a block device against BLKBSZSET. The splice read path
+# has to hold i_rwsem like the plain read path so that it does not race
+# set_blocksize() raising the mapping's minimum folio order. Without it, the
+# splice adds a folio that is too small for the mapping, which a
+# CONFIG_DEBUG_VM kernel reports as a BUG.
+#
+# Regression test for patch "block: take i_rwsem for the splice read path".
+
+. tests/block/rc
+. common/null_blk
+
+DESCRIPTION="race splice() from a block device against BLKBSZSET"
+TIMED=1
+
+requires() {
+	_have_null_blk
+	_have_kernel_option TRANSPARENT_HUGEPAGE
+	_have_kernel_option DEBUG_VM
+	_have_src_program splice-race
+	if (( $(_get_page_size) >= 65536 )); then
+		SKIP_REASONS+=("a 64K block size is not above the page size")
+		return 1
+	fi
+}
+
+test() {
+	echo "Running ${TEST_NAME}"
+
+	: "${TIMEOUT:=30}"
+
+	if ! _configure_null_blk nullb1 blocksize=512 memory_backed=1 \
+	     size=64 power=1; then
+		echo "configuring null_blk failed"
+		return 1
+	fi
+
+	if ! blockdev --setbsz 65536 /dev/nullb1; then
+		SKIP_REASONS+=("kernel does not support a 64K block size")
+		_exit_null_blk
+		return
+	fi
+
+	if ! src/splice-race /dev/nullb1 "${TIMEOUT}" >>"${FULL}" 2>&1; then
+		echo "splice-race helper failed"
+	fi
+
+	_exit_null_blk
+
+	echo "Test complete"
+}
diff --git a/tests/block/050.out b/tests/block/050.out
new file mode 100644
index 0000000..fc4e537
--- /dev/null
+++ b/tests/block/050.out
@@ -0,0 +1,2 @@
+Running block/050
+Test complete

-- 
2.39.5
```
