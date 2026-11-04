---
title: [PATCH blktests 08/10] nvme/rc: change the host keys on a remote target
list: linux-block
message_id: 20261104-nvme-target-control-v1-8-b31b40537bb4@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-8-b31b40537bb4@suse.de/
---

# [PATCH blktests 08/10] nvme/rc: change the host keys on a remote target

来源：[https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-8-b31b40537bb4@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-8-b31b40537bb4@suse.de/)

```
The authentication tests change the DH-CHAP keys, hash and DH group of
the host with _set_nvmet_hostkey, _set_nvmet_ctrlkey, _set_nvmet_hash
and _set_nvmet_dhgroup. They write to the local nvmet configfs. With
NVME_TARGET_CONTROL the host is configured on the remote target, the
writes fail and the target keeps the old values. nvme/042 to nvme/045
fail on the write errors. nvme/045 renews the keys and changes the DH
group, and the re-authentication with the new values fails.

Change the values on the target with the set-host command of the
script. Document the command in running-tests.md.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 Documentation/running-tests.md |  9 +++++++++
 tests/nvme/rc                  | 20 ++++++++++++++++++++
 2 files changed, 29 insertions(+)

diff --git a/Documentation/running-tests.md b/Documentation/running-tests.md
index 9ca01e6893ec..847792cec240 100644
--- a/Documentation/running-tests.md
+++ b/Documentation/running-tests.md
@@ -288,6 +288,15 @@ set-ana: set the state of an ANA group on the port
 
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
index 8abd14eeb112..3c3ed680e416 100644
--- a/tests/nvme/rc
+++ b/tests/nvme/rc
@@ -247,6 +247,11 @@ _set_nvmet_hostkey() {
 	local nvmet_hostkey="$2"
 	local cfs_path="${NVMET_CFS}/hosts/${nvmet_hostnqn}"
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		"${nvme_target_control}" set-host --hostnqn "${nvmet_hostnqn}" \
+			--hostkey "${nvmet_hostkey}"
+		return
+	fi
 	_set_attr "${nvmet_hostkey}" "${cfs_path}/dhchap_key"
 }
 
@@ -255,6 +260,11 @@ _set_nvmet_ctrlkey() {
 	local nvmet_ctrlkey="$2"
 	local cfs_path="${NVMET_CFS}/hosts/${nvmet_hostnqn}"
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		"${nvme_target_control}" set-host --hostnqn "${nvmet_hostnqn}" \
+			--ctrlkey "${nvmet_ctrlkey}"
+		return
+	fi
 	_set_attr "${nvmet_ctrlkey}" "${cfs_path}/dhchap_ctrl_key"
 }
 
@@ -263,6 +273,11 @@ _set_nvmet_hash() {
 	local nvmet_hash="$2"
 	local cfs_path="${NVMET_CFS}/hosts/${nvmet_hostnqn}"
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		"${nvme_target_control}" set-host --hostnqn "${nvmet_hostnqn}" \
+			--hash "${nvmet_hash}"
+		return
+	fi
 	_set_attr "${nvmet_hash}" "${cfs_path}/dhchap_hash"
 }
 
@@ -271,6 +286,11 @@ _set_nvmet_dhgroup() {
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
2.56.0
```
