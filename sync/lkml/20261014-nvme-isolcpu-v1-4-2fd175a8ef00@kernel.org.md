---
title: [PATCH blktests 4/5] nvme/072: test poll support without poll queues
list: linux-block
message_id: 20261014-nvme-isolcpu-v1-4-2fd175a8ef00@kernel.org
link: https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-4-2fd175a8ef00@kernel.org/
---

# [PATCH blktests 4/5] nvme/072: test poll support without poll queues

来源：[https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-4-2fd175a8ef00@kernel.org/](https://lore.kernel.org/linux-block/20261014-nvme-isolcpu-v1-4-2fd175a8ef00@kernel.org/)

```
From: Daniel Wagner <wagi@kernel.org>

blk_mq_alloc_tag_set() initializes all queue maps. When nr_poll_queues
is set but the target grants no queues for polling, nvmf_map_queues()
used to leave the poll map in this state, with all CPUs mapped to the
first hardware context. The queue claimed poll support and polled I/O
was sent to a queue which isn't a poll queue.

Limit the target to twice the number of online CPUs, connect with as
many read, write and poll queues as there are online CPUs, so no queues
are left for polling, check that the queue doesn't claim poll support
and run verified I/O.

The problem is fixed by kernel commit XXX ("nvme-fabrics: clear the poll
map if no poll queues are mapped").

Signed-off-by: Daniel Wagner <wagi@kernel.org>
---
 tests/nvme/072     | 85 ++++++++++++++++++++++++++++++++++++++++++++++++++++++
 tests/nvme/072.out |  2 ++
 2 files changed, 87 insertions(+)

diff --git a/tests/nvme/072 b/tests/nvme/072
new file mode 100755
index 000000000000..72bf80d660f5
--- /dev/null
+++ b/tests/nvme/072
@@ -0,0 +1,85 @@
+#!/bin/bash
+# SPDX-License-Identifier: GPL-3.0+
+# Copyright (c) 2026 SUSE LLC and contributors
+#
+# Test that a controller without poll queues doesn't claim poll support.
+# blk_mq_alloc_tag_set initializes all queue maps. When nr_poll_queues is set
+# but the target grants no queues for polling, nvmf_map_queues used to leave
+# the poll map in this state, so the queue claimed poll support and polled I/O
+# was sent to a queue which isn't a poll queue.
+#
+# The bug was introduced for nvme-tcp by commit 1a9460cef571 ("nvme-tcp:
+# support simple polling") and for nvme-rdma by commit 5651cd3c4336
+# ("nvme-rdma: fix queue mapping when queue count is limited").
+#
+# Regression test for commit XXX ("nvme-fabrics: clear the poll map if no poll
+# queues are mapped").
+
+. tests/nvme/rc
+
+DESCRIPTION="Test poll support without poll queues"
+QUICK=1
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
+	if [[ $(cat "${cfs_path}/attr_qid_max") -lt $((2 * nr_cpus)) ]]; then
+		SKIP_REASONS+=("target supports less than $((2 * nr_cpus)) I/O queues")
+		_nvmet_target_cleanup
+		return 1
+	fi
+
+	# Only grant enough queues for the read and default queues, so no
+	# queues are left for polling.
+	_set_attr $((2 * nr_cpus)) "${cfs_path}/attr_qid_max"
+
+	if _nvme_connect_subsys --nr-io-queues "${nr_cpus}" \
+				--nr-write-queues "${nr_cpus}" \
+				--nr-poll-queues "${nr_cpus}"; then
+		_nvmf_wait_for_state "${def_subsysnqn}" "live" || echo FAIL
+		nvmedev=$(_find_nvme_dev "${def_subsysnqn}")
+		disk=$(basename /sys/class/nvme/"${nvmedev}"/nvme*n*)
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
+	fi
+
+	_nvmet_target_cleanup
+
+	echo "Test complete"
+}
diff --git a/tests/nvme/072.out b/tests/nvme/072.out
new file mode 100644
index 000000000000..3f765b30a22b
--- /dev/null
+++ b/tests/nvme/072.out
@@ -0,0 +1,2 @@
+Running nvme/072
+Test complete

-- 
2.56.0
```
