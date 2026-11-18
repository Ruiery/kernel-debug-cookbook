---
title: [PATCH blktests v2 1/9] nvme/047: look up the namespace again after reconnecting
list: linux-block
message_id: 20261118-nvme-target-control-v2-1-d191bbbf5dd6@suse.de
link: https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-1-d191bbbf5dd6@suse.de/
---

# [PATCH blktests v2 1/9] nvme/047: look up the namespace again after reconnecting

来源：[https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-1-d191bbbf5dd6@suse.de/](https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-1-d191bbbf5dd6@suse.de/)

```
nvme/047 keeps using the namespace name from the first connect after
reconnecting. The name can change when other controllers come and go,
and fio then fails to open the device. Look it up again after the
second connect.

Fixes: 7497d8b45817 ("nvme/047: Test different queue types for fabrics transports")
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 tests/nvme/047 | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/tests/nvme/047 b/tests/nvme/047
index 433090f2d6f2..2aeee2f0f1aa 100755
--- a/tests/nvme/047
+++ b/tests/nvme/047
@@ -42,6 +42,8 @@ test() {
 
 	_nvme_connect_subsys --nr-write-queues 1 --nr-poll-queues 1
 
+	ns=$(_find_nvme_ns "${def_subsys_uuid}")
+
 	_run_fio_rand_io --filename="/dev/${ns}" --size="${rand_io_size}"
 
 	_nvme_disconnect_subsys >> "$FULL" 2>&1

-- 
2.56.1
```
