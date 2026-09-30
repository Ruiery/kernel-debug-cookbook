---
title: [PATCH v2] rteval: Added unit tests for stress-ng validation
list: linux-rt-users
message_id: aqRl4ImQ--RS_HBG@fedora
link: https://lore.kernel.org/linux-rt-users/aqRl4ImQ--RS_HBG@fedora/
---

# [PATCH v2] rteval: Added unit tests for stress-ng validation

来源：[https://lore.kernel.org/linux-rt-users/aqRl4ImQ--RS_HBG@fedora/](https://lore.kernel.org/linux-rt-users/aqRl4ImQ--RS_HBG@fedora/)

```
Used the python unittest capability to add tests that check the
code paths added in commit aecc7c6e47d4 which added stressor
validation to the stress-ng load.

Signed-off-by: Sana Sharma <sansshar@redhat.com>

---
v2 of this patch gets rid of the unnecessary Makefile changes
by changing the unit-test location so it gets automatically
discovered. I also changed the commit sha in the commit
message to be compliant with style requirements.

 tests/test_stressng.py | 39 +++++++++++++++++++++++++++++++++++++++
 1 file changed, 39 insertions(+)
 create mode 100644 tests/test_stressng.py

diff --git a/tests/test_stressng.py b/tests/test_stressng.py
new file mode 100644
index 0000000..a4302f6
--- /dev/null
+++ b/tests/test_stressng.py
@@ -0,0 +1,39 @@
+import sys, os, subprocess, unittest
+from unittest.mock import patch, MagicMock
+sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+from rteval.modules.loads import stressng
+
+class TestGetValidStressors(unittest.TestCase):
+    @patch('rteval.modules.loads.stressng.subprocess.run')
+    def test_parses_stressor_list(self, mock_run):
+        mock_run.return_value = MagicMock(stdout="cpu vm matrix\n")
+        self.assertEqual(stressng.get_valid_stressors(), ['cpu', 'vm', 'matrix'])
+
+    @patch('rteval.modules.loads.stressng.subprocess.run',
+           side_effect=FileNotFoundError)
+    def test_not_installed_exits(self, _):
+        with self.assertRaises(SystemExit) as cm:
+            stressng.get_valid_stressors()
+        self.assertEqual(cm.exception.code, 1)
+
+    @patch('rteval.modules.loads.stressng.subprocess.run',
+           side_effect=subprocess.CalledProcessError(1, 'stress-ng'))
+    def test_query_failure_exits(self, _):
+        with self.assertRaises(SystemExit):
+            stressng.get_valid_stressors()
+
+class TestValidateStressor(unittest.TestCase):
+    @patch('rteval.modules.loads.stressng.get_valid_stressors',
+           return_value=['cpu', 'vm'])
+    def test_valid_passes(self, _):
+        stressng.validate_stressor('cpu')   # should not raise
+
+    @patch('rteval.modules.loads.stressng.get_valid_stressors',
+           return_value=['cpu', 'vm'])
+    def test_invalid_exits(self, _):
+        with self.assertRaises(SystemExit) as cm:
+            stressng.validate_stressor('bogus')
+        self.assertEqual(cm.exception.code, 1)
+
+if __name__ == '__main__':
+    unittest.main()
-- 
2.54.0


-- 
Sana Sharma <sansshar@redhat.com>
```
