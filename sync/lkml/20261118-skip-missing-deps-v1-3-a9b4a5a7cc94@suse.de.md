---
title: [PATCH 3/5] nbd/003: skip if mkfs.ext4 is missing
list: linux-block
message_id: 20261118-skip-missing-deps-v1-3-a9b4a5a7cc94@suse.de
link: https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-3-a9b4a5a7cc94@suse.de/
---

# [PATCH 3/5] nbd/003: skip if mkfs.ext4 is missing

来源：[https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-3-a9b4a5a7cc94@suse.de/](https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-3-a9b4a5a7cc94@suse.de/)

```
nbd/003 runs mkfs.ext4 without checking for it, so it fails instead of
being skipped on a host without e2fsprogs. Check for it in requires().

Fixes: f7b47c58e87c ("nbd/003:add mount and clear_sock test for nbd")
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 tests/nbd/003 | 1 +
 1 file changed, 1 insertion(+)

diff --git a/tests/nbd/003 b/tests/nbd/003
index 4fabdebc8f6a..fdcfe0182653 100755
--- a/tests/nbd/003
+++ b/tests/nbd/003
@@ -13,6 +13,7 @@ QUICK=1
 requires() {
 	_have_nbd
 	_have_src_program mount_clear_sock
+	_have_program mkfs.ext4
 }
 
 test() {

-- 
2.56.1
```
