---
title: [PATCH blktests v2 3/6] nvme/078: test reconnect with fewer I/O queues
list: linux-block
message_id: 20261104-nvme-isolcpu-v2-3-2d59f622a2c8@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-3-2d59f622a2c8@suse.de/
---

# [PATCH blktests v2 3/6] nvme/078: test reconnect with fewer I/O queues

来源：[https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-3-2d59f622a2c8@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-isolcpu-v2-3-2d59f622a2c8@suse.de/)

```
nvmf_set_io_queues() used to only set the io_queues entries for the
queue types it hands out, but the array is reused on every reconnect.
When the target granted fewer queues on a reconnect, the poll queue
count from the previous association survived, nvmf_map_queues() mapped
CPUs to hardware contexts which don't exist anymore and
blk_mq_map_swqueue() crashed with a NULL pointer dereference.

Connect with as many read, write and poll queues as there are online
CPUs, then lower attr_qid_max on the target to twice the number of
online CPUs, which makes the target drop the controller. After the
reconnect with fewer queues, check the queue count, that the queue
doesn't claim poll support and run verified I/O.

The problem is fixed by kernel commits 9588769af5fc ("nvme-fabrics:
reset io_queues before computing the queue mapping") and 36ede1aa85d5
("nvme-fabrics: clear the poll map if no poll queues are mapped").

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 tests/nvme/078     | 119 +++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/nvme/078.out |   2 +
 2 files changed, 121 insertions(+)

diff --git a/tests/nvme/078 b/tests/nvme/078
new file mode 100755
index 000000000000..6efeb740e075
--- /dev/null
+++ b/tests/nvme/078
@@ -0,0 +1,119 @@
+#!/bin/bash
+# SPDX-License-Identifier: GPL-3.0+
+# Copyright (c) 2026 SUSE LLC and contributors
+#
+# Test reconnecting with fewer I/O queues. nvmf_set_io_queues used to only set
+# the io_queues entries for the queue types it hands out, but the array is
+# reused on every reconnect. When the target grants fewer queues on a
+# reconnect, the poll queue count from the previous association survived,
+# nvmf_map_queues mapped CPUs to hardware contexts which don't exist anymore
+# and blk_mq_map_swqueue crashed. Without the poll map fix, the poll map keeps
+# mapping all CPUs to the first hardware context and the queue claims poll
+# support.
+#
+# The stale io_queues entries were introduced for nvme-tcp by commit
+# 6486199378a5 ("nvme-tcp: fix queue mapping when queue count is limited") and
+# for nvme-rdma by commit 5651cd3c4336 ("nvme-rdma: fix queue mapping when
+# queue count is limited"). The stale poll map was introduced for nvme-tcp by
+# commit 1a9460cef571 ("nvme-tcp: support simple polling") and for nvme-rdma by
+# commit 5651cd3c4336.
+#
+# Regression test for commits 9588769af5fc ("nvme-fabrics: reset io_queues
+# before computing the queue mapping") and 36ede1aa85d5 ("nvme-fabrics: clear
+# the poll map if no poll queues are mapped").
+
+. tests/nvme/rc
+
+DESCRIPTION="Test reconnect with fewer I/O queues"
+QUICK=1
+CHECK_DMESG=1
+
+requires() {
+	_nvme_requires
+	_have_fio
+	_have_loop
+	_require_nvme_trtype tcp rdma
+}
+
+set_conditions() {
+	_set_nvme_trtype "$@"
+}
+
+wait_for_queue_count() {
+	local nvmedev="$1"
+	local queue_count="$2"
+	local file="/sys/class/nvme-fabrics/ctl/${nvmedev}/queue_count"
+	local retries=10
+
+	while [[ $(cat "${file}") -ne $((queue_count + 1)) ]]; do
+		if [[ "${retries}" == 0 ]]; then
+			echo "FAIL: queue count $(cat "${file}") instead of $((queue_count + 1))"
+			return 1
+		fi
+		sleep 1
+		retries=$((retries - 1))
+	done
+
+	return 0
+}
+
+test() {
+	echo "Running ${TEST_NAME}"
+
+	local cfs_path="${NVMET_CFS}/subsystems/${def_subsysnqn}"
+	local nr_cpus
+	local nvmedev
+	local disk
+	local ns
+
+	_setup_nvmet
+
+	nr_cpus=$(getconf _NPROCESSORS_ONLN)
+
+	_nvmet_target_setup
+
+	if [[ ! -f "${cfs_path}/attr_qid_max" ]]; then
+		SKIP_REASONS+=("missing attr_qid_max feature")
+		_nvmet_target_cleanup
+		return 1
+	fi
+	if [[ $(cat "${cfs_path}/attr_qid_max") -lt $((3 * nr_cpus)) ]]; then
+		SKIP_REASONS+=("target supports less than $((3 * nr_cpus)) I/O queues")
+		_nvmet_target_cleanup
+		return 1
+	fi
+
+	if _nvme_connect_subsys --nr-io-queues "${nr_cpus}" \
+				--nr-write-queues "${nr_cpus}" \
+				--nr-poll-queues "${nr_cpus}" \
+				--keep-alive-tmo 1 \
+				--reconnect-delay 2; then
+		_nvmf_wait_for_state "${def_subsysnqn}" "live" || echo FAIL
+		nvmedev=$(_find_nvme_dev "${def_subsysnqn}")
+		disk=$(basename /sys/class/nvme/"${nvmedev}"/nvme*n*)
+		wait_for_queue_count "${nvmedev}" $((3 * nr_cpus))
+
+		# Changing attr_qid_max makes the target drop the controller.
+		# Reconnect with only enough queues for the read and default
+		# queues, so no queues are left for polling.
+		_set_attr $((2 * nr_cpus)) "${cfs_path}/attr_qid_max"
+		wait_for_queue_count "${nvmedev}" $((2 * nr_cpus))
+		_nvmf_wait_for_state "${def_subsysnqn}" "live" || echo FAIL
+
+		if [[ $(cat "/sys/block/${disk}/queue/io_poll") != 0 ]]; then
+			echo "FAIL: ${disk} claims poll support without poll queues"
+		fi
+
+		ns=$(_find_nvme_ns "${def_subsys_uuid}")
+		_run_fio_verify_io --size=32m --filename="/dev/${ns}" ||
+			echo "FAIL: fio verify"
+
+		_nvme_disconnect_subsys
+	else
+		echo "FAIL: controller not ready"
+	fi
+
+	_nvmet_target_cleanup
+
+	echo "Test complete"
+}
diff --git a/tests/nvme/078.out b/tests/nvme/078.out
new file mode 100644
index 000000000000..53857c8914c0
--- /dev/null
+++ b/tests/nvme/078.out
@@ -0,0 +1,2 @@
+Running nvme/078
+Test complete

-- 
2.56.0
```
