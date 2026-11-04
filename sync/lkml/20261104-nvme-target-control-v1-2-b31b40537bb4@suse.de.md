---
title: [PATCH blktests 02/10] common/nvme: wait for the namespace of a remote target
list: linux-block
message_id: 20261104-nvme-target-control-v1-2-b31b40537bb4@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-2-b31b40537bb4@suse.de/
---

# [PATCH blktests 02/10] common/nvme: wait for the namespace of a remote target

来源：[https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-2-b31b40537bb4@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-2-b31b40537bb4@suse.de/)

```
_nvme_ns_ready waits for the namespaces in the local nvmet configfs. With
NVME_TARGET_CONTROL the subsystem is configured on the remote target, so
the configfs directory doesn't exist. The glob stays unexpanded and
_nvme_ns_ready never succeeds. _nvme_connect_subsys then returns 2 after
every connect, and tests which check its return value skip their I/O and
the disconnect.

Wait for the first namespace of the controller instead.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 common/nvme | 7 +++++++
 1 file changed, 7 insertions(+)

diff --git a/common/nvme b/common/nvme
index a8c7634ec2b8..93782d07dc78 100644
--- a/common/nvme
+++ b/common/nvme
@@ -1027,6 +1027,13 @@ _nvme_ns_ready() {
 	local cfs_path="${NVMET_CFS}/subsystems/$subsysnqn"
 
 	dev=$(_find_nvme_dev "$subsysnqn")
+	if [[ -n "${nvme_target_control}" ]]; then
+		# The namespaces are configured on the remote target, wait
+		# for the first one the controller reports.
+		[[ -b /dev/${dev}n1 && -e /sys/block/${dev}n1/uuid &&
+			-e /sys/block/${dev}n1/wwid ]]
+		return
+	fi
 	for ns_path in "${cfs_path}/namespaces/"*; do
 		ns_id=${ns_path##*/}
 		if [[ ! -b /dev/${dev}n${ns_id} ||

-- 
2.56.0
```
