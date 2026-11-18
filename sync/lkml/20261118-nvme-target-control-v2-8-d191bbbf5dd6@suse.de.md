---
title: [PATCH blktests v2 8/9] nvme/rc: change the host keys on a remote target
list: linux-block
message_id: 20261118-nvme-target-control-v2-8-d191bbbf5dd6@suse.de
link: https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-8-d191bbbf5dd6@suse.de/
---

# [PATCH blktests v2 8/9] nvme/rc: change the host keys on a remote target

来源：[https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-8-d191bbbf5dd6@suse.de/](https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-8-d191bbbf5dd6@suse.de/)

```
The helpers that change the DH-CHAP settings of the host write to the
local nvmet configfs, so a remote target never sees the new values. Use
the set-host command of the target control script instead and document
it.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 Documentation/running-tests.md |  9 +++++++++
 tests/nvme/rc                  | 20 ++++++++++++++++++++
 2 files changed, 29 insertions(+)

diff --git a/Documentation/running-tests.md b/Documentation/running-tests.md
index 8300d9aa4842..149b3656d7c8 100644
--- a/Documentation/running-tests.md
+++ b/Documentation/running-tests.md
@@ -296,6 +296,15 @@ set-ana: set the state of an ANA group on the port
 
 If list-ports prints nothing, blktests connects to the address config shows.
 
+The authentication tests change the DH-CHAP attributes of the host:
+
+set-host:
+  --hostnqn HOSTNQN
+  --hostkey HOSTKEY
+  --ctrlkey CTRLKEY
+  --hash HASH
+  --dhgroup DHGROUP
+
 contrib/nvme-target-control implements this interface. It configures a Linux
 nvmet target over ssh and can be extended for other targets, see
 contrib/nvme-target-control/README.md.
diff --git a/tests/nvme/rc b/tests/nvme/rc
index 0d74c427313c..47710efc5096 100644
--- a/tests/nvme/rc
+++ b/tests/nvme/rc
@@ -285,6 +285,11 @@ _set_nvmet_hostkey() {
 	local nvmet_hostkey="$2"
 	local cfs_path="${NVMET_CFS}/hosts/${nvmet_hostnqn}"
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		"${nvme_target_control}" set-host --hostnqn "${nvmet_hostnqn}" \
+			--hostkey "${nvmet_hostkey}"
+		return
+	fi
 	_set_attr "${nvmet_hostkey}" "${cfs_path}/dhchap_key"
 }
 
@@ -293,6 +298,11 @@ _set_nvmet_ctrlkey() {
 	local nvmet_ctrlkey="$2"
 	local cfs_path="${NVMET_CFS}/hosts/${nvmet_hostnqn}"
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		"${nvme_target_control}" set-host --hostnqn "${nvmet_hostnqn}" \
+			--ctrlkey "${nvmet_ctrlkey}"
+		return
+	fi
 	_set_attr "${nvmet_ctrlkey}" "${cfs_path}/dhchap_ctrl_key"
 }
 
@@ -301,6 +311,11 @@ _set_nvmet_hash() {
 	local nvmet_hash="$2"
 	local cfs_path="${NVMET_CFS}/hosts/${nvmet_hostnqn}"
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		"${nvme_target_control}" set-host --hostnqn "${nvmet_hostnqn}" \
+			--hash "${nvmet_hash}"
+		return
+	fi
 	_set_attr "${nvmet_hash}" "${cfs_path}/dhchap_hash"
 }
 
@@ -309,6 +324,11 @@ _set_nvmet_dhgroup() {
 	local nvmet_dhgroup="$2"
 	local cfs_path="${NVMET_CFS}/hosts/${nvmet_hostnqn}"
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		"${nvme_target_control}" set-host --hostnqn "${nvmet_hostnqn}" \
+			--dhgroup "${nvmet_dhgroup}"
+		return
+	fi
 	_set_attr "${nvmet_dhgroup}" "${cfs_path}/dhchap_dhgroup"
 }
 

-- 
2.56.1
```
