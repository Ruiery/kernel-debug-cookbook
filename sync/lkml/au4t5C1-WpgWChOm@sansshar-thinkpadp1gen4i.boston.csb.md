---
title: [PATCH v1] rteval: Covering edge cases in multi-stressor support
list: linux-rt-users
message_id: au4t5C1-WpgWChOm@sansshar-thinkpadp1gen4i.boston.csb
link: https://lore.kernel.org/linux-rt-users/au4t5C1-WpgWChOm@sansshar-thinkpadp1gen4i.boston.csb/
---

# [PATCH v1] rteval: Covering edge cases in multi-stressor support

来源：[https://lore.kernel.org/linux-rt-users/au4t5C1-WpgWChOm@sansshar-thinkpadp1gen4i.boston.csb/](https://lore.kernel.org/linux-rt-users/au4t5C1-WpgWChOm@sansshar-thinkpadp1gen4i.boston.csb/)

```
Added a number of unit and integration tests for edga case coverage
Also added some logic to multi-stressor support to de-duplicate values
and cleans up trailing spaces and commas.

Signed-off-by: Sana Sharma <sansshar@redhat.com>
---
 rteval/modules/loads/stressng.py | 46 ++++++++++++++++++++---
 tests/test_stressng.py           | 64 ++++++++++++++++++++++++++------
 2 files changed, 93 insertions(+), 17 deletions(-)

diff --git a/rteval/modules/loads/stressng.py b/rteval/modules/loads/stressng.py
index a3f8d6f..ec59bf9 100644
--- a/rteval/modules/loads/stressng.py
+++ b/rteval/modules/loads/stressng.py
@@ -7,14 +7,26 @@ import subprocess
 import signal
 import sys
 import warnings
+import re
 from rteval.modules.loads import CommandLineLoad
 from rteval.Log import Log
 from rteval.systopology import SysTopology
 from rteval.cpulist_utils import CpuList
 from rteval.cpuset import cpuset_preexec
 
+def validate_workers(workers):
+    try:
+        workers_int = int(workers)
+    except:
+        raise TypeError("Invalid stress-ng workers: Needs to be int")
+    if ( workers_int >= 0):
+        return workers
+    else:
+        raise ValueError("Invalid stress-ng workers >=0" )
+
+
 def validate_stressors(stressor_list):
-    """Validate multiple stressor names.
+    """Validate multiple stressor names, cleaning up all formatting anomalies.
 
     Args:
         stressor_list: stressor names to validate, either as a list
@@ -25,20 +37,39 @@ def validate_stressors(stressor_list):
         ValueError: If any stressor is invalid
     """
     valid = get_valid_stressors()
+
+    # Normalize input types safely (handles strings, lists, tuples, or None)
     if isinstance(stressor_list, str):
-        stressor_list = stressor_list.split(",")
-    stressors = [word.strip() for word in stressor_list]
+        raw_items = [stressor_list]
+    elif isinstance(stressor_list, (list, tuple)):
+        raw_items = [str(item) for item in stressor_list if item is not None]
+    else:
+        raw_items = []
+
+    # Aggressively split out any continuous sequence of commas and whitespace
+    stressors = []
+    for item in raw_items:
+        parts = re.split(r'[,\s]+', item)
+        for part in parts:
+            if part:  # Effectively skips empty entries like '', ' ', ','
+                stressors.append(part)
+
+    # de-duplicate stressors
+    stressors = list(dict.fromkeys(stressors))
+
+    # Validate against valid stress-ng options
     invalid = []
     for stressor in stressors:
         if stressor not in valid:
             invalid.append(stressor)
-            continue
 
     if invalid:
         raise ValueError(f"Invalid stress-ng stressors: {', '.join(invalid)}. "
-                        f"Run 'stress-ng --stressors' to see valid options.")
+                         f"Run 'stress-ng --stressors' to see valid options.")
+
     return stressors
 
+
 def get_valid_stressors():
     """Query stress-ng for list of valid stressor names."""
     try:
@@ -68,6 +99,9 @@ class Stressng(CommandLineLoad):
         " Warn if both stressor and stressors are invoked "
         if (self.cfg.stressors is not None and self.cfg.stressor is not None):
             warnings.warn("In cases where stressng-stressor and stressng-stressors are both invoked, rteval will choose only stressors")
+        elif (self.cfg.stressors is None and self.cfg.stressor is None):
+            warnings.warn("Stress-ng will not run as no stressor has been invoked")
+            self._donotrun = True
         " Only run this module if the user specifies an stressor "
         if (hasattr(self.cfg, 'stressors') and self.cfg.stressors is not None):
             self._donotrun = False
@@ -101,7 +135,7 @@ class Stressng(CommandLineLoad):
         # stress-ng is only run if the user specifies an stressor
         self.args = ['stress-ng']
         stressors = validate_stressors(self.cfg.stressors)
-        workers = str(self.cfg.workers)  # defaults to '0'
+        workers = validate_workers(self.cfg.workers)  # defaults to '0'
         for stressor in stressors:
             self.args.extend([f'--{stressor}', workers])
         if self.cfg.timeout is not None:
diff --git a/tests/test_stressng.py b/tests/test_stressng.py
index d854a69..090822a 100644
--- a/tests/test_stressng.py
+++ b/tests/test_stressng.py
@@ -13,6 +13,22 @@ from pathlib import Path
 sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
 from rteval.modules.loads import stressng
 
+class TestValidateWorkers(unittest.TestCase):
+    """Test suite for the function validate_workers"""
+    def test_valid_passes(self):
+        """Test that a valid worker count is accepted"""
+        stressng.validate_workers('3')   # should not raise
+
+    def test_neg_int_fails(self):
+        """Test that a invalid worker count is rejected"""
+        with self.assertRaises(ValueError):
+            stressng.validate_workers('-1')   # should not raise
+
+    def test_non_num_fails(self):
+        """Test that a invalid worker type is rejected"""
+        with self.assertRaises(TypeError):
+             stressng.validate_workers('cpu')   # should not raise
+
 class TestGetValidStressors(unittest.TestCase):
     """Test suite for the function get_valid_stressors"""
 
@@ -41,18 +57,45 @@ class TestValidateStressor(unittest.TestCase):
     """Test suite for the function validate_stressor"""
 
     @patch('rteval.modules.loads.stressng.get_valid_stressors',
-           return_value=['cpu', 'vm'])
+            return_value=['cpu', 'vm'])
     def test_valid_passes(self, _):
         """Test that a valid stressor is accepted"""
         stressng.validate_stressors('cpu, vm')   # should not raise
 
     @patch('rteval.modules.loads.stressng.get_valid_stressors',
            return_value=['cpu', 'vm'])
-    def test_invalid_exits(self, _):
+    def test_patial_invalid_fails(self, _):
+        """Test that a valid stressor is rejected"""
+        with self.assertRaises(ValueError):
+            stressng.validate_stressors('cpu, bogus')   # should raise
+
+    @patch('rteval.modules.loads.stressng.get_valid_stressors',
+           return_value=['cpu', 'vm'])
+    def test_invalid_fails(self, _):
         """Test that an invalid stressor is rejected"""
         with self.assertRaises(ValueError):
             stressng.validate_stressors('bogus')
 
+    @patch('rteval.modules.loads.stressng.get_valid_stressors',
+           return_value=['cpu', 'vm'])
+    def test_multiple_invalid_fails(self, _):
+        """Test that a list of invalid stressors is rejected"""
+        with self.assertRaises(ValueError):
+            stressng.validate_stressors('fake, bogus')
+
+    @patch('rteval.modules.loads.stressng.get_valid_stressors',
+           return_value=['cpu', 'vm'])
+    def test_invalid_case_fails(self, _):
+        """Test that an invalid stressor is rejected"""
+        with self.assertRaises(ValueError):
+            stressng.validate_stressors('CPU, VM')
+
+    @patch('rteval.modules.loads.stressng.get_valid_stressors',
+           return_value=['cpu', 'vm'])
+    def test_extra_comma_passes(self, _):
+        """Test that extra commas are accepted"""
+        stressng.validate_stressors('cpu,vm,,')
+
 
 """Integration Tests for stress_ng stressor functionality"""
 
@@ -91,14 +134,13 @@ class TestSingleStressor(unittest.TestCase):
         assert "stressng: stress-ng --cpu 3 --taskset" in result.stdout
 
     def test_single_with_multi(self):
-        """Tests that passing multiple stressors with the single stressor argument raises a Value Error """
+        """Tests that passing multiple stressors with the single stressor argument works """
         result = subprocess.run(
             ["./rteval-cmd", "--stressng-stressor", "cpu,vm", "--stressng-workers", "3","-d","5","--measurement-module","timerlat"],
             capture_output=True,
             text=True
         )
-        assert result.returncode != 0
-        assert "ValueError
```
