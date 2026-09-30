---
title: [PATCH v3] rteval: Added unit tests for stress-ng validation
list: linux-rt-users
message_id: aqf9xfUiTADVvM-9@fedora
link: https://lore.kernel.org/linux-rt-users/aqf9xfUiTADVvM-9@fedora/
---

# [PATCH v3] rteval: Added unit tests for stress-ng validation

来源：[https://lore.kernel.org/linux-rt-users/aqf9xfUiTADVvM-9@fedora/](https://lore.kernel.org/linux-rt-users/aqf9xfUiTADVvM-9@fedora/)

```
Used the python unittest capability to add tests that check the
code paths added in commit aecc7c6e47d4 (rteval: Adding stressor
validation for stress-ng).

Signed-off-by: Sana Sharma <sansshar@redhat.com>

---
v3 of this patch changed the commit sha in the commit message to
be compliant with style requirements and added comments describing
the test functionswq
---
 tests/test_stressng.py | 55 ++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 55 insertions(+)
 create mode 100644 tests/test_stressng.py

diff --git a/tests/test_stressng.py b/tests/test_stressng.py
new file mode 100644
index 0000000..497bf54
--- /dev/null
+++ b/tests/test_stressng.py
@@ -0,0 +1,55 @@
+#!/usr/bin/env python3
+# SPDX-License-Identifier: GPL-2.0-or-later
+# Copyright 2026 Sana Sharma <sansshar@redhat.com>
+""" Unit tests for the new stressng input validation """
+
+import sys
+import os
+import subprocess
+sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
+from rteval.modules.loads import stressng
+import unittest
+from unittest.mock import patch, MagicMock
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
