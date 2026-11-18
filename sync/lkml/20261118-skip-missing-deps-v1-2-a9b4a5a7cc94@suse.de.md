---
title: [PATCH 2/5] nvme/053, nvme/068: skip if fio or xfs_io is missing
list: linux-block
message_id: 20261118-skip-missing-deps-v1-2-a9b4a5a7cc94@suse.de
link: https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-2-a9b4a5a7cc94@suse.de/
---

# [PATCH 2/5] nvme/053, nvme/068: skip if fio or xfs_io is missing

来源：[https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-2-a9b4a5a7cc94@suse.de/](https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-2-a9b4a5a7cc94@suse.de/)

```
nvme/053 runs fio and nvme/068 runs xfs_io without checking for them, so
they fail instead of being skipped on a host without the tools. Check
for them in requires().

Fixes: ed9b60a05a3f ("nvme: add test for controller rescan under I/O load")
Fixes: ca59dfcce4ef ("nvme/068: add a test for multipath delayed removal")
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 tests/nvme/053 | 4 ++++
 tests/nvme/068 | 1 +
 2 files changed, 5 insertions(+)

diff --git a/tests/nvme/053 b/tests/nvme/053
index 99dbd3880edd..255cff177c0f 100755
--- a/tests/nvme/053
+++ b/tests/nvme/053
@@ -12,6 +12,10 @@ DESCRIPTION="test controller rescan under I/O load"
 TIMED=1
 : "${TIMEOUT:=60}"
 
+requires() {
+	_have_fio
+}
+
 get_sleep_time() {
 	local duration=$((RANDOM % 50 + 1))
 
diff --git a/tests/nvme/068 b/tests/nvme/068
index cab57cd62969..b9d28a50d03e 100755
--- a/tests/nvme/068
+++ b/tests/nvme/068
@@ -15,6 +15,7 @@ requires() {
 	_nvme_requires
 	_have_loop
 	_have_module_param_value nvme_core multipath Y
+	_have_program xfs_io
 	_require_nvme_trtype_is_fabrics
 }
 

-- 
2.56.1
```
