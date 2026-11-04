---
title: [PATCH blktests 09/10] nvme: skip the tests which need a feature the remote target lacks
list: linux-block
message_id: 20261104-nvme-target-control-v1-9-b31b40537bb4@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-9-b31b40537bb4@suse.de/
---

# [PATCH blktests 09/10] nvme: skip the tests which need a feature the remote target lacks

来源：[https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-9-b31b40537bb4@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-9-b31b40537bb4@suse.de/)

```
An NVME_TARGET_CONTROL target need not implement the optional commands.
A storage array, for example, has fixed ports, manages the ANA states
itself and may not take host keys or a TLS key from blktests. The tests
which use a missing command then fail, e.g. nvme/057 on set-ana.

Add _require_nvme_target_control_feature, which checks the features
config --show-features lists. Use it in the tests which add and remove
ports (nvme/031), set ANA states (nvme/057), change host keys (nvme/042
to nvme/045, nvme/063) or set up TLS (nvme/062, nvme/063). No target
lists tls yet: blktests doesn't pass the TLS key to the script.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 Documentation/running-tests.md |  5 +++++
 tests/nvme/031                 |  1 +
 tests/nvme/042                 |  1 +
 tests/nvme/043                 |  1 +
 tests/nvme/044                 |  1 +
 tests/nvme/045                 |  1 +
 tests/nvme/057                 |  1 +
 tests/nvme/062                 |  1 +
 tests/nvme/063                 |  1 +
 tests/nvme/rc                  | 18 ++++++++++++++++++
 10 files changed, 31 insertions(+)

diff --git a/Documentation/running-tests.md b/Documentation/running-tests.md
index 847792cec240..9ac55f2c6724 100644
--- a/Documentation/running-tests.md
+++ b/Documentation/running-tests.md
@@ -248,6 +248,7 @@ The blktests expects that the script interface implements following
   --show-trsvid
   --show-subsys-uuid
   --show-subsysnqn
+  --show-features
 
 setup:
   --subsysnqn SUBSYSNQN
@@ -288,6 +289,10 @@ set-ana: set the state of an ANA group on the port
 
 If list-ports prints nothing, blktests connects to the address config shows.
 
+config --show-features prints the optional commands the script supports,
+add-ports to set-host, and tls if the target can set up TLS. blktests skips
+the tests which need a feature the list lacks.
+
 The authentication tests change the DH-CHAP attributes of the host:
 
 set-host:
diff --git a/tests/nvme/031 b/tests/nvme/031
index cd69e8ef13ac..b12e24489740 100755
--- a/tests/nvme/031
+++ b/tests/nvme/031
@@ -21,6 +21,7 @@ requires() {
 	_nvme_requires
 	_have_loop
 	_require_nvme_trtype_is_fabrics
+	_require_nvme_target_control_feature add-port remove-port
 }
 
 set_conditions() {
diff --git a/tests/nvme/042 b/tests/nvme/042
index bddbd1bbfc28..7ddc0e91706e 100755
--- a/tests/nvme/042
+++ b/tests/nvme/042
@@ -16,6 +16,7 @@ requires() {
 	_require_kernel_nvme_fabrics_feature dhchap_ctrl_secret
 	_require_nvme_trtype_is_fabrics
 	_require_nvme_cli_auth
+	_require_nvme_target_control_feature set-host
 }
 
 set_conditions() {
diff --git a/tests/nvme/043 b/tests/nvme/043
index ac25610a402b..f3b8d640891a 100755
--- a/tests/nvme/043
+++ b/tests/nvme/043
@@ -17,6 +17,7 @@ requires() {
 	_require_nvme_trtype_is_fabrics
 	_require_nvme_cli_auth
 	_have_crypto_algorithm dh-generic
+	_require_nvme_target_control_feature set-host
 }
 
 set_conditions() {
diff --git a/tests/nvme/044 b/tests/nvme/044
index 1d9202143cf4..c1a48f1e3d86 100755
--- a/tests/nvme/044
+++ b/tests/nvme/044
@@ -17,6 +17,7 @@ requires() {
 	_require_nvme_trtype_is_fabrics
 	_require_nvme_cli_auth
 	_have_crypto_algorithm dh-generic
+	_require_nvme_target_control_feature set-host
 }
 
 set_conditions() {
diff --git a/tests/nvme/045 b/tests/nvme/045
index 78a1c607e9c6..14f4949e198e 100755
--- a/tests/nvme/045
+++ b/tests/nvme/045
@@ -18,6 +18,7 @@ requires() {
 	_require_nvme_trtype_is_fabrics
 	_require_nvme_cli_auth
 	_have_crypto_algorithm dh-generic
+	_require_nvme_target_control_feature set-host
 }
 
 set_conditions() {
diff --git a/tests/nvme/057 b/tests/nvme/057
index 0a5cfa4df1a8..6c45af8b5ed9 100755
--- a/tests/nvme/057
+++ b/tests/nvme/057
@@ -13,6 +13,7 @@ requires() {
 	_have_loop
 	_have_fio
 	_require_nvme_trtype_is_fabrics
+	_require_nvme_target_control_feature list-ports show-port set-ana
 }
 
 set_conditions() {
diff --git a/tests/nvme/062 b/tests/nvme/062
index eabe2d99bdcc..4402b848ecee 100755
--- a/tests/nvme/062
+++ b/tests/nvme/062
@@ -18,6 +18,7 @@ requires() {
 	_require_nvme_cli_tls
 	_have_libnvme_ver 1 11
 	_have_systemd_tlshd_service
+	_require_nvme_target_control_feature tls
 }
 
 set_conditions() {
diff --git a/tests/nvme/063 b/tests/nvme/063
index feb07bf3a06c..fae1e8941136 100755
--- a/tests/nvme/063
+++ b/tests/nvme/063
@@ -19,6 +19,7 @@ requires() {
 	_require_nvme_trtype tcp
 	_require_nvme_cli_auth
 	_have_systemd_tlshd_service
+	_require_nvme_target_control_feature set-host tls
 }
 
 set_conditions() {
diff --git a/tests/nvme/rc b/tests/nvme/rc
index 3c3ed680e416..6bdd4058586a 100644
--- a/tests/nvme/rc
+++ b/tests/nvme/rc
@@ -155,6 +155,24 @@ _require_remote_nvme_target() {
 	return 0
 }
 
+# Skip the test if the NVME_TARGET_CONTROL target lacks one of the features,
+# the optional commands and e.g. tls, see Documentation/running-tests.md.
+_require_nvme_target_control_feature() {
+	local features feature
+
+	if [[ -z "${nvme_target_control}" ]]; then
+		return 0
+	fi
+	features=" $("${nvme_target_control}" config --show-features) "
+	for feature in "$@"; do
+		if [[ "${features}" != *" ${feature} "* ]]; then
+			SKIP_REASONS+=("NVME_TARGET_CONTROL target does not support ${feature}")
+			return 1
+		fi
+	done
+	return 0
+}
+
 _test_dev_nvme_ctrl() {
 	echo "/dev/char/$(cat "${TEST_DEV_SYSFS}/device/dev")"
 }

-- 
2.56.0
```
