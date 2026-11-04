---
title: [PATCH blktests 05/10] nvme/029: skip if the I/O exceeds the maximum transfer size
list: linux-block
message_id: 20261104-nvme-target-control-v1-5-b31b40537bb4@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-5-b31b40537bb4@suse.de/
---

# [PATCH blktests 05/10] nvme/029: skip if the I/O exceeds the maximum transfer size

来源：[https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-5-b31b40537bb4@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-5-b31b40537bb4@suse.de/)

```
nvme/029 reads and writes up to 1025 blocks with one passthrough
command. The test was written for 512 byte blocks, where this is 512
KiB. A namespace with 4 KiB blocks needs 4 MiB per command. If the
controller's maximum transfer size is smaller, the kernel rejects the
command with EINVAL and the test fails, e.g. against a target with a
1 MiB MDTS.

Skip the test if 1025 blocks don't fit the maximum transfer size of the
queue.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 tests/nvme/029 | 15 +++++++++++++--
 1 file changed, 13 insertions(+), 2 deletions(-)

diff --git a/tests/nvme/029 b/tests/nvme/029
index 59f87144e95a..a757cb9915b0 100755
--- a/tests/nvme/029
+++ b/tests/nvme/029
@@ -63,6 +63,19 @@ test() {
 
 	_nvme_connect_subsys
 
+	local ns dev max_bytes
+	ns="$(_find_nvme_ns "${def_subsys_uuid}")"
+	dev="/dev/${ns}"
+
+	# The largest I/O is 1025 blocks, it must fit the maximum transfer size.
+	max_bytes=$(($(cat "/sys/block/${ns}/queue/max_hw_sectors_kb") * 1024))
+	if ((1025 * $(blockdev --getss "$dev") > max_bytes)); then
+		SKIP_REASONS+=("max transfer size ${max_bytes} is smaller than 1025 blocks")
+		_nvme_disconnect_subsys >> "$FULL" 2>&1
+		_nvmet_target_cleanup
+		return 1
+	fi
+
 	# nvme-cli may fail to allocate linear memory for rather large IO buffers.
 	# Increase nr_hugepages to allow nvme-cli to try the linear memory allocation
 	# from HugeTLB pool.
@@ -72,8 +85,6 @@ test() {
 		reset_nr_hugepages=true
 	fi
 
-	local dev
-	dev="/dev/$(_find_nvme_ns "${def_subsys_uuid}")"
 	test_user_io "$dev" 1 512 > "$FULL" 2>&1 || echo FAIL
 	test_user_io "$dev" 1 511 >> "$FULL" 2>&1 || echo FAIL
 	test_user_io "$dev" 1 513 >> "$FULL" 2>&1 || echo FAIL

-- 
2.56.0
```
