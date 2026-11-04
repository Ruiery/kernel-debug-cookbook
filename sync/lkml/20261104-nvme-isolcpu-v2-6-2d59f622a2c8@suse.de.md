---
title: [PATCH blktests v2 6/6] nvme/080: test connect with offline CPUs
list: linux-block
message_id: 20261104-nvme-isolcpu-v2-6-2d59f622a2c8@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-6-2d59f622a2c8@suse.de/
---

# [PATCH blktests v2 6/6] nvme/080: test connect with offline CPUs

来源：[https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-6-2d59f622a2c8@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-6-2d59f622a2c8@suse.de/)

```
blk-mq maps all possible CPUs to the hardware contexts, offline CPUs
included. If a hardware context is mapped only to offline CPUs,
blk_mq_alloc_request_hctx has no online CPU to select the software
context from and fails with -EXDEV. The fabrics transports allocate the
Connect command for each I/O queue this way, so connecting fails while
CPUs are offline.

Offline the upper half of the CPUs and connect. Check that a hardware
context is mapped only to offline CPUs, bring them online, run I/O from
one of them and trace that its commands are sent on the queue of that
hardware context.

The bug was introduced by kernel commit 20e4d8139319 ("blk-mq: simplify
queue mapping & schedule with each possisble CPU") and is fixed by
kernel commit XXX ("blk-mq: allow passthrough requests on hctxs without
online CPUs").

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 tests/nvme/080     | 142 +++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/nvme/080.out |   2 +
 2 files changed, 144 insertions(+)

diff --git a/tests/nvme/080 b/tests/nvme/080
new file mode 100755
index 000000000000..eea4ed237218
--- /dev/null
+++ b/tests/nvme/080
@@ -0,0 +1,142 @@
+#!/bin/bash
+# SPDX-License-Identifier: GPL-3.0+
+# Copyright (c) 2026 SUSE LLC and contributors
+#
+# Test connecting with offline CPUs. blk-mq maps all possible CPUs to the
+# hardware contexts, the offline ones too. If only offline CPUs are mapped to
+# a hardware context, blk_mq_alloc_request_hctx has no online CPU to take the
+# software context from and fails with -EXDEV. The fabrics transports allocate
+# the Connect command for each I/O queue this way, so the connect fails.
+#
+# Offline the upper half of the CPUs and connect. Check that a hardware context
+# has only offline CPUs mapped, bring them online, run I/O from one of them and
+# trace the queue IDs of the commands to verify that the hardware context is
+# used and works.
+#
+# The bug was introduced by commit 20e4d8139319 ("blk-mq: simplify queue
+# mapping & schedule with each possisble CPU").
+#
+# Regression test for commit XXX ("blk-mq: allow passthrough requests on hctxs
+# without online CPUs").
+
+. tests/nvme/rc
+. common/cpuhotplug
+
+DESCRIPTION="Test connect with offline CPUs"
+QUICK=1
+
+requires() {
+	_nvme_requires
+	_have_fio
+	_have_loop
+	_require_nvme_trtype_is_fabrics
+	_require_min_cpus 4
+	_have_cpu_hotplug
+	_have_tracefs
+}
+
+set_conditions() {
+	_set_nvme_trtype "$@"
+}
+
+offline_upper_cpus() {
+	local -a cpus
+	local cpu
+
+	mapfile -t cpus < <(printf '%s\n' "${HOTPLUGGABLE_CPUS[@]}" | sort -n)
+	for cpu in "${cpus[@]:$((${#cpus[@]} / 2))}"; do
+		_offline_cpu "${cpu}"
+	done
+}
+
+# Print the hctx directory and the CPUs of the first hardware context which
+# only has offline CPUs mapped.
+find_offline_hctx() {
+	local disk="$1"
+	local hctx
+	local cpu
+	local cpus
+
+	for hctx in /sys/block/"${disk}"/mq/*; do
+		cpus=$(tr -d ' ' < "${hctx}/cpu_list" | tr ',' ' ')
+		for cpu in ${cpus}; do
+			if [[ $(cat "/sys/devices/system/cpu/cpu${cpu}/online" \
+					2>/dev/null || echo 1) == 1 ]]; then
+				continue 2
+			fi
+		done
+		echo "$(basename "${hctx}") ${cpus}"
+		return 0
+	done
+	return 1
+}
+
+test() {
+	echo "Running ${TEST_NAME}"
+
+	local nvmedev
+	local disk
+	local ns
+	local hctx
+	local cpu_list
+	local -a cpus
+	local cpu
+	local nr_cmds
+	local trace_dir="/sys/kernel/debug/tracing/instances/blktests-nvme-080"
+	local skipped=false
+
+	_setup_nvmet
+
+	offline_upper_cpus
+
+	_nvmet_target_setup
+
+	if _nvme_connect_subsys; then
+		_nvmf_wait_for_state "${def_subsysnqn}" "live" || echo FAIL
+		nvmedev=$(_find_nvme_dev "${def_subsysnqn}")
+		disk=$(basename /sys/class/nvme/"${nvmedev}"/nvme*n*)
+		ns=$(_find_nvme_ns "${def_subsys_uuid}")
+
+		# The CPUs are spread over the hardware contexts in topology
+		# order, so usually the upper ones end up without online CPU.
+		if read -r hctx cpu_list < <(find_offline_hctx "${disk}"); then
+			read -r -a cpus <<< "${cpu_list}"
+			for cpu in "${HOTPLUGGABLE_CPUS[@]}"; do
+				_online_cpu "${cpu}"
+			done
+
+			cpu=${cpus[0]}
+			mkdir "${trace_dir}"
+			if _nvme_have_setup_cmd_event "${trace_dir}"; then
+				_nvme_trace_qid_start "${trace_dir}" \
+					"${nvmedev#nvme}" $((hctx + 1))
+				_run_fio_verify_io --size=32m \
+					--filename="/dev/${ns}" \
+					--cpus_allowed="${cpu}" ||
+					echo "FAIL: fio verify on CPU ${cpu}"
+				nr_cmds=$(_nvme_trace_qid_stop "${trace_dir}")
+				if [[ "${nr_cmds}" -eq 0 ]]; then
+					echo "FAIL: no commands from CPU ${cpu} on hctx ${hctx}"
+				fi
+			else
+				skipped=true
+			fi
+			rmdir "${trace_dir}"
+		else
+			SKIP_REASONS+=("no hardware context with only offline CPUs")
+			skipped=true
+		fi
+
+		_nvme_disconnect_subsys
+	else
+		echo "FAIL: controller not ready"
+	fi
+
+	_nvmet_target_cleanup
+
+	if [[ "${skipped}" = true ]]; then
+		return 1
+	fi
+
+	echo "Test complete"
+}
diff --git a/tests/nvme/080.out b/tests/nvme/080.out
new file mode 100644
index 000000000000..15119b8d7a83
--- /dev/null
+++ b/tests/nvme/080.out
@@ -0,0 +1,2 @@
+Running nvme/080
+Test complete

-- 
2.56.0
```
