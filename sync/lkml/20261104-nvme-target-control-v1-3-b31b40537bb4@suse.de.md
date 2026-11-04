---
title: [PATCH blktests 03/10] common/nvme: check the subsystem in _nvmet_target_add_ports
list: linux-block
message_id: 20261104-nvme-target-control-v1-3-b31b40537bb4@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-3-b31b40537bb4@suse.de/
---

# [PATCH blktests 03/10] common/nvme: check the subsystem in _nvmet_target_add_ports

来源：[https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-3-b31b40537bb4@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-3-b31b40537bb4@suse.de/)

```
_nvmet_target_add_ports checks that the subsystem exists before it adds
ports to it. It checks the configfs directory of ${subsystem}, which is
not set. The path is then the subsystems directory, which always exists,
so the check never fails.

It also appends the keys to ARGS, which it doesn't declare local. They
end up in the ARGS of the caller.

Check the directory of ${subsysnqn} and declare ARGS local, as
_nvmet_target_setup does.

Fixes: db623ee8039f ("nvme: Add _nvmet_target_add_ports")
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 common/nvme | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

diff --git a/common/nvme b/common/nvme
index 93782d07dc78..dfe85b6e281f 100644
--- a/common/nvme
+++ b/common/nvme
@@ -1668,6 +1668,7 @@ _nvmet_target_add_ports() {
 	local host_port=0
 	local tls="none"
 	local cfs_path
+	local -a ARGS
 
 	while [[ $# -gt 0 ]]; do
 		case $1 in
@@ -1734,7 +1735,7 @@ _nvmet_target_add_ports() {
 		return
 	fi
 
-	cfs_path="${NVMET_CFS}/subsystems/${subsystem}"
+	cfs_path="${NVMET_CFS}/subsystems/${subsysnqn}"
 	if [[ ! -d "${cfs_path}" ]]; then
 		echo "Can not add ports to a non-existent subsystem. subsystem not found"
 		return 1;

-- 
2.56.0
```
