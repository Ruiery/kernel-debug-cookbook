---
title: [PATCH v1] rteval: Added multi stressor support
list: linux-rt-users
message_id: arwPN52esmki-k_f@fedora
link: https://lore.kernel.org/linux-rt-users/arwPN52esmki-k_f@fedora/
---

# [PATCH v1] rteval: Added multi stressor support

来源：[https://lore.kernel.org/linux-rt-users/arwPN52esmki-k_f@fedora/](https://lore.kernel.org/linux-rt-users/arwPN52esmki-k_f@fedora/)

```
Added the ability for rteval to take multiple stressors in one
command. The syntax works as follows:

--stressng-stressor cpu --stressng-stressor vm --stressng-workers 2
will use 2 workers for each  stressor (in this case cpu and vm)

--stressng-stressors cpu,vm --stressng-workers 2
will use 2 workers for each stressor as in the above example

The second option exists to allow the user to access multiple
stressors in an easier way.

The tests/test_stressng file has also been updated to reflect
these changes.

Signed-off-by: Sana Sharma <sansshar@redhat.com>
---
 rteval/modules/__init__.py       |  3 +-
 rteval/modules/loads/stressng.py | 59 ++++++++++++++++++++++++--------
 tests/test_stressng.py           |  7 ++--
 3 files changed, 49 insertions(+), 20 deletions(-)

diff --git a/rteval/modules/__init__.py b/rteval/modules/__init__.py
index 183efd8..a89d452 100644
--- a/rteval/modules/__init__.py
+++ b/rteval/modules/__init__.py
@@ -356,6 +356,7 @@ reference from the first import"""
             for (o, s) in list(opts.items()):
                 descr = 'descr' in s and s['descr'] or ""
                 metavar = 'metavar' in s and s['metavar'] or None
+                action = 'action' in s and s['action'] or 'store'
 
                 try:
                     default = cfg and getattr(cfg, o) or None
@@ -369,7 +370,7 @@ reference from the first import"""
 
                 grparser.add_argument(f'--{shortmod}-{o}',
                                          dest=f"{shortmod}___{o}",
-                                         action='store',
+                                         action=action,
                                          help='%s%s' % (descr,
                                                         default and ' (default: %s)' % default or ''),
                                          default=default,
diff --git a/rteval/modules/loads/stressng.py b/rteval/modules/loads/stressng.py
index 564e798..24dd7a2 100644
--- a/rteval/modules/loads/stressng.py
+++ b/rteval/modules/loads/stressng.py
@@ -1,5 +1,6 @@
 # SPDX-License-Identifier: GPL-2.0-or-later
 """ Module containing class Stressng to manage stress-ng as an rteval load """
+import argparse
 import os
 import os.path
 import time
@@ -12,6 +13,32 @@ from rteval.systopology import SysTopology
 from rteval.cpulist_utils import CpuList
 from rteval.cpuset import cpuset_preexec
 
+def validate_stressors(stressor_list):
+    """Validate multiple stressor names.
+
+    Args:
+        stressor_list: stressor names to validate, either as a list
+                       (from repeated --stressng-stressor) or a
+                       comma-separated string (from --stressng-stressors)
+
+    Raises:
+        ValueError: If any stressor is invalid
+    """
+    valid = get_valid_stressors()
+    if isinstance(stressor_list, str):
+        stressor_list = stressor_list.split(",")
+    stressors = [word.strip() for word in stressor_list]
+    invalid = []
+    for stressor in stressors:
+        if stressor not in valid:
+            invalid.append(stressor)
+            continue
+
+    if invalid:
+        raise ValueError(f"Invalid stress-ng stressors: {', '.join(invalid)}. "
+                        f"Run 'stress-ng --stressors' to see valid options.")
+    return stressors
+
 def get_valid_stressors():
     """Query stress-ng for list of valid stressor names."""
     try:
@@ -25,14 +52,6 @@ def get_valid_stressors():
         print(f"Failed to query stress-ng stressors: {e}")
         sys.exit(1)
 
-def validate_stressor(stressor_name):
-    """Validate a single stressor name against stress-ng's available stressors."""
-    valid = get_valid_stressors()
-    if stressor_name not in valid:
-        print(f"Invalid stress-ng stressor: '{stressor_name}'. "
-              f"Run 'stress-ng --stressors' to see valid options.")
-        sys.exit(1)
-
 class Stressng(CommandLineLoad):
     " This class creates a load module that runs stress-ng "
     def __init__(self, config, logger):
@@ -47,10 +66,14 @@ class Stressng(CommandLineLoad):
         self.__nullfp = None
         self.args = None
         " Only run this module if the user specifies an stressor "
-        if self.cfg.stressor is not None:
+        if (hasattr(self.cfg, 'stressor') and self.cfg.stressor is not None):
+            setattr(self.cfg, 'stressors', list(self.cfg.stressor))
+            self._donotrun = False
+        elif (hasattr(self.cfg, 'stressors') and self.cfg.stressors is not None):
             self._donotrun = False
         else:
             self._donotrun = True
+
         # When this module runs, other load modules should not
         self.set_exclusive()
 
@@ -74,10 +97,10 @@ class Stressng(CommandLineLoad):
 
         # stress-ng is only run if the user specifies an stressor
         self.args = ['stress-ng']
-        validate_stressor(self.cfg.stressor)
-        self.args.append(f'--{str(self.cfg.stressor)}')
-        if self.cfg.workers is not None:
-            self.args.append(self.cfg.workers) #default is 0
+        stressors = validate_stressors(self.cfg.stressors)
+        workers = str(self.cfg.workers)  # defaults to '0'
+        for stressor in stressors:
+            self.args.extend([f'--{stressor}', workers])
         if self.cfg.timeout is not None:
             self.args.append('--timeout')
             self.args.append(self.cfg.timeout)
@@ -164,8 +187,14 @@ def ModuleParameters():
     """ Commandline options for Stress-ng """
     return {
         "stressor": {
-            "descr": "stressor name (eg. vm, cpu)",
-            "metavar": "STRESSOR"
+            "descr": "stressor to run; repeat the flag to run several in parallel "
+                     "(e.g., --stressng-stressor cpu --stressng-stressor vm)",
+            "action": "append",
+            "metavar": "NAME"
+        },
+        "stressors": {
+            "descr": "comma-separated stressors to run in parallel (e.g., cpu,vm,io)",
+            "metavar": "LIST"
         },
         "workers": {
             "descr": "number of workers(default: 0 = one per CPU)",
diff --git a/tests/test_stressng.py b/tests/test_stressng.py
index 6211fb3..29291e6 100644
--- a/tests/test_stressng.py
+++ b/tests/test_stressng.py
@@ -41,15 +41,14 @@ class TestValidateStressor(unittest.TestCase):
            return_value=['cpu', 'vm'])
     def test_valid_passes(self, _):
         """Test that a valid stressor is accepted"""
-        stressng.validate_stressor('cpu')   # should not raise
+        stressng.validate_stressors('cpu, vm')   # should not raise
 
     @patch('rteval.modules.loads.stressng.get_valid_stressors',
            return_value=['cpu', 'vm'])
     def test_invalid_exits(self, _):
         """Test that an invalid stressor is rejected"""
-        with self.assertRaises(SystemExit) as cm:
-            stressng.validate_stressor('bogus')
-        self.assertEqual(cm.exception.code, 1)
+        with self.assertRaises(ValueError):    
+            stressng.validate_stressors('bogus')
 
 def main():
     """Run the test suite"""
-- 
2.54.0


-- 
Sana Sharma <sansshar@redhat.com>
```
