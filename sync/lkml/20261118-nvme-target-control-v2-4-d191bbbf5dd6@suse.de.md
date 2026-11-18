---
title: [PATCH blktests v2 4/9] nvme: skip tests that need a feature the remote target lacks
list: linux-block
message_id: 20261118-nvme-target-control-v2-4-d191bbbf5dd6@suse.de
link: https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-4-d191bbbf5dd6@suse.de/
---

# [PATCH blktests v2 4/9] nvme: skip tests that need a feature the remote target lacks

来源：[https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-4-d191bbbf5dd6@suse.de/](https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-4-d191bbbf5dd6@suse.de/)

```
A remote target does not have to implement the optional commands, e.g. a
storage array has fixed ports and manages the ANA state itself. Tests
that use a missing command fail instead of being skipped.

Add a _require_nvme_target_control_feature helper that checks the output
of "config --show-features", and use it in the tests that need ports,
ANA, host keys or TLS. No target lists tls yet, as blktests can't pass
a TLS key to the script.

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
 tests/nvme/rc                  | 19 +++++++++++++++++++
 10 files changed, 32 insertions(+)

diff --git a/Documentation/running-tests.md b/Documentation/running-tests.md
index 095d6aa4e18e..b66bdf9cb2e8 100644
--- a/Documentation/running-tests.md
+++ b/Documentation/running-tests.md
@@ -248,6 +248,7 @@ The blktests expects that the script interface implements following
   --show-trsvid
   --show-subsys-uuid
   --show-subsysnqn
+  --show-features
 
 setup:
   --subsysnqn SUBSYSNQN
@@ -259,6 +260,10 @@ The blktests expects that the script interface implements following
 cleanup:
   --subsysnqn SUBSYSNQN
 
+config --show-features prints the optional commands the script supports,
+e.g. add-port, set-ana or set-host, and tls if the target can set up TLS.
+blktests skips the tests which need a feature the list lacks.
+
 contrib/nvme-target-control implements this interface. It configures a Linux
 nvmet target over ssh and can be extended for other targets, see
 contrib/nvme-target-control/README.md.
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
index 7c558e287805..e771cb6ca4aa 100755
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
index f85916c842fe..eb8f8b035f6d 100755
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
index ff8e0ab90026..20aabd91ca80 100755
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
index 8abd14eeb112..41811c033069 100644
--- a/tests/nvme/rc
+++ b/tests/nvme/rc
@@ -155,6 +155,25 @@ _require_remote_nvme_target() {
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
+		# shellcheck disable=SC2076 # match the feature literally
+		if [[ ! "${features}" =~ " ${feature} " ]]; then
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
2.56.1
```
