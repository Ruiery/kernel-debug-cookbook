---
title: [PATCH 4/5] block/009, block/012: skip if hexdump is missing
list: linux-block
message_id: 20261118-skip-missing-deps-v1-4-a9b4a5a7cc94@suse.de
link: https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-4-a9b4a5a7cc94@suse.de/
---

# [PATCH 4/5] block/009, block/012: skip if hexdump is missing

来源：[https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-4-a9b4a5a7cc94@suse.de/](https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-4-a9b4a5a7cc94@suse.de/)

```
block/009 and block/012 compare the device contents with hexdump, which
some distributions ship separately from util-linux, e.g. Debian in
bsdextrautils. Check for it in requires().

Fixes: 576668a4a6b1 ("add: Check page-cache coherency after BLKDISCARD")
Fixes: 3aeec46f048b ("block/012: add test for BLKROSET/BLKROGET ioctls")
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 tests/block/009 | 1 +
 tests/block/012 | 1 +
 2 files changed, 2 insertions(+)

diff --git a/tests/block/009 b/tests/block/009
index 8995646e5d21..1e3bc8ece8cf 100755
--- a/tests/block/009
+++ b/tests/block/009
@@ -14,6 +14,7 @@ DESCRIPTION="check page-cache coherency after BLKDISCARD"
 requires() {
 	_have_loadable_scsi_debug
 	_have_program xfs_io
+	_have_program hexdump
 }
 
 test() {
diff --git a/tests/block/012 b/tests/block/012
index c92f5b4b8dd2..430a3ac7f0b6 100755
--- a/tests/block/012
+++ b/tests/block/012
@@ -11,6 +11,7 @@ TIMED=1
 
 requires() {
 	_have_program xfs_io
+	_have_program hexdump
 }
 
 test_device() {

-- 
2.56.1
```
