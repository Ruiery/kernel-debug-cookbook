---
title: [PATCH blktests 1/5] common/nvme: don't truncate the full log when disconnecting
list: linux-block
message_id: 20261014-nvme-isolcpu-v1-1-2fd175a8ef00@kernel.org
link: https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-1-2fd175a8ef00@kernel.org/
---

# [PATCH blktests 1/5] common/nvme: don't truncate the full log when disconnecting

来源：[https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-1-2fd175a8ef00@kernel.org/](https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-1-2fd175a8ef00@kernel.org/)

```
From: Daniel Wagner <wagi@kernel.org>

_nvme_disconnect_ctrl and _nvme_disconnect_subsys redirect the output
of nvme disconnect with '&>' into $FULL. This truncates the file and
everything a test logged before the disconnect is lost, e.g. the fio
command lines logged by _run_fio.

Append to $FULL instead.

Signed-off-by: Daniel Wagner <wagi@kernel.org>
---
 common/nvme | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/common/nvme b/common/nvme
index 8c907c34910d..1b3090e0a5da 100644
--- a/common/nvme
+++ b/common/nvme
@@ -290,7 +290,7 @@ _nvme_disconnect_ctrl() {
 	if [[ -d "${ctrl_dir}" ]]; then
 		local ret
 
-		nvme disconnect --device "${ctrl}" &> "${FULL}"
+		nvme disconnect --device "${ctrl}" &>> "${FULL}"
 		ret=$?
 		if [[ ${ret} -ne 0 ]]; then
 			echo "FAIL: nvme disconnect returned error code: ${ret}"
@@ -574,7 +574,7 @@ _nvme_disconnect_subsys() {
 		esac
 	done
 
-	nvme disconnect --nqn "${subsysnqn}" &> "${FULL}"
+	nvme disconnect --nqn "${subsysnqn}" &>> "${FULL}"
 	ret=$?
 	if [[ ${ret} -ne 0 ]]; then
 		echo "FAIL: nvme disconnect returned error code: ${ret}"

-- 
2.56.0
```
