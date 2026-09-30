---
title: [PATCH v5] rteval: Added unit tests for stress-ng validation
list: linux-rt-users
message_id: aqhMQ9dwr2N_C6VJ@fedora
link: https://lore.kernel.org/linux-rt-users/aqhMQ9dwr2N_C6VJ@fedora/
---

# [PATCH v5] rteval: Added unit tests for stress-ng validation

来源：[https://lore.kernel.org/linux-rt-users/aqhMQ9dwr2N_C6VJ@fedora/](https://lore.kernel.org/linux-rt-users/aqhMQ9dwr2N_C6VJ@fedora/)

```
Used the python unittest capability to add tests that check the
code paths added in commit aecc7c6e47d4 ("rteval: Adding stressor
validation for stress-ng").

Signed-off-by: Sana Sharma <sansshar@redhat.com>

---
v5 of this patch re-added main because taking it out was a mistake
that stopped the code from running.

---
 tests/test_stressng.py | 54 ++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 54 insertions(+)
 create mode 100644 tests/test_stressng.py

diff --git a/tests/test_stressng.py b/tests/test_stressng.py
new file mode 100644
index 0000000..e0445c8
--- /dev/null
+++ b/tests/test_stressng.py
@@ -0,0 +1,54 @@
+#!/usr/bin/env python3
+# SPDX-License-Identifier: GPL-2.0-or-later
+Copyright 2026 Sana Sharma <sansshar@redhat.com>
+""" Unit tests for the new stressng input validation """
+
+import sys
+import subprocess
+import unittest
+from unittest.mock import patch, MagicMock
+sys.path.insert(0,'.')
+from rteval.modules.loads import stressng
+
+class TestGetValidStressors(unittest.TestCase):
+    """Test suite for the function get_valid_stressors"""
+
+    @patch('rteval.modules.loads.stressng.subprocess.run')
+    def test_parses_stressor_list(self, mock_run):
+        """Tests that the function works for multiple correct inputs"""
+        mock_run.return_value = MagicMock(stdout="cpu vm matrix\n")
+        self.assertEqual(stressng.get_valid_stressors(), ['cpu', 'vm', 'matrix'])
+
+    @patch('rteval.modules.loads.stressng.subprocess.run',
+           side_effect=FileNotFoundError)
+    def test_not_installed_exits(self, _):
+        """Tests that the program exits correctly if stress-ng is not installed"""
+        with self.assertRaises(SystemExit) as cm:
+            stressng.get_valid_stressors()
+        self.assertEqual(cm.exception.code, 1)
+
+    @patch('rteval.modules.loads.stressng.subprocess.run',
+           side_effect=subprocess.CalledProcessError(1, 'stress-ng'))
+    def test_query_failure_exits(self, _):
+        """Tests that the program exits correctly if the query attempt fails"""
+        with self.assertRaises(SystemExit):
+            stressng.get_valid_stressors()
+
+class TestValidateStressor(unittest.TestCase):
+    """Test suite for the function validate_stressor"""
+
+    @patch('rteval.modules.loads.stressng.get_valid_stressors',
+           return_value=['cpu', 'vm'])
+    def test_valid_passes(self, _):
+        """Tests that the function works for correct inputs"""
+        stressng.validate_stressor('cpu')   # should not raise
+
+    @patch('rteval.modules.loads.stressng.get_valid_stressors',
+           return_value=['cpu', 'vm'])
+    def test_invalid_exits(self, _):
+        """Tests that the function exits properly for incorrect inputs"""
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
