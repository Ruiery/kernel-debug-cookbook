---
title: [PATCH v1] rteval: Added unit tests for stress-ng validation functions
list: linux-rt-users
message_id: aqLKkrKSpkUt2OQ3@fedora
link: https://lore.kernel.org/linux-rt-users/aqLKkrKSpkUt2OQ3@fedora/
---

# [PATCH v1] rteval: Added unit tests for stress-ng validation functions

来源：[https://lore.kernel.org/linux-rt-users/aqLKkrKSpkUt2OQ3@fedora/](https://lore.kernel.org/linux-rt-users/aqLKkrKSpkUt2OQ3@fedora/)

```
Used the python unittest capability to add tests that check the
code paths added in commit aecc7c6e47d4b6b47108fabcf79be75a86ababe8
which added stressor validation to the stress-ng load.

Signed-off-by: Sana Sharma <sansshar@redhat.com
---
 Makefile                     |  6 +++++-
 tests/loads/test_stressng.py | 39 ++++++++++++++++++++++++++++++++++++
 2 files changed, 44 insertions(+), 1 deletion(-)
 create mode 100644 tests/loads/test_stressng.py

diff --git a/Makefile b/Makefile
index 869d42d..3612fc0 100644
--- a/Makefile
+++ b/Makefile
@@ -59,7 +59,11 @@ sysreport:
 unit-tests:
 	@echo "Running unit tests..."
 	./tests/run_tests.sh

+stressng-unit-tests:	
+	@echo "Running stress-ng unit tests..."
+	$(PYTHON) -m unittest tests/loads/test_stressng.py
+	
 mcp-tests:
 	@echo "Running MCP server tests..."
 	@echo "These tests require rteval result files to be present"
diff --git a/tests/loads/test_stressng.py b/tests/loads/test_stressng.py
new file mode 100644
index 0000000..6072c37
--- /dev/null
+++ b/tests/loads/test_stressng.py
@@ -0,0 +1,39 @@
+import sys, os, subprocess, unittest
+from unittest.mock import patch, MagicMock
+#sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
