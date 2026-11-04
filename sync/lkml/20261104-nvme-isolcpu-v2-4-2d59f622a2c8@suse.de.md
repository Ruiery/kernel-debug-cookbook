---
title: [PATCH blktests v2 4/6] nvme/rc: add helpers to count the commands on a queue
list: linux-block
message_id: 20261104-nvme-isolcpu-v2-4-2d59f622a2c8@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-4-2d59f622a2c8@suse.de/
---

# [PATCH blktests v2 4/6] nvme/rc: add helpers to count the commands on a queue

来源：[https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-4-2d59f622a2c8@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-4-2d59f622a2c8@suse.de/)

```
Tests for the queue mapping need to know which I/O queue the commands of
a CPU are sent on. Add helpers which trace the nvme_setup_cmd event for
one queue of a controller and count the commands.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 tests/nvme/rc | 33 +++++++++++++++++++++++++++++++++
 1 file changed, 33 insertions(+)

diff --git a/tests/nvme/rc b/tests/nvme/rc
index 8abd14eeb112..ea4cd500af9a 100644
--- a/tests/nvme/rc
+++ b/tests/nvme/rc
@@ -640,3 +640,36 @@ _nvme_ctrl_tls_key() {
 
 	cat /sys/class/nvme/"$ctrl"/tls_key 2>/dev/null
 }
+
+# Check that the trace instance $1 has the nvme_setup_cmd event.
+_nvme_have_setup_cmd_event() {
+	local trace_dir="$1"
+
+	if [[ ! -d "${trace_dir}/events/nvme/nvme_setup_cmd" ]]; then
+		SKIP_REASONS+=("tracepoint nvme/nvme_setup_cmd does not exist")
+		return 1
+	fi
+	return 0
+}
+
+# Start tracing the commands sent on queue $3 of controller $2 in the trace
+# instance $1.
+_nvme_trace_qid_start() {
+	local trace_dir="$1"
+	local ctrl_id="$2"
+	local qid="$3"
+	local event="${trace_dir}/events/nvme/nvme_setup_cmd"
+
+	_set_attr "" "${trace_dir}/trace"
+	_set_attr "ctrl_id == ${ctrl_id} && qid == ${qid}" "${event}/filter"
+	_set_attr 1 "${event}/enable"
+}
+
+# Stop tracing in the trace instance $1 and print the number of traced
+# commands.
+_nvme_trace_qid_stop() {
+	local trace_dir="$1"
+
+	_set_attr 0 "${trace_dir}/events/nvme/nvme_setup_cmd/enable"
+	grep -c "nvme_setup_cmd:" "${trace_dir}/trace"
+}

-- 
2.56.0
```
