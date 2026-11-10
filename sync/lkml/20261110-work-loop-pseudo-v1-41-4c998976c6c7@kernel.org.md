---
title: [PATCH RFC 41/41] selftests/filesystems: add backing file tests for pseudo files
list: linux-block
message_id: 20261110-work-loop-pseudo-v1-41-4c998976c6c7@kernel.org
link: https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-41-4c998976c6c7@kernel.org/
---

# [PATCH RFC 41/41] selftests/filesystems: add backing file tests for pseudo files

来源：[https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-41-4c998976c6c7@kernel.org/](https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-41-4c998976c6c7@kernel.org/)

```
Add tests that files on pseudo filesystems can't be used as storage:

- a procfs file attached read-only to a loop device
- sysfs files attached read-only and read-write to a loop device
- a sysfs file behind a lower-only overlayfs attached to a loop device
- a sysfs file as the backing file of a usb mass storage gadget LUN
- a sysfs file as the source of a file-backed erofs mount

And make sure that a memfd and another loop device still work as loop
backing files and that loop refuses a backing file that isn't open for
reading.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 tools/testing/selftests/filesystems/.gitignore     |   1 +
 tools/testing/selftests/filesystems/Makefile       |   2 +-
 tools/testing/selftests/filesystems/config         |   9 +
 .../selftests/filesystems/pseudo_backing_test.c    | 274 +++++++++++++++++++++
 4 files changed, 285 insertions(+), 1 deletion(-)

diff --git a/tools/testing/selftests/filesystems/.gitignore b/tools/testing/selftests/filesystems/.gitignore
index cf79000e4092..8df38eabb125 100644
--- a/tools/testing/selftests/filesystems/.gitignore
+++ b/tools/testing/selftests/filesystems/.gitignore
@@ -7,3 +7,4 @@ kernfs_test
 idmapped_tmpfile
 ustat_test
 rw_hint_test
+pseudo_backing_test
diff --git a/tools/testing/selftests/filesystems/Makefile b/tools/testing/selftests/filesystems/Makefile
index fbd5c27505ef..0ebb9005bcd2 100644
--- a/tools/testing/selftests/filesystems/Makefile
+++ b/tools/testing/selftests/filesystems/Makefile
@@ -2,7 +2,7 @@
 
 CFLAGS += $(KHDR_INCLUDES)
 TEST_GEN_PROGS := devpts_pts anon_inode_test kernfs_test fclog ustat_test rw_hint_test
-TEST_GEN_PROGS += idmapped_tmpfile
+TEST_GEN_PROGS += idmapped_tmpfile pseudo_backing_test
 TEST_GEN_PROGS_EXTENDED := dnotify_test
 
 include ../lib.mk
diff --git a/tools/testing/selftests/filesystems/config b/tools/testing/selftests/filesystems/config
index 9f45bc493a30..228196160d29 100644
--- a/tools/testing/selftests/filesystems/config
+++ b/tools/testing/selftests/filesystems/config
@@ -6,3 +6,12 @@ CONFIG_NET=y
 CONFIG_NET_NS=y
 CONFIG_INET=y
 CONFIG_SYSFS=y
+CONFIG_BLK_DEV_LOOP=y
+CONFIG_OVERLAY_FS=y
+CONFIG_TMPFS=y
+CONFIG_CONFIGFS_FS=y
+CONFIG_USB_GADGET=y
+CONFIG_USB_CONFIGFS=y
+CONFIG_USB_CONFIGFS_MASS_STORAGE=y
+CONFIG_EROFS_FS=y
+CONFIG_EROFS_FS_BACKED_BY_FILE=y
diff --git a/tools/testing/selftests/filesystems/pseudo_backing_test.c b/tools/testing/selftests/filesystems/pseudo_backing_test.c
new file mode 100644
index 000000000000..bc8e17ab8e6e
--- /dev/null
+++ b/tools/testing/selftests/filesystems/pseudo_backing_test.c
@@ -0,0 +1,274 @@
+// SPDX-License-Identifier: GPL-2.0
+#define _GNU_SOURCE
+
+#include <errno.h>
+#include <fcntl.h>
+#include <limits.h>
+#include <sched.h>
+#include <stdbool.h>
+#include <stdio.h>
+#include <stdlib.h>
+#include <string.h>
+#include <unistd.h>
+#include <linux/loop.h>
+#include <linux/magic.h>
+#include <sys/ioctl.h>
+#include <sys/mman.h>
+#include <sys/mount.h>
+#include <sys/stat.h>
+#include <sys/vfs.h>
+
+#include "kselftest_harness.h"
+#include "wrappers.h"
+
+/*
+ * Put @fd behind a free loop device. The device is set up with
+ * LO_FLAGS_AUTOCLEAR and goes away again when it is closed here.
+ */
+static int loop_attach(int fd, bool rw, char *dev, size_t len)
+{
+	struct loop_config cfg = {};
+	int ctl, nr, lfd, ret = 0;
+
+	ctl = open("/dev/loop-control", O_RDWR | O_CLOEXEC);
+	if (ctl < 0)
+		return -errno;
+	nr = ioctl(ctl, LOOP_CTL_GET_FREE);
+	if (nr < 0)
+		ret = -errno;
+	close(ctl);
+	if (ret)
+		return ret;
+
+	snprintf(dev, len, "/dev/loop%d", nr);
+	lfd = open(dev, (rw ? O_RDWR : O_RDONLY) | O_CLOEXEC);
+	if (lfd < 0)
+		return -errno;
+
+	cfg.fd = fd;
+	cfg.info.lo_flags = LO_FLAGS_AUTOCLEAR;
+	if (!rw)
+		cfg.info.lo_flags |= LO_FLAGS_READ_ONLY;
+	if (ioctl(lfd, LOOP_CONFIGURE, &cfg)) {
+		ret = -errno;
+		close(lfd);
+	} else {
+		ret = lfd;
+	}
+	return ret;
+}
+
+static int attach_path(const char *path, bool rw)
+{
+	char dev[PATH_MAX];
+	int fd, ret;
+
+	fd = open(path, (rw ? O_RDWR : O_RDONLY) | O_CLOEXEC);
+	if (fd < 0)
+		return -errno;
+	ret = loop_attach(fd, rw, dev, sizeof(dev));
+	close(fd);
+	if (ret >= 0) {
+		close(ret);
+		ret = 0;
+	}
+	return ret;
+}
+
+static bool can_use_loop(void)
+{
+	return geteuid() == 0 && access("/dev/loop-control", R_OK | W_OK) == 0;
+}
+
+TEST(memfd_backing_file)
+{
+	char dev[PATH_MAX];
+	int fd, lfd;
+
+	if (!can_use_loop())
+		SKIP(return, "loop devices unavailable");
+
+	fd = memfd_create("pseudo_backing_test", MFD_CLOEXEC);
+	ASSERT_GE(fd, 0);
+	ASSERT_EQ(ftruncate(fd, 1 << 20), 0);
+
+	lfd = loop_attach(fd, true, dev, sizeof(dev));
+	ASSERT_GE(lfd, 0);
+	EXPECT_EQ(close(lfd), 0);
+	EXPECT_EQ(close(fd), 0);
+}
+
+TEST(loop_device_backing_file)
+{
+	char dev[PATH_MAX], dev2[PATH_MAX];
+	int fd, lfd, bfd, lfd2;
+
+	if (!can_use_loop())
+		SKIP(return, "loop devices unavailable");
+
+	fd = memfd_create("pseudo_backing_test", MFD_CLOEXEC);
+	ASSERT_GE(fd, 0);
+	ASSERT_EQ(ftruncate(fd, 1 << 20), 0);
+	lfd = loop_attach(fd, true, dev, sizeof(dev));
+	ASSERT_GE(lfd, 0);
+
+	/* A block device stays fine as a backing file. */
+	bfd = open(dev, O_RDWR | O_CLOEXEC);
+	ASSERT_GE(bfd, 0);
+	lfd2 = loop_attach(bfd, true, dev2, sizeof(dev2));
+	ASSERT_GE(lfd2, 0);
+
+	EXPECT_EQ(close(lfd2), 0);
+	EXPECT_EQ(close(bfd), 0);
+	EXPECT_EQ(close(lfd), 0);
+	EXPECT_EQ(close(fd), 0);
+}
+
+TEST(write_only_backing_file)
+{
+	char dev[PATH_MAX], path[PATH_MAX];
+	int fd, wfd, lfd;
+
+	if (!can_use_loop())
+		SKIP(return, "loop devices unavailable");
+
+	fd = memfd_create("pseudo_backing_test", MFD_CLOEXEC);
+	ASSERT_GE(fd, 0);
+	ASSERT_EQ(ftruncate(fd, 1 << 20), 0);
+
+	/* Loop reads from its backing file so it must be open for reading. */
+	snprintf(path, sizeof(path), "/proc/self/fd/%d", fd);
+	wfd = open(path, O_WRONLY | O_CLOEXEC);
+	ASSERT_GE(wfd, 0);
+
+	lfd = loop_attach(wfd, true, dev, sizeof(dev));
+	if (lfd >= 0)
+		close(lfd);
+	EXPECT_EQ(lfd, -EBADF);
+	EXPECT_EQ(close(wfd), 0);
+	EXPECT_EQ(close(fd), 0);
+}
+
+TEST(procfs_backing_file)
+{
+	if (!can_use_loop())
+		SKIP(return, "loop devices unavailable");
+
+	ASSERT_EQ(attach_path("/proc/cpuinfo", false), -EINVAL);
+}
+
+TEST(sysfs_backing_file)
+{
+	if (!can_use_loop())
+		SKIP(return, "loop devices unavailable");
+
+	ASSERT_EQ(attach_path("/sys/kernel/warn_count", false), -EINVAL);
+
+	if (access("/sys/kernel/reboot/mode", F_OK))
+		SKIP(return, "no /sys/kernel/reboot/mode");
+	ASSERT_EQ(attach_path("/sys/kernel/reboot/mode", true), -EINVAL);
+}
+
+TEST(overlayfs_on_sysfs_backing_file)
+{
+	if (!can_use_loop())
+		SKIP(return, "loop devices unavailable");
+
+	ASSERT_EQ(unshare(CLONE_NEWNS), 0);
+	ASSERT_EQ(mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL), 0);
+	ASSERT_EQ(mount("tmpfs", "/tmp", "tmpfs", 0, NULL), 0);
+	ASSERT_EQ(mkdir("/tmp/empty", 0755), 0);
+	ASSERT_EQ(mkdir("/tmp/merged", 0755), 0);
+
+	/* A lower-only overlayfs serves reads from sysfs. */
+	if (mount("overlay", "/tmp/merged", "overlay", MS_RDONLY,
+		  "lowerdir=/sys/kernel:/tmp/empty"))
+		SKIP(return, "no overlayfs on top of sysfs: %s", strerror(errno));
+
+	ASSERT_EQ(attach_path("/tmp/merged/warn_count", false), -EINVAL);
+}
+
+#define CONFIGFS_DIR "/sys/kernel/config"
+#define GADGET_DIR CONFIGFS_DIR "/usb_gadget/pseudo_backing_test"
+#define MASS_STORAGE_DIR GADGET_DIR "/functions/mass_storage.0"
+
+TEST(usb_mass_storage_backing_file)
+{
+	const char *path = "/sys/kernel/warn_count";
+	struct statfs sfs;
+	ssize_t ret;
+	int fd, err;
+
+	if (geteuid())
+		SKIP(return, "needs root");
+
+	/* Mounting configfs on top of itself fails with EBUSY. */
+	if (statfs(CONFIGFS_DIR, &sfs) || sfs.f_type != CONFIGFS_MAGIC) {
+		ASSERT_EQ(unshare(CLONE_NEWNS), 0);
+		ASSERT_EQ(mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL), 0);
+		if (mount("configfs", CONFIGFS_DIR, "configfs", 0, NULL))
+			SKIP(return, "no configfs: %s", strerror(errno));
+	}
+
+	if (mkdir(GADGET_DIR, 0755))
+		SKIP(return, "no usb gadget conf
```
