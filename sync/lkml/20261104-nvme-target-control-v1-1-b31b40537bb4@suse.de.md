---
title: [PATCH blktests 01/10] common/nvme: pass --ctrlkey to the target control script
list: linux-block
message_id: 20261104-nvme-target-control-v1-1-b31b40537bb4@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-1-b31b40537bb4@suse.de/
---

# [PATCH blktests 01/10] common/nvme: pass --ctrlkey to the target control script

来源：[https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-1-b31b40537bb4@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-1-b31b40537bb4@suse.de/)

```
_nvmet_target_setup and _nvmet_target_add_ports pass the controller key
to the NVME_TARGET_CONTROL script as --ctrkey. running-tests.md and
contrib/nvme_target_control.py name the option --ctrlkey. The script
rejects --ctrkey, so the setup fails for the tests with a controller
key, nvme/044 and nvme/045.

Pass --ctrlkey.

Fixes: 5b6d89ced118 ("nvme/rc: introduce remote target support")
Fixes: db623ee8039f ("nvme: Add _nvmet_target_add_ports")
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 common/nvme | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/common/nvme b/common/nvme
index ad3d140a8811..a8c7634ec2b8 100644
--- a/common/nvme
+++ b/common/nvme
@@ -1611,7 +1611,7 @@ _nvmet_target_setup() {
 			ARGS+=(--hostkey "${hostkey}")
 		fi
 		if [[ -n "${ctrlkey}" ]]; then
-			ARGS+=(--ctrkey "${ctrlkey}")
+			ARGS+=(--ctrlkey "${ctrlkey}")
 		fi
 
 		"${nvme_target_control}" setup \
@@ -1708,7 +1708,7 @@ _nvmet_target_add_ports() {
 			ARGS+=(--hostkey "${hostkey}")
 		fi
 		if [[ -n "${ctrlkey}" ]]; then
-			ARGS+=(--ctrkey "${ctrlkey}")
+			ARGS+=(--ctrlkey "${ctrlkey}")
 		fi
 
 		"${nvme_target_control}" add-ports \

-- 
2.56.0
```
