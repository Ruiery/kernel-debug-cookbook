---
title: [PATCH 1/5] check: unload modules when a test with a fallback device is skipped
list: linux-block
message_id: 20261118-skip-missing-deps-v1-1-a9b4a5a7cc94@suse.de
link: https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-1-a9b4a5a7cc94@suse.de/
---

# [PATCH 1/5] check: unload modules when a test with a fallback device is skipped

来源：[https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-1-a9b4a5a7cc94@suse.de/](https://lore.kernel.org/linux-block/20261118-skip-missing-deps-v1-1-a9b4a5a7cc94@suse.de/)

```
The requirement checks load modules, e.g. _have_scsi_debug loads
scsi_debug. When a test with a fallback device is skipped before the
fallback device is created, the modules stay loaded, and the next tests
that need to load the module themselves skip. A missing xfs_io for
scsi/009 skips the scsi and zbd tests that follow it.

Unload the modules on these early returns as well.

Fixes: 1967331d6667 ("check: do not create fallback device when other requirements are not met")
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 check | 3 +++
 1 file changed, 3 insertions(+)

diff --git a/check b/check
index e8613936554e..a0ce930942d8 100755
--- a/check
+++ b/check
@@ -761,6 +761,7 @@ _check_and_call_test_device() {
 		if [[ $TEST_DEV == fallback ]]; then
 			if [[ -v SKIP_REASONS ]]; then
 				_output_notrun "$TEST_NAME"
+				_unload_modules
 				return 0
 			fi
 
@@ -768,6 +769,7 @@ _check_and_call_test_device() {
 			fb_dev_file="${OUTPUT}/${TEST_NAME/\//_}_fallback_dev"
 			if ! fallback_device > "$fb_dev_file"; then
 				_warning "$TEST_NAME: fallback_device call failure"
+				_unload_modules
 				return 0
 			fi
 			TEST_DEV=$(<"$fb_dev_file")
@@ -776,6 +778,7 @@ _check_and_call_test_device() {
 			if ! _find_sysfs_dirs "$TEST_DEV"; then
 				_warning "$TEST_NAME: could not find sysfs directory for ${TEST_DEV}"
 				cleanup_fallback_device
+				_unload_modules
 				return 0
 			fi
 			fallback=1

-- 
2.56.1
```
