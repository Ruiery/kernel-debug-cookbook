---
title: [PATCH] rteval: Changed logic for when stress-ng is absent
list: linux-rt-users
message_id: au4xNH5aozR5P2MD@sansshar-thinkpadp1gen4i.boston.csb
link: https://lore.kernel.org/linux-rt-users/au4xNH5aozR5P2MD@sansshar-thinkpadp1gen4i.boston.csb/
---

# [PATCH] rteval: Changed logic for when stress-ng is absent

来源：[https://lore.kernel.org/linux-rt-users/au4xNH5aozR5P2MD@sansshar-thinkpadp1gen4i.boston.csb/](https://lore.kernel.org/linux-rt-users/au4xNH5aozR5P2MD@sansshar-thinkpadp1gen4i.boston.csb/)

```
Changed the failure in case stressng it not found from a sys exit
to return an empty list so as to make it more graceful

Signed-off-by: Sana Sharma <sansshar@redhat.com>
---
 rteval/modules/loads/stressng.py | 4 ++--
 tests/test_stressng.py           | 7 ++-----
 2 files changed, 4 insertions(+), 7 deletions(-)

diff --git a/rteval/modules/loads/stressng.py b/rteval/modules/loads/stressng.py
index ec59bf9..ec812dc 100644
--- a/rteval/modules/loads/stressng.py
+++ b/rteval/modules/loads/stressng.py
@@ -78,10 +78,10 @@ def get_valid_stressors():
         return result.stdout.strip().split()
     except FileNotFoundError:
         print("stress-ng is not installed. Please install the stress-ng package.")
-        sys.exit(1)
+        return []
     except subprocess.CalledProcessError as e:
         print(f"Failed to query stress-ng stressors: {e}")
-        sys.exit(1)
+        return []
 
 class Stressng(CommandLineLoad):
     " This class creates a load module that runs stress-ng "
diff --git a/tests/test_stressng.py b/tests/test_stressng.py
index 090822a..94e7cbe 100644
--- a/tests/test_stressng.py
+++ b/tests/test_stressng.py
@@ -42,16 +42,13 @@ class TestGetValidStressors(unittest.TestCase):
            side_effect=FileNotFoundError)
     def test_not_installed_exits(self, _):
         """Test when stress-ng is not installed"""
-        with self.assertRaises(SystemExit) as cm:
-            stressng.get_valid_stressors()
-        self.assertEqual(cm.exception.code, 1)
+        self.assertEqual(stressng.get_valid_stressors(), [])
 
     @patch('rteval.modules.loads.stressng.subprocess.run',
            side_effect=subprocess.CalledProcessError(1, 'stress-ng'))
     def test_query_failure_exits(self, _):
         """Test when the stress-ng query fails"""
-        with self.assertRaises(SystemExit):
-            stressng.get_valid_stressors()
+        self.assertEqual(stressng.get_valid_stressors(), [])
 
 class TestValidateStressor(unittest.TestCase):
     """Test suite for the function validate_stressor"""
-- 
2.55.0
```
