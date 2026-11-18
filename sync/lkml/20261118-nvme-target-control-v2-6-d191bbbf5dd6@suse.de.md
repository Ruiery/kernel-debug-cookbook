---
title: [PATCH blktests v2 6/9] nvme: skip the DH-HMAC-CHAP algorithms the target doesn't support
list: linux-block
message_id: 20261118-nvme-target-control-v2-6-d191bbbf5dd6@suse.de
link: https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-6-d191bbbf5dd6@suse.de/
---

# [PATCH blktests v2 6/9] nvme: skip the DH-HMAC-CHAP algorithms the target doesn't support

来源：[https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-6-d191bbbf5dd6@suse.de/](https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-6-d191bbbf5dd6@suse.de/)

```
The authentication tests fail against a target that can't do
DH-HMAC-CHAP, and nvme/042 and nvme/043 fail on every hash or DH group
the target doesn't support.

Skip the authentication tests if the target doesn't list dhchap-sha256,
the hash every DH-HMAC-CHAP target supports, and skip just the steps of
nvme/042 and nvme/043 for the other algorithms the target doesn't list.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 Documentation/running-tests.md |  7 +++++--
 tests/nvme/041                 |  1 +
 tests/nvme/042                 |  3 ++-
 tests/nvme/043                 |  4 +++-
 tests/nvme/044                 |  2 +-
 tests/nvme/045                 |  2 +-
 tests/nvme/063                 |  2 +-
 tests/nvme/rc                  | 31 +++++++++++++++++++++++++------
 8 files changed, 39 insertions(+), 13 deletions(-)

diff --git a/Documentation/running-tests.md b/Documentation/running-tests.md
index b66bdf9cb2e8..d556f1d3b7cc 100644
--- a/Documentation/running-tests.md
+++ b/Documentation/running-tests.md
@@ -261,8 +261,11 @@ The blktests expects that the script interface implements following
   --subsysnqn SUBSYSNQN
 
 config --show-features prints the optional commands the script supports,
-e.g. add-port, set-ana or set-host, and tls if the target can set up TLS.
-blktests skips the tests which need a feature the list lacks.
+e.g. add-port, set-ana or set-host, the DH-HMAC-CHAP hashes and DH groups
+the target supports, e.g. dhchap-sha256 or dhchap-ffdhe2048, and tls if
+the target can set up TLS. blktests skips the tests which need a feature
+the list lacks: the authentication tests without dhchap-sha256, and
+nvme/042 and nvme/043 only the steps for the other missing algorithms.
 
 contrib/nvme-target-control implements this interface. It configures a Linux
 nvmet target over ssh and can be extended for other targets, see
diff --git a/tests/nvme/041 b/tests/nvme/041
index 9c3d9aaf4e12..2571c851be4d 100755
--- a/tests/nvme/041
+++ b/tests/nvme/041
@@ -16,6 +16,7 @@ requires() {
 	_require_kernel_nvme_fabrics_feature dhchap_ctrl_secret
 	_require_nvme_trtype_is_fabrics
 	_require_nvme_cli_auth
+	_require_nvme_target_control_feature dhchap-sha256
 }
 
 set_conditions() {
diff --git a/tests/nvme/042 b/tests/nvme/042
index e771cb6ca4aa..f9019e9640c4 100755
--- a/tests/nvme/042
+++ b/tests/nvme/042
@@ -16,7 +16,7 @@ requires() {
 	_require_kernel_nvme_fabrics_feature dhchap_ctrl_secret
 	_require_nvme_trtype_is_fabrics
 	_require_nvme_cli_auth
-	_require_nvme_target_control_feature set-host
+	_require_nvme_target_control_feature set-host dhchap-sha256
 }
 
 set_conditions() {
@@ -37,6 +37,7 @@ test() {
 
 	for hash in none sha256 sha384 sha512; do
 		echo "Testing hash ${hash}"
+		_have_nvme_target_dhchap "${hash}" || continue
 		hostkey="$(_nvme_gen_kxchap_secret --hash="${hash}" 2> /dev/null)"
 		if [ -z "$hostkey" ] ; then
 			echo "couldn't generate host key for hash ${hash}"
diff --git a/tests/nvme/043 b/tests/nvme/043
index eb8f8b035f6d..695edaab9741 100755
--- a/tests/nvme/043
+++ b/tests/nvme/043
@@ -17,7 +17,7 @@ requires() {
 	_require_nvme_trtype_is_fabrics
 	_require_nvme_cli_auth
 	_have_crypto_algorithm dh-generic
-	_require_nvme_target_control_feature set-host
+	_require_nvme_target_control_feature set-host dhchap-sha256
 }
 
 set_conditions() {
@@ -45,6 +45,7 @@ test() {
 	for hash in sha256 sha384 sha512; do
 
 		echo "Testing hash ${hash}"
+		_have_nvme_target_dhchap "${hash}" || continue
 
 		_set_nvmet_hash "${def_hostnqn}" "hmac(${hash})"
 
@@ -56,6 +57,7 @@ test() {
 	for dhgroup in ffdhe2048 ffdhe3072 ffdhe4096 ffdhe6144 ffdhe8192; do
 
 		echo "Testing DH group ${dhgroup}"
+		_have_nvme_target_dhchap "${dhgroup}" || continue
 
 		_set_nvmet_dhgroup "${def_hostnqn}" "${dhgroup}"
 
diff --git a/tests/nvme/044 b/tests/nvme/044
index c1a48f1e3d86..01a153e1f2a0 100755
--- a/tests/nvme/044
+++ b/tests/nvme/044
@@ -17,7 +17,7 @@ requires() {
 	_require_nvme_trtype_is_fabrics
 	_require_nvme_cli_auth
 	_have_crypto_algorithm dh-generic
-	_require_nvme_target_control_feature set-host
+	_require_nvme_target_control_feature set-host dhchap-sha256
 }
 
 set_conditions() {
diff --git a/tests/nvme/045 b/tests/nvme/045
index 14f4949e198e..52d04ce40860 100755
--- a/tests/nvme/045
+++ b/tests/nvme/045
@@ -18,7 +18,7 @@ requires() {
 	_require_nvme_trtype_is_fabrics
 	_require_nvme_cli_auth
 	_have_crypto_algorithm dh-generic
-	_require_nvme_target_control_feature set-host
+	_require_nvme_target_control_feature set-host dhchap-sha256
 }
 
 set_conditions() {
diff --git a/tests/nvme/063 b/tests/nvme/063
index 20aabd91ca80..578cb8799a6d 100755
--- a/tests/nvme/063
+++ b/tests/nvme/063
@@ -19,7 +19,7 @@ requires() {
 	_require_nvme_trtype tcp
 	_require_nvme_cli_auth
 	_have_systemd_tlshd_service
-	_require_nvme_target_control_feature set-host tls
+	_require_nvme_target_control_feature set-host tls dhchap-sha256
 }
 
 set_conditions() {
diff --git a/tests/nvme/rc b/tests/nvme/rc
index 41811c033069..0d74c427313c 100644
--- a/tests/nvme/rc
+++ b/tests/nvme/rc
@@ -155,18 +155,37 @@ _require_remote_nvme_target() {
 	return 0
 }
 
-# Skip the test if the NVME_TARGET_CONTROL target lacks one of the features,
-# the optional commands and e.g. tls, see Documentation/running-tests.md.
-_require_nvme_target_control_feature() {
-	local features feature
+# Check if the NVME_TARGET_CONTROL target lists the feature, one of the
+# optional commands or e.g. tls, see Documentation/running-tests.md. The
+# local target has all of them.
+_have_nvme_target_control_feature() {
+	local features
 
 	if [[ -z "${nvme_target_control}" ]]; then
 		return 0
 	fi
 	features=" $("${nvme_target_control}" config --show-features) "
+	# shellcheck disable=SC2076 # match the feature literally
+	[[ "${features}" =~ " $1 " ]]
+}
+
+# Check if the target supports the DH-HMAC-CHAP hash or DH group, e.g. sha384
+# or ffdhe2048, and log it if it doesn't. Every target which can do
+# DH-HMAC-CHAP supports sha256, a secret with hash none needs no support.
+_have_nvme_target_dhchap() {
+	if [[ "$1" == none ]] || _have_nvme_target_control_feature "dhchap-$1"; then
+		return 0
+	fi
+	echo "Target lacks $1, skipped" >> "$FULL"
+	return 1
+}
+
+# Skip the test if the NVME_TARGET_CONTROL target lacks one of the features.
+_require_nvme_target_control_feature() {
+	local feature
+
 	for feature in "$@"; do
-		# shellcheck disable=SC2076 # match the feature literally
-		if [[ ! "${features}" =~ " ${feature} " ]]; then
+		if ! _have_nvme_target_control_feature "${feature}"; then
 			SKIP_REASONS+=("NVME_TARGET_CONTROL target does not support ${feature}")
 			return 1
 		fi

-- 
2.56.1
```
