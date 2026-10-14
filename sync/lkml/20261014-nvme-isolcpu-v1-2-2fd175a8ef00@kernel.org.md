---
title: [PATCH blktests 2/5] nvme/070: test connect with an isolated CPU
list: linux-block
message_id: 20261014-nvme-isolcpu-v1-2-2fd175a8ef00@kernel.org
link: https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-2-2fd175a8ef00@kernel.org/
---

# [PATCH blktests 2/5] nvme/070: test connect with an isolated CPU

来源：[https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-2-2fd175a8ef00@kernel.org/](https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-2-2fd175a8ef00@kernel.org/)

```
From: Daniel Wagner <wagi@kernel.org>

Since kernel commit a46c27026da1 ("blk-mq: don't schedule block kworker
on isolated CPUs") isolated CPUs are removed from the CPU mask of the
hardware contexts. If only isolated CPUs are mapped to a hardware
context, the mask is empty and blk_mq_alloc_request_hctx fails with
-EXDEV. The fabrics transports allocate the Connect command for each
I/O queue this way, so the connect fails, e.g. with isolcpus=domain or
with an isolated cpuset partition.

Isolate the last online CPU with a cpuset partition, connect with the
default number of I/O queues and run verified I/O from a housekeeping
CPU and from the isolated CPU. To make sure the test exercises the
problem, it checks that the hardware context of the isolated CPU has an
empty CPU mask, that the I/O of the isolated CPU runs on that CPU, and
traces nvme_setup_cmd on the queue of the hardware context: the
housekeeping CPUs must not submit commands on it, the isolated CPU must.

The problem is fixed by kernel commit XXX ("blk-mq: use a housekeeping
CPU for passthrough requests on isolated hctxs").

Signed-off-by: Daniel Wagner <wagi@kernel.org>
---
 tests/nvme/070     | 196 +++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/nvme/070.out |   2 +
 2 files changed, 198 insertions(+)

diff --git a/tests/nvme/070 b/tests/nvme/070
new file mode 100755
index 000000000000..6b9d4d80e257
--- /dev/null
+++ b/tests/nvme/070
@@ -0,0 +1,196 @@
+#!/bin/bash
+# SPDX-License-Identifier: GPL-3.0+
+# Copyright (c) 2026 SUSE LLC and contributors
+#
+# Test connecting with an isolated CPU. blk-mq removes the CPUs which are
+# isolated, e.g. with a cpuset isolated partition, from the CPU mask of the
+# hardware contexts. If a hardware context ends up without a CPU, the Connect
+# command for its I/O queue can't be allocated and the connect fails. Run I/O
+# from a housekeeping CPU and from the isolated CPU and trace the queue IDs of
+# the commands to verify that the hardware context of the isolated CPU is used
+# and works.
+#
+# The bug was introduced by commit a46c27026da1 ("blk-mq: don't schedule block
+# kworker on isolated CPUs").
+#
+# Regression test for commit XXX ("blk-mq: use a housekeeping CPU for
+# passthrough requests on isolated hctxs").
+
+. tests/nvme/rc
+. common/cgroup
+
+DESCRIPTION="Test connect with an isolated CPU"
+QUICK=1
+
+requires() {
+	_nvme_requires
+	_have_fio
+	_have_loop
+	_require_nvme_trtype_is_fabrics
+	_require_min_cpus 2
+	_have_cgroup2_controller_file cpuset cpuset.cpus.partition
+	_have_tracefs
+}
+
+set_conditions() {
+	_set_nvme_trtype "$@"
+}
+
+isolate_cpu() {
+	local cpu="$1"
+	local partition
+
+	_init_cgroup2 || return 1
+	_set_attr "+cpuset" "$(_cgroup2_base_dir)/cgroup.subtree_control"
+	_set_attr "${cpu}" "${CGROUP2_DIR}/cpuset.cpus"
+	_set_attr "isolated" "${CGROUP2_DIR}/cpuset.cpus.partition"
+
+	partition=$(cat "${CGROUP2_DIR}/cpuset.cpus.partition")
+	if [[ "${partition}" != "isolated" ]]; then
+		SKIP_REASONS+=("failed to isolate CPU ${cpu}: ${partition}")
+		_exit_cgroup2
+		return 1
+	fi
+
+	return 0
+}
+
+run_io() {
+	local ns="$1"
+
+	_run_fio_verify_io --size=32m --filename="/dev/${ns}"
+}
+
+# Set isolated_hctx to the index of the hardware context the software context
+# of the CPU is mapped to, if the CPU mask of the hardware context is empty.
+find_isolated_hctx() {
+	local nvmedev="$1"
+	local cpu="$2"
+	local ctx
+	local hctx
+
+	for ctx in /sys/class/nvme/"${nvmedev}"/nvme*n*/mq/*/cpu"${cpu}"; do
+		[[ -d "${ctx}" ]] || continue
+		hctx="$(dirname "${ctx}")"
+		if [[ -n "$(cat "${hctx}/cpu_list")" ]]; then
+			SKIP_REASONS+=("hctx of CPU ${cpu} has CPUs: $(cat "${hctx}/cpu_list")")
+			return 1
+		fi
+		isolated_hctx="$(basename "${hctx}")"
+		return 0
+	done
+
+	SKIP_REASONS+=("no hctx found for CPU ${cpu}")
+	return 1
+}
+
+start_trace() {
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
+# Stop tracing and print the number of traced commands.
+stop_trace() {
+	local trace_dir="$1"
+
+	_set_attr 0 "${trace_dir}/events/nvme/nvme_setup_cmd/enable"
+	grep -c "nvme_setup_cmd:" "${trace_dir}/trace"
+}
+
+check_io() {
+	local nvmedev="$1"
+	local cpu="$2"
+	local trace_dir="$3"
+	local ns
+	local isolated_hctx
+	local qid
+	local nr_cmds
+
+	ns=$(_find_nvme_ns "${def_subsys_uuid}")
+	find_isolated_hctx "${nvmedev}" "${cpu}" || return 1
+	qid=$((isolated_hctx + 1))
+
+	if [[ ! -d "${trace_dir}/events/nvme/nvme_setup_cmd" ]]; then
+		SKIP_REASONS+=("tracepoint nvme/nvme_setup_cmd does not exist")
+		return 1
+	fi
+
+	# The test runs on the housekeeping CPUs, which must not use the
+	# hardware context of the isolated CPU.
+	start_trace "${trace_dir}" "${nvmedev#nvme}" "${qid}"
+	run_io "${ns}" || echo "FAIL: I/O from housekeeping CPU"
+	nr_cmds=$(stop_trace "${trace_dir}")
+	if [[ "${nr_cmds}" -ne 0 ]]; then
+		echo "FAIL: ${nr_cmds} commands from housekeeping CPUs on qid ${qid}"
+	fi
+
+	# Moving the subshell into the partition confines it to the
+	# isolated CPU, so its I/O uses the hardware context of the
+	# isolated CPU.
+	start_trace "${trace_dir}" "${nvmedev#nvme}" "${qid}"
+	(
+		local allowed
+
+		_set_attr "${BASHPID}" "${CGROUP2_DIR}/cgroup.procs"
+		allowed=$(awk '/^Cpus_allowed_list:/ { print $2 }' \
+				"/proc/${BASHPID}/status")
+		if [[ "${allowed}" != "${cpu}" ]]; then
+			echo "FAIL: subshell runs on CPUs ${allowed}"
+			exit 1
+		fi
+		run_io "${ns}"
+	) || echo "FAIL: I/O from isolated CPU ${cpu}"
+	nr_cmds=$(stop_trace "${trace_dir}")
+	if [[ "${nr_cmds}" -eq 0 ]]; then
+		echo "FAIL: no commands from isolated CPU ${cpu} on qid ${qid}"
+	fi
+
+	return 0
+}
+
+test() {
+	echo "Running ${TEST_NAME}"
+
+	local cpu
+	local nvmedev
+	local trace_dir="/sys/kernel/debug/tracing/instances/blktests-nvme-070"
+	local skipped=false
+
+	_setup_nvmet
+
+	# Isolate the last online CPU. Without nr_io_queues there is usually
+	# one I/O queue per online CPU, so its hardware context has no other
+	# CPU.
+	cpu=$(awk -F'[-,]' '{ print $NF }' /sys/devices/system/cpu/online)
+	if ! isolate_cpu "${cpu}"; then
+		return 1
+	fi
+
+	_nvmet_target_setup
+
+	if _nvme_connect_subsys; then
+		_nvmf_wait_for_state "${def_subsysnqn}" "live" || echo FAIL
+		nvmedev=$(_find_nvme_dev "${def_subsysnqn}")
+
+		mkdir "${trace_dir}"
+		check_io "${nvmedev}" "${cpu}" "${trace_dir}" || skipped=true
+		rmdir "${trace_dir}"
+
+		_nvme_disconnect_subsys
+	fi
+
+	_nvmet_target_cleanup
+	_exit_cgroup2
+
+	if [[ "${skipped}" = true ]]; then
+		return 1
+	fi
+
+	echo "Test complete"
+}
diff --git a/tests/nvme/070.out b/tests/nvme/070.out
new file mode 100644
index 000000000000..b765a2894652
--- /dev/null
+++ b/tests/nvme/070.out
@@ -0,0 +1,2 @@
+Running nvme/070
+Test complete

-- 
2.56.0
```
