---
title: [PATCH blktests 04/10] nvme: skip the tests which need the kernel target with a remote target
list: linux-block
message_id: 20261104-nvme-target-control-v1-4-b31b40537bb4@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-4-b31b40537bb4@suse.de/
---

# [PATCH blktests 04/10] nvme: skip the tests which need the kernel target with a remote target

来源：[https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-4-b31b40537bb4@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-4-b31b40537bb4@suse.de/)

```
nvme/038, nvme/051, nvme/058, nvme/060 and nvme/065 work on the local
nvmet target directly. nvme/038 creates and removes a subsystem in the
local configfs. nvme/051 enables and disables the namespace in the local
configfs. nvme/058 creates its namespaces there. nvme/060 reads the
nvmet debugfs. nvme/065 exports a local scsi_debug device. With
NVME_TARGET_CONTROL the subsystem is on the remote target and the tests
fail.

Skip them with _require_kernel_nvme_target, as nvme/030 and
nvme/072-074 do.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 tests/nvme/038 | 1 +
 tests/nvme/051 | 1 +
 tests/nvme/058 | 1 +
 tests/nvme/060 | 1 +
 tests/nvme/065 | 1 +
 5 files changed, 5 insertions(+)

diff --git a/tests/nvme/038 b/tests/nvme/038
index 4271ee3af951..a5dcdeda14aa 100755
--- a/tests/nvme/038
+++ b/tests/nvme/038
@@ -16,6 +16,7 @@ QUICK=1
 
 requires() {
 	_nvme_requires
+	_require_kernel_nvme_target
 }
 
 set_conditions() {
diff --git a/tests/nvme/051 b/tests/nvme/051
index 8b3bb2b592a5..c5a37af31515 100755
--- a/tests/nvme/051
+++ b/tests/nvme/051
@@ -13,6 +13,7 @@ QUICK=1
 requires() {
 	_nvme_requires
 	_require_nvme_trtype_is_fabrics
+	_require_kernel_nvme_target
 }
 
 set_conditions() {
diff --git a/tests/nvme/058 b/tests/nvme/058
index 997ff7f87be3..a410cf728c52 100755
--- a/tests/nvme/058
+++ b/tests/nvme/058
@@ -12,6 +12,7 @@ requires() {
 	_nvme_requires
 	_have_loop
 	_require_nvme_trtype_is_fabrics
+	_require_kernel_nvme_target
 }
 
 set_conditions() {
diff --git a/tests/nvme/060 b/tests/nvme/060
index 49786afba8cb..4c5fa8c31648 100755
--- a/tests/nvme/060
+++ b/tests/nvme/060
@@ -13,6 +13,7 @@ requires() {
 	_have_loop
 	_require_nvme_trtype tcp rdma fc
 	_have_kernel_option NVME_TARGET_DEBUGFS
+	_require_kernel_nvme_target
 }
 
 set_conditions() {
diff --git a/tests/nvme/065 b/tests/nvme/065
index e878001efbdd..05480f3072fd 100755
--- a/tests/nvme/065
+++ b/tests/nvme/065
@@ -17,6 +17,7 @@ requires() {
 	_have_scsi_debug
 	_nvme_requires
 	_require_nvme_trtype_is_fabrics
+	_require_kernel_nvme_target
 }
 
 set_conditions() {

-- 
2.56.0
```
