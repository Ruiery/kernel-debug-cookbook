---
title: [PATCH 2/4] selftests: nbd: test concurrent device starts
list: linux-block
message_id: 43fe4ee554aff0b97377cbb7be55ef0a0bdad5f6.1792399225.git.liuyun01@kylinos.cn
link: https://lore.kernel.org/linux-block/43fe4ee554aff0b97377cbb7be55ef0a0bdad5f6.1792399225.git.liuyun01@kylinos.cn/
---

# [PATCH 2/4] selftests: nbd: test concurrent device starts

来源：[https://lore.kernel.org/linux-block/43fe4ee554aff0b97377cbb7be55ef0a0bdad5f6.1792399225.git.liuyun01@kylinos.cn/](https://lore.kernel.org/linux-block/43fe4ee554aff0b97377cbb7be55ef0a0bdad5f6.1792399225.git.liuyun01@kylinos.cn/)

```
From: Jackie Liu <liuyun01@kylinos.cn>

Add an NBD selftest that races two NBD_DO_IT callers and checks that the
loser returns EBUSY while the sysfs pid attribute retains the successful
caller's PID. Prime the device with a different connection count before
each attempt so that the hardware queue update cannot take its no-op
path.

Use socket pairs and an exclusively opened unused device, with bounded
waits and cleanup of the test's own configuration. Skip the test when
CAP_SYS_ADMIN, at least two CPUs, or an unused NBD device is unavailable.
Register the new nbd target with kselftest.

The test uses scheduling stress rather than kernel instrumentation, so a
passing run only means that no regression was observed during that run.
The number of attempts, delays and random seed can be set on the command
line. Load nbd with nbds_max=4 max_part=0 before running the test.

Signed-off-by: Jackie Liu <liuyun01@kylinos.cn>
---
 MAINTAINERS                                |   1 +
 tools/testing/selftests/Makefile           |   1 +
 tools/testing/selftests/nbd/.gitignore     |   1 +
 tools/testing/selftests/nbd/Makefile       |   8 +
 tools/testing/selftests/nbd/config         |   7 +
 tools/testing/selftests/nbd/nbd_common.c   | 465 +++++++++++++++++++++
 tools/testing/selftests/nbd/nbd_common.h   |  53 +++
 tools/testing/selftests/nbd/nbd_pid_race.c |  86 ++++
 8 files changed, 622 insertions(+)
 create mode 100644 tools/testing/selftests/nbd/.gitignore
 create mode 100644 tools/testing/selftests/nbd/Makefile
 create mode 100644 tools/testing/selftests/nbd/config
 create mode 100644 tools/testing/selftests/nbd/nbd_common.c
 create mode 100644 tools/testing/selftests/nbd/nbd_common.h
 create mode 100644 tools/testing/selftests/nbd/nbd_pid_race.c

diff --git a/MAINTAINERS b/MAINTAINERS
index 782389bd5cd3..f4495cb942d7 100644
--- a/MAINTAINERS
+++ b/MAINTAINERS
@@ -18884,6 +18884,7 @@ F:	Documentation/admin-guide/blockdev/nbd.rst
 F:	drivers/block/nbd.c
 F:	include/trace/events/nbd.h
 F:	include/uapi/linux/nbd.h
+F:	tools/testing/selftests/nbd/
 
 NETWORK DROP MONITOR
 M:	Neil Horman <nhorman@tuxdriver.com>
diff --git a/tools/testing/selftests/Makefile b/tools/testing/selftests/Makefile
index bc4fdb6f5337..67ab46cb173b 100644
--- a/tools/testing/selftests/Makefile
+++ b/tools/testing/selftests/Makefile
@@ -82,6 +82,7 @@ TARGETS += mount_setattr
 TARGETS += move_mount_set_group
 TARGETS += mqueue
 TARGETS += mseal_system_mappings
+TARGETS += nbd
 TARGETS += nci
 TARGETS += net
 TARGETS += net/af_unix
diff --git a/tools/testing/selftests/nbd/.gitignore b/tools/testing/selftests/nbd/.gitignore
new file mode 100644
index 000000000000..5516e34b30f2
--- /dev/null
+++ b/tools/testing/selftests/nbd/.gitignore
@@ -0,0 +1 @@
+/nbd_pid_race
diff --git a/tools/testing/selftests/nbd/Makefile b/tools/testing/selftests/nbd/Makefile
new file mode 100644
index 000000000000..e49ee6cfc82e
--- /dev/null
+++ b/tools/testing/selftests/nbd/Makefile
@@ -0,0 +1,8 @@
+# SPDX-License-Identifier: GPL-2.0-only
+CFLAGS += -O2 -Wall -Wextra $(KHDR_INCLUDES)
+TEST_GEN_PROGS := nbd_pid_race
+LOCAL_HDRS += nbd_common.h
+
+include ../lib.mk
+
+$(TEST_GEN_PROGS): nbd_common.c
diff --git a/tools/testing/selftests/nbd/config b/tools/testing/selftests/nbd/config
new file mode 100644
index 000000000000..390cd288cec6
--- /dev/null
+++ b/tools/testing/selftests/nbd/config
@@ -0,0 +1,7 @@
+CONFIG_MODULES=y
+CONFIG_BLOCK=y
+CONFIG_BLK_DEV_NBD=m
+CONFIG_NET=y
+CONFIG_UNIX=y
+CONFIG_SMP=y
+CONFIG_SYSFS=y
diff --git a/tools/testing/selftests/nbd/nbd_common.c b/tools/testing/selftests/nbd/nbd_common.c
new file mode 100644
index 000000000000..b686c02fbd8e
--- /dev/null
+++ b/tools/testing/selftests/nbd/nbd_common.c
@@ -0,0 +1,465 @@
+// SPDX-License-Identifier: GPL-2.0
+/*
+ * Copyright (C) 2026 KylinSoft Co., Ltd. All rights reserved.
+ *
+ * Exercise the nbd_start_device() config_lock window introduced by
+ * 8b428f42f3ed ("nbd: fix lockdep deadlock warning"). Prime the hardware
+ * queue count before each race so the update cannot take its no-op path.
+ * A passing stress run means that no regression was observed in that run;
+ * scheduling alone cannot guarantee that both callers entered the window.
+ */
+#include <dirent.h>
+#include <errno.h>
+#include <fcntl.h>
+#include <getopt.h>
+#include <limits.h>
+#include <linux/capability.h>
+#include <linux/nbd.h>
+#include <poll.h>
+#include <signal.h>
+#include <stdbool.h>
+#include <stdio.h>
+#include <stdlib.h>
+#include <string.h>
+#include <sys/ioctl.h>
+#include <sys/socket.h>
+#include <sys/syscall.h>
+#include <sys/wait.h>
+#include <time.h>
+#include <unistd.h>
+
+#include "../kselftest.h"
+#include "nbd_common.h"
+
+#define MAX_DEVICES	32
+
+static int devices[MAX_DEVICES];
+static int nr_devices;
+
+long long nbd_now_ms(void)
+{
+	struct timespec ts;
+
+	clock_gettime(CLOCK_MONOTONIC, &ts);
+	return (long long)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
+}
+
+static int read_timeout(int fd, void *buf, size_t len, int timeout)
+{
+	long long end = nbd_now_ms() + timeout;
+	struct pollfd pfd = { .fd = fd, .events = POLLIN };
+	size_t done = 0;
+
+	while (done < len) {
+		long long left = end - nbd_now_ms();
+		ssize_t n;
+		int ret;
+
+		ret = poll(&pfd, 1, left > 0 ? left : 0);
+		if (ret < 0 && errno == EINTR)
+			continue;
+		if (ret <= 0)
+			return ret ? -errno : -ETIMEDOUT;
+		n = read(fd, (char *)buf + done, len - done);
+		if (n < 0 && errno == EINTR)
+			continue;
+		if (n <= 0)
+			return n ? -errno : -EPIPE;
+		done += n;
+	}
+	return 0;
+}
+
+static void close_fd(int *fd)
+{
+	if (*fd >= 0)
+		close(*fd);
+	*fd = -1;
+}
+
+/* An absent pid attribute denotes an unstarted device, not a read error. */
+int nbd_device_pid(int index)
+{
+	char path[64], buf[32], *end;
+	long pid;
+	int fd, error;
+	ssize_t n;
+
+	snprintf(path, sizeof(path), "/sys/block/nbd%d/pid", index);
+	fd = open(path, O_RDONLY | O_CLOEXEC);
+	if (fd < 0)
+		return errno == ENOENT ? 0 : -errno;
+	do {
+		n = read(fd, buf, sizeof(buf) - 1);
+	} while (n < 0 && errno == EINTR);
+	error = errno;
+	close(fd);
+	if (n <= 0) {
+		/* Only a removed attribute confirms that the device has stopped. */
+		if (access(path, F_OK) < 0 && errno == ENOENT)
+			return 0;
+		return n < 0 ? -error : -EIO;
+	}
+	buf[n] = '\0';
+	errno = 0;
+	pid = strtol(buf, &end, 10);
+	if (errno || end == buf || (*end && *end != '\n') ||
+	    pid <= 0 || pid > INT_MAX)
+		return -EPROTO;
+	return pid;
+}
+
+static int open_unused(int index)
+{
+	char path[64];
+	int fd, pid;
+
+	snprintf(path, sizeof(path), "/dev/nbd%d", index);
+	fd = open(path, O_RDWR | O_EXCL | O_CLOEXEC);
+	if (fd < 0)
+		return -errno;
+	pid = nbd_device_pid(index);
+	if (pid) {
+		close(fd);
+		return pid < 0 ? pid : -EBUSY;
+	}
+	return fd;
+}
+
+static int find_device(void)
+{
+	struct dirent *entry;
+	DIR *dir;
+
+	nr_devices = 0;
+	dir = opendir("/sys/block");
+	if (!dir)
+		return -1;
+	while ((entry = readdir(dir))) {
+		char tail;
+		int candidate, fd;
+
+		if (sscanf(entry->d_name, "nbd%d%c", &candidate, &tail) != 1)
+			continue;
+		fd = open_unused(candidate);
+		if (fd < 0)
+			continue;
+		close(fd);
+		devices[nr_devices] = candidate;
+		if (++nr_devices >= MAX_DEVICES)
+			break;
+	}
+	closedir(dir);
+	return nr_devices ? devices[0] : -1;
+}
+
+int nbd_session_open(struct session *s, int index, int connections,
+		     unsigned long flags)
+{
+	int i;
+
+	memset(s, 0, sizeof(*s));
+	s->index = index;
+	s->fd = -1;
+	for (i = 0; i < 2; i++) {
+		s->sockets[i][0] = -1;
+		s->sockets[i][1] = -1;
+		s->go[i] = -1;
+		s->ready[i] = -1;
+		s->result[i] = -1;
+	}
+	s->fd = open_unused(index);
+	if (s->fd < 0) {
+		ksft_print_msg("nbd%d: exclusive open: %s\n", index,
+			       strerror(-s->fd));
+		return s->fd;
+	}
+	for (i = 0; i < 2; i++) {
+		if (socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0,
+			       s->sockets[i]))
+			return -errno;
+		if (i >= connections)
+			continue;
+		if (ioctl(s->fd, NBD_SET_SOCK, s->sockets
```
