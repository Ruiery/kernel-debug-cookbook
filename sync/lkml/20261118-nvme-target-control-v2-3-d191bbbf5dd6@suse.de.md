---
title: [PATCH blktests v2 3/9] nvme/042, nvme/043: iterate over the DH-HMAC-CHAP hashes by name
list: linux-block
message_id: 20261118-nvme-target-control-v2-3-d191bbbf5dd6@suse.de
link: https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-3-d191bbbf5dd6@suse.de/
---

# [PATCH blktests v2 3/9] nvme/042, nvme/043: iterate over the DH-HMAC-CHAP hashes by name

来源：[https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-3-d191bbbf5dd6@suse.de/](https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-3-d191bbbf5dd6@suse.de/)

```
nvme/042 iterates over the numeric hash IDs nvme-cli takes, nvme/043
over the hash names of the nvmet configfs. Add a --hash option to
_nvme_gen_kxchap_secret which takes the hash name, and use the plain
names in both tests, and in nvme/063.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 common/nvme        | 18 ++++++++++++++++++
 tests/nvme/042     | 10 +++++-----
 tests/nvme/042.out |  8 ++++----
 tests/nvme/043     |  6 +++---
 tests/nvme/043.out |  6 +++---
 tests/nvme/063     |  4 ++--
 6 files changed, 35 insertions(+), 17 deletions(-)

diff --git a/common/nvme b/common/nvme
index dfe85b6e281f..6fba3890b6ce 100644
--- a/common/nvme
+++ b/common/nvme
@@ -168,9 +168,27 @@ _nvme_run() {
 	nvme $(_nvme_cmd "$current") "$@"
 }
 
+# Generate a DH-HMAC-CHAP secret. --hash=HASH transforms the secret with HASH:
+# none, sha256, sha384 or sha512. The other arguments go to nvme-cli.
 _nvme_gen_kxchap_secret() {
+	local -a secret_args=()
+	local -A hmac_ids=([none]=0 [sha256]=1 [sha384]=2 [sha512]=3)
+
 	_nvme_cli_detect_version
 
+	while (($#)); do
+		case "$1" in
+		--hash=*)
+			secret_args+=("--hmac=${hmac_ids[${1#--hash=}]}")
+			;;
+		*)
+			secret_args+=("$1")
+			;;
+		esac
+		shift
+	done
+	set -- "${secret_args[@]}"
+
 	if ((!_is_nvme_cli_pre_v3)); then
 		local -a kxchap_args=()
 
diff --git a/tests/nvme/042 b/tests/nvme/042
index bddbd1bbfc28..7c558e287805 100755
--- a/tests/nvme/042
+++ b/tests/nvme/042
@@ -27,18 +27,18 @@ test() {
 
 	_setup_nvmet
 
-	local hmac
+	local hash
 	local key_len
 	local hostkey
 	local ctrldev
 
 	_nvmet_target_setup --blkdev file
 
-	for hmac in 0 1 2 3; do
-		echo "Testing hmac ${hmac}"
-		hostkey="$(_nvme_gen_kxchap_secret --hmac=${hmac} 2> /dev/null)"
+	for hash in none sha256 sha384 sha512; do
+		echo "Testing hash ${hash}"
+		hostkey="$(_nvme_gen_kxchap_secret --hash="${hash}" 2> /dev/null)"
 		if [ -z "$hostkey" ] ; then
-			echo "couldn't generate host key for hmac ${hmac}"
+			echo "couldn't generate host key for hash ${hash}"
 			return 1
 		fi
 		_set_nvmet_hostkey "${def_hostnqn}" "${hostkey}"
diff --git a/tests/nvme/042.out b/tests/nvme/042.out
index 1c3fc6130696..9a9fc697b4f5 100644
--- a/tests/nvme/042.out
+++ b/tests/nvme/042.out
@@ -1,8 +1,8 @@
 Running nvme/042
-Testing hmac 0
-Testing hmac 1
-Testing hmac 2
-Testing hmac 3
+Testing hash none
+Testing hash sha256
+Testing hash sha384
+Testing hash sha512
 Testing key length 32
 Testing key length 48
 Testing key length 64
diff --git a/tests/nvme/043 b/tests/nvme/043
index ac25610a402b..f85916c842fe 100755
--- a/tests/nvme/043
+++ b/tests/nvme/043
@@ -41,18 +41,18 @@ test() {
 
 	_nvmet_target_setup --blkdev file --hostkey "${hostkey}"
 
-	for hash in "hmac(sha256)" "hmac(sha384)" "hmac(sha512)" ; do
+	for hash in sha256 sha384 sha512; do
 
 		echo "Testing hash ${hash}"
 
-		_set_nvmet_hash "${def_hostnqn}" "${hash}"
+		_set_nvmet_hash "${def_hostnqn}" "hmac(${hash})"
 
 		_nvme_connect_subsys --dhchap-secret "${hostkey}"
 
 		_nvme_disconnect_subsys
 	done
 
-	for dhgroup in "ffdhe2048" "ffdhe3072" "ffdhe4096" "ffdhe6144" "ffdhe8192" ; do
+	for dhgroup in ffdhe2048 ffdhe3072 ffdhe4096 ffdhe6144 ffdhe8192; do
 
 		echo "Testing DH group ${dhgroup}"
 
diff --git a/tests/nvme/043.out b/tests/nvme/043.out
index f3f55a4449b6..c99949489070 100644
--- a/tests/nvme/043.out
+++ b/tests/nvme/043.out
@@ -1,7 +1,7 @@
 Running nvme/043
-Testing hash hmac(sha256)
-Testing hash hmac(sha384)
-Testing hash hmac(sha512)
+Testing hash sha256
+Testing hash sha384
+Testing hash sha512
 Testing DH group ffdhe2048
 Testing DH group ffdhe3072
 Testing DH group ffdhe4096
diff --git a/tests/nvme/063 b/tests/nvme/063
index feb07bf3a06c..ff8e0ab90026 100755
--- a/tests/nvme/063
+++ b/tests/nvme/063
@@ -34,7 +34,7 @@ test() {
 
 	_systemctl_start tlshd
 
-	hostkey=$(_nvme_gen_kxchap_secret --hmac 1 2> /dev/null)
+	hostkey=$(_nvme_gen_kxchap_secret --hash=sha256 2> /dev/null)
 	if [ -z "$hostkey" ] ; then
 		echo "key generation failed"
 		_systemctl_stop
@@ -76,7 +76,7 @@ test() {
 
 	_nvme_disconnect_subsys
 
-	hostkey=$(_nvme_gen_kxchap_secret --hmac 2 2> /dev/null)
+	hostkey=$(_nvme_gen_kxchap_secret --hash=sha384 2> /dev/null)
 	if [ -z "$hostkey" ] ; then
 		echo "key generation failed"
 		_systemctl_stop

-- 
2.56.1
```
