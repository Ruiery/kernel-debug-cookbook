---
title: [PATCH blktests v2 1/4] block/049: add a direct I/O write fallback race test for block devices
list: linux-block
message_id: 20261009-blkdev-fixes-tests-v2-1-fcb3599e47f7@columbia.edu
link: https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-1-fcb3599e47f7@columbia.edu/
---

# [PATCH blktests v2 1/4] block/049: add a direct I/O write fallback race test for block devices

来源：[https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-1-fcb3599e47f7@columbia.edu/](https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-1-fcb3599e47f7@columbia.edu/)

```
A direct write to a block device that completes only partially finishes
as a buffered write through the direct I/O fallback. That buffered write
has to hold i_rwsem like the plain buffered write path, so that it does
not race set_blocksize() raising the mapping's minimum folio order and
add a folio that is too small for the mapping.

This is a regression test for that issue, fixed in the kernel patch
"block: take i_rwsem for the direct I/O write fallback" [1].

Issue O_DIRECT pwritev() to a memory-backed null_blk device with a
two-segment iovec whose second segment is an unreadable PROT_NONE
mapping, so that the direct path returns short and enters the fallback.
Meanwhile toggle the second segment's protection so that some fallbacks
get past the fault-in and reach the page cache, populate the page cache
with folios of the current block size, and toggle the block size between
512 bytes and 64K with BLKBSZSET. A CONFIG_DEBUG_VM kernel reports the
folio order mismatch as a BUG, which blktests picks up from dmesg.

The minimum folio order only moves with block sizes above the page size,
i.e. with CONFIG_TRANSPARENT_HUGEPAGE raising BLK_MAX_BLOCK_SIZE to 64K.

[1]: https://lore.kernel.org/linux-block/20261009-blkdev-fixes-v6-2-307939c387df@columbia.edu/

Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 src/.gitignore          |   1 +
 src/Makefile            |   7 +-
 src/dio-fallback-race.c | 229 ++++++++++++++++++++++++++++++++++++++++++++++++
 tests/block/049         |  57 ++++++++++++
 tests/block/049.out     |   2 +
 5 files changed, 295 insertions(+), 1 deletion(-)

diff --git a/src/.gitignore b/src/.gitignore
index e9869e1..754beef 100644
--- a/src/.gitignore
+++ b/src/.gitignore
@@ -1,5 +1,6 @@
 /bio-bounce-read
 /bio-full-trim
+/dio-fallback-race
 /dio-offsets
 /discontiguous-io
 /loblksize
diff --git a/src/Makefile b/src/Makefile
index dd64694..4590639 100644
--- a/src/Makefile
+++ b/src/Makefile
@@ -33,6 +33,7 @@ C_TARGETS := \
 C_URING_TARGETS := metadata \
 	nvme-passthru-admin-uring
 C_UBLK_TARGETS := miniublk
+C_THREAD_TARGETS := dio-fallback-race
 
 HAVE_LIBURING := $(call HAVE_C_MACRO,liburing.h,IORING_OP_URING_CMD)
 HAVE_UBLK_HEADER := $(call HAVE_C_HEADER,linux/ublk_cmd.h,1)
@@ -44,7 +45,7 @@ CXX_TARGETS := \
 SYZKALLER_TARGETS := \
 	sg/syzkaller1
 
-TARGETS := $(C_TARGETS) $(CXX_TARGETS) $(SYZKALLER_TARGETS)
+TARGETS := $(C_TARGETS) $(C_THREAD_TARGETS) $(CXX_TARGETS) $(SYZKALLER_TARGETS)
 
 ifeq ($(HAVE_UBLK_HEADER), 1)
 ifeq ($(HAVE_NEW_UBLK_INTF), 1)
@@ -69,6 +70,7 @@ override CXXFLAGS := -O2 -std=c++11 -Wall -Wextra -Wshadow -Wno-sign-compare \
 		     -Werror $(CXXFLAGS) $(CONFIG_DEFS)
 URING_FLAGS :=  -D_GNU_SOURCE
 URING_LIBS := -lpthread -luring
+THREAD_LIBS := -lpthread
 LDFLAGS ?=
 
 all: $(TARGETS)
@@ -89,6 +91,9 @@ $(CXX_TARGETS): %: %.cpp
 $(SYZKALLER_TARGETS): %: %.c
 	$(CC) $(CFLAGS) -Wno-unused-but-set-variable $(LDFLAGS) -o $@ $^
 
+$(C_THREAD_TARGETS): %: %.c
+	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o $@ $^ $(THREAD_LIBS)
+
 $(C_URING_TARGETS): %: %.c
 	$(CC) $(CFLAGS) $(LDFLAGS) $(URING_FLAGS) -o $@ $^ $(URING_LIBS)
 
diff --git a/src/dio-fallback-race.c b/src/dio-fallback-race.c
new file mode 100644
index 0000000..e5221c5
--- /dev/null
+++ b/src/dio-fallback-race.c
@@ -0,0 +1,229 @@
+// SPDX-License-Identifier: GPL-3.0+
+/*
+ * Copyright (C) 2026 Tal Zussman
+ *
+ * Race partial O_DIRECT writes to a block device against BLKBSZSET.
+ *
+ * Writer threads issue O_DIRECT pwritev() with a two-segment iovec whose
+ * second segment is an unreadable PROT_NONE mapping. The direct path writes
+ * the first segment, fails to pin the second and returns short, so the write
+ * finishes as a buffered write through the direct I/O fallback. A second
+ * thread toggles the second segment's protection so that some fallbacks get
+ * past fault_in_iov_iter_readable() and reach the page cache, a third
+ * populates the page cache with folios of the current block size, and a
+ * fourth toggles the block size between 512 bytes and 64K with BLKBSZSET.
+ *
+ * The fallback has to run under i_rwsem like the plain buffered write path.
+ * If it does not, it races set_blocksize() raising the mapping's minimum
+ * folio order and adds a folio that is too small for the mapping, which a
+ * CONFIG_DEBUG_VM kernel reports as a BUG. The caller checks dmesg.
+ *
+ * usage: dio-fallback-race <blockdev> <seconds>
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
+#include <sys/mman.h>
+#include <sys/uio.h>
+#include <unistd.h>
+
+#include <linux/fs.h>
+
+#define GOOD		(8 * 1024)		/* written by the direct path */
+#define BAD		(64 * 1024)		/* unreadable, forces a short write */
+#define RANGE		(2 * 1024 * 1024)	/* keep the race on a few folios */
+#define NR_WRITERS	2
+
+#define SMALL_BS	512
+#define LARGE_BS	(64 * 1024)
+
+static const char *dev;
+static long pgsz;
+static char *badseg;
+static int bszfd;
+static volatile int stop;
+static int failed;
+
+/* partial direct write, finished as a buffered write by the fallback */
+static void *writer(void *arg)
+{
+	struct iovec iov[2];
+	off_t off = 0;
+	char *good;
+	int fd;
+
+	fd = open(dev, O_RDWR | O_DIRECT);
+	if (fd < 0) {
+		perror("open");
+		failed = 1;
+		return NULL;
+	}
+
+	if (posix_memalign((void **)&good, pgsz, GOOD)) {
+		perror("posix_memalign");
+		failed = 1;
+		return NULL;
+	}
+	memset(good, 'A', GOOD);
+
+	iov[0].iov_base = good;
+	iov[0].iov_len = GOOD;
+	iov[1].iov_base = badseg;
+	iov[1].iov_len = BAD;
+
+	while (!stop) {
+		if (pwritev(fd, iov, 2, off) < 0) {
+			perror("pwritev");
+			failed = 1;
+			break;
+		}
+		off = (off + GOOD) % RANGE;
+	}
+
+	return NULL;
+}
+
+/* let some fallbacks get past the fault-in and into the page cache */
+static void *flipper(void *arg)
+{
+	while (!stop) {
+		if (mprotect(badseg, BAD, PROT_READ | PROT_WRITE) ||
+		    mprotect(badseg, BAD, PROT_NONE)) {
+			perror("mprotect");
+			failed = 1;
+			break;
+		}
+	}
+
+	return NULL;
+}
+
+/* populate the page cache with folios sized for the current block size */
+static void *reader(void *arg)
+{
+	off_t off = 0;
+	char *buf;
+	int fd;
+
+	fd = open(dev, O_RDONLY);
+	if (fd < 0) {
+		perror("open");
+		failed = 1;
+		return NULL;
+	}
+
+	buf = malloc(GOOD);
+	if (!buf) {
+		perror("malloc");
+		failed = 1;
+		return NULL;
+	}
+
+	while (!stop) {
+		if (pread(fd, buf, GOOD, off) < 0) {
+			perror("pread");
+			failed = 1;
+			break;
+		}
+		readahead(fd, off, RANGE / 4);
+		off = (off + GOOD) % RANGE;
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
+	pthread_t writers[NR_WRITERS];
+	pthread_t flipper_t, reader_t, resizer_t;
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
+	pgsz = sysconf(_SC_PAGESIZE);
+	if (pgsz < 0) {
+		perror("sysconf");
+		return EXIT_FAILURE;
+	}
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
+	badseg = mmap(NULL, BAD, PROT_NONE, MAP_PRIVATE
```
