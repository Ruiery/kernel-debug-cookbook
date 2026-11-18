---
title: [PATCH 5/5] zbd/008: skip if fio or hexdump is missing
list: linux-block
message_id: 20261118-skip-missing-deps-v1-5-a9b4a5a7cc94@suse.de
link: https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-5-a9b4a5a7cc94@suse.de/
---

# [PATCH 5/5] zbd/008: skip if fio or hexdump is missing

来源：[https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-5-a9b4a5a7cc94@suse.de/](https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-5-a9b4a5a7cc94@suse.de/)

```
zbd/008 runs fio and hexdump without checking for them. Check for them
in requires().

Fixes: a2737bbd421a ("zbd/008: check no stale page cache after BLKRESETZONE ioctl")
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 tests/zbd/008 | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/tests/zbd/008 b/tests/zbd/008
index cdfbedfd7976..480b3d55a122 100755
--- a/tests/zbd/008
+++ b/tests/zbd/008
@@ -15,7 +15,9 @@ TIMED=1
 requires() {
 	_have_loadable_scsi_debug
 	_have_module_param scsi_debug zbc
+	_have_fio
 	_have_program xfs_io
+	_have_program hexdump
 }
 
 test() {

-- 
2.56.1
```
