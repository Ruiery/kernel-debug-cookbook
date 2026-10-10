---
title: [PATCH blktests v2 3/4] block/051: add a pinned page leak test for trimmed direct writes
list: linux-block
message_id: 20261009-blkdev-fixes-tests-v2-3-fcb3599e47f7@columbia.edu
link: https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-3-fcb3599e47f7@columbia.edu/
---

# [PATCH blktests v2 3/4] block/051: add a pinned page leak test for trimmed direct writes

来源：[https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-3-fcb3599e47f7@columbia.edu/](https://lore.kernel.org/linux-block/20261009-blkdev-fixes-tests-v2-3-fcb3599e47f7@columbia.edu/)

```
bio_iov_iter_align_down() trims a direct I/O bio down to the logical
block size and unpins the pages it drops. A bvec can span several pages
of one folio, each with its own pin, and dropping or shrinking such a
bvec has to release all of them. When it does not, the folio is never
freed.

This is a regression test for that issue, fixed in the kernel patch
"block: unpin all pages of a bvec in bio_iov_iter_align_down()" [1].

Issue O_DIRECT pwritev() from a hugetlb mapping to a memory-backed
null_blk device with a 64K logical block size, with a first segment that
ends half a block past a block boundary and an unreadable second
segment, so that the bio is trimmed by several pages of one huge page.
Place the first segment across two huge pages so the tail is its own
bvec and gets dropped, and inside one huge page so the tail is the end
of a larger bvec and gets shrunk, to cover both paths. Compare
HugePages_Free before and after, and fail if huge pages leaked.

The leak needs a logical block size above the page size, i.e.
CONFIG_TRANSPARENT_HUGEPAGE raising BLK_MAX_BLOCK_SIZE to 64K, and a
large folio backing the buffer, which hugetlb provides. Reserve huge
pages for the test and restore the previous count afterwards.

[1]: https://lore.kernel.org/linux-block/20261009-blkdev-fixes-v6-8-307939c387df@columbia.edu/

Signed-off-by: Tal Zussman <tz2294@columbia.edu>
---
 src/.gitignore          |   1 +
 src/Makefile            |   1 +
 src/bio-trim-pin-leak.c | 191 ++++++++++++++++++++++++++++++++++++++++++++++++
 tests/block/051         |  64 ++++++++++++++++
 tests/block/051.out     |   2 +
 5 files changed, 259 insertions(+)

diff --git a/src/.gitignore b/src/.gitignore
index dbebc22..92c08d1 100644
--- a/src/.gitignore
+++ b/src/.gitignore
@@ -1,5 +1,6 @@
 /bio-bounce-read
 /bio-full-trim
+/bio-trim-pin-leak
 /dio-fallback-race
 /dio-offsets
 /discontiguous-io
diff --git a/src/Makefile b/src/Makefile
index b7e8ca9..0bdfd05 100644
--- a/src/Makefile
+++ b/src/Makefile
@@ -16,6 +16,7 @@ HAVE_C_DEF = $(shell if printf '$(H)include <%s>\n$(H)ifdef %s\nHAVE_%s\n$(H)end
 C_TARGETS := \
 	bio-bounce-read \
 	bio-full-trim \
+	bio-trim-pin-leak \
 	dio-offsets \
 	loblksize \
 	loop_change_fd \
diff --git a/src/bio-trim-pin-leak.c b/src/bio-trim-pin-leak.c
new file mode 100644
index 0000000..54af181
--- /dev/null
+++ b/src/bio-trim-pin-leak.c
@@ -0,0 +1,191 @@
+// SPDX-License-Identifier: GPL-3.0+
+/*
+ * Copyright (C) 2026 Tal Zussman
+ *
+ * Check that a direct write trimmed to the logical block size unpins all the
+ * pages it drops.
+ *
+ * Issue O_DIRECT pwritev() from a hugetlb mapping with a two-segment iovec
+ * whose first segment ends half a block past a block boundary and whose
+ * second segment is an unreadable PROT_NONE mapping. The direct path pins the
+ * first segment, fails to pin the second and trims the bio down to a block
+ * boundary. The trimmed tail spans several pages of one huge page, each with
+ * its own pin. If the trim releases at most one of them, the huge page
+ * never returns to the pool, which shows up as a drop in HugePages_Free.
+ *
+ * The tail is either its own bvec, when the first segment straddles two huge
+ * pages, or the end of a larger one, when it sits inside a single huge page.
+ * Each iteration issues one write of each kind. The direct I/O fallback
+ * finishes the trimmed half block through the page cache, so each write
+ * returns one and a half blocks.
+ *
+ * The tail only holds several pins when it spans several pages of a large
+ * folio, so the device needs a logical block size of at least four pages and
+ * the buffer comes from a hugetlb mapping.
+ *
+ * usage: bio-trim-pin-leak <blockdev> <iterations>
+ *
+ * exit:  0 = no huge pages leaked
+ *        1 = setup error
+ *        2 = huge pages leaked
+ */
+#define _GNU_SOURCE
+#include <fcntl.h>
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
+#define EXIT_LEAKED	2
+
+static long meminfo(const char *key)
+{
+	char line[256];
+	long val = -1;
+	FILE *f;
+
+	f = fopen("/proc/meminfo", "r");
+	if (!f) {
+		perror("fopen");
+		return -1;
+	}
+
+	while (fgets(line, sizeof(line), f)) {
+		if (!strncmp(line, key, strlen(key))) {
+			val = strtol(line + strlen(key), NULL, 10);
+			break;
+		}
+	}
+
+	fclose(f);
+	return val;
+}
+
+int main(int argc, char **argv)
+{
+	struct iovec iov[2];
+	long pgsz, hpsz;
+	long before, after;
+	char *badseg;
+	char *map;
+	int lbs, iters;
+	int fd, i;
+
+	if (argc != 3) {
+		fprintf(stderr, "usage: %s <blockdev> <iterations>\n", argv[0]);
+		return EXIT_FAILURE;
+	}
+
+	iters = atoi(argv[2]);
+
+	pgsz = sysconf(_SC_PAGESIZE);
+	if (pgsz < 0) {
+		perror("sysconf");
+		return EXIT_FAILURE;
+	}
+
+	hpsz = meminfo("Hugepagesize:") * 1024;
+	if (hpsz <= 0) {
+		fprintf(stderr, "no hugetlb page size in /proc/meminfo\n");
+		return EXIT_FAILURE;
+	}
+
+	fd = open(argv[1], O_RDWR | O_DIRECT);
+	if (fd < 0) {
+		perror("open");
+		return EXIT_FAILURE;
+	}
+
+	if (ioctl(fd, BLKSSZGET, &lbs)) {
+		perror("BLKSSZGET");
+		return EXIT_FAILURE;
+	}
+	printf("logical block size: %d, page size: %ld, huge page size: %ld\n",
+	       lbs, pgsz, hpsz);
+
+	/*
+	 * The trimmed tail is half a block, and it has to span at least two
+	 * pages for a pin to leak.
+	 */
+	if (lbs < 4 * pgsz) {
+		fprintf(stderr, "logical block size %d is below four pages\n",
+			lbs);
+		return EXIT_FAILURE;
+	}
+	if (hpsz < 2 * lbs) {
+		fprintf(stderr, "huge page size %ld is below two blocks\n", hpsz);
+		return EXIT_FAILURE;
+	}
+
+	badseg = mmap(NULL, lbs, PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
+	if (badseg == MAP_FAILED) {
+		perror("mmap");
+		return EXIT_FAILURE;
+	}
+
+	before = meminfo("HugePages_Free:");
+	if (before < 2 * iters + 2) {
+		fprintf(stderr, "HugePages_Free is %ld, need at least %d\n",
+			before, 2 * iters + 2);
+		return EXIT_FAILURE;
+	}
+
+	for (i = 0; i < iters; i++) {
+		map = mmap(NULL, 2 * hpsz, PROT_READ | PROT_WRITE,
+			   MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
+		if (map == MAP_FAILED) {
+			perror("mmap");
+			return EXIT_FAILURE;
+		}
+		memset(map, 'A', 2 * hpsz);
+
+		iov[0].iov_len = lbs + lbs / 2;
+		iov[1].iov_base = badseg;
+		iov[1].iov_len = lbs / 2;
+
+		/*
+		 * One block from the end of the first huge page and half a
+		 * block from the start of the second, then an unreadable
+		 * segment: the bio is trimmed by half a block, dropping the
+		 * bvec pinned from the second huge page.
+		 */
+		iov[0].iov_base = map + hpsz - lbs;
+		if (pwritev(fd, iov, 2, 0) != lbs + lbs / 2) {
+			perror("pwritev");
+			return EXIT_FAILURE;
+		}
+
+		/*
+		 * The same write from the start of the first huge page: the
+		 * pinned segment is a single bvec, and the trim shrinks it
+		 * by half a block instead of dropping one.
+		 */
+		iov[0].iov_base = map;
+		if (pwritev(fd, iov, 2, 0) != lbs + lbs / 2) {
+			perror("pwritev");
+			return EXIT_FAILURE;
+		}
+
+		if (munmap(map, 2 * hpsz)) {
+			perror("munmap");
+			return EXIT_FAILURE;
+		}
+	}
+
+	after = meminfo("HugePages_Free:");
+	printf("HugePages_Free: %ld -> %ld over %d iterations\n",
+	       before, after, iters);
+
+	if (after < before) {
+		printf("%ld huge pages leaked\n", before - after);
+		return EXIT_LEAKED;
+	}
+
+	printf("no huge pages leaked\n");
+	return EXIT_SUCCESS;
+}
diff --git a/tests/block/051 b/tests/block/051
new file mode 100755
index 0000000..a4edec2
--- /dev/null
+++ b/tests/block/051
@@ -0,0 +1,64 @@
+#!/bin/bash
+# SPDX-License-Identifier: GPL-3.0+
+# Copyright (C) 2026 Tal Zussman
+#
+# Issue partial O_DIRECT writes from a hugetlb mapping to a block device with
+# a 64K logical block size and check that no huge pages leak. The bio of such
+# a write is trimmed down to a block boundary, and the pages it drops each
+# hold their own pin when a large folio backs the buffer. If the trim
+# releases at most
```
