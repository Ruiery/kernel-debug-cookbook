---
title: [PATCH v2] rteval: Fixed hardcoded paths in class TestCpusetManagerCLIIntegration
list: linux-rt-users
message_id: auI9GfqN-g0YtJhD@fedora
link: https://lore.kernel.org/linux-rt-users/auI9GfqN-g0YtJhD@fedora/
---

# [PATCH v2] rteval: Fixed hardcoded paths in class TestCpusetManagerCLIIntegration

来源：[https://lore.kernel.org/linux-rt-users/auI9GfqN-g0YtJhD@fedora/](https://lore.kernel.org/linux-rt-users/auI9GfqN-g0YtJhD@fedora/)

```
This patch makes 2 changes to the tests/test_cpusetmanager.py file
1. The hardcoded paths introduced in commit 6227294897b7 ("rteval:
Add --housekeeping-isolated flag") have been made generic
2. The os.path.dirname invocation has been replaced with a more
modern pathlib module since I was importing it for the fix.

Signed-off-by: Sana Sharma <sansshar@redhat.com>
---
Changes since v1: Fixed assumption that the repo will be named
rteval.

 tests/test_cpusetmanager.py | 22 ++++++++++++----------
 1 file changed, 12 insertions(+), 10 deletions(-)

diff --git a/tests/test_cpusetmanager.py b/tests/test_cpusetmanager.py
index 3f1c4b4..1f9789a 100644
--- a/tests/test_cpusetmanager.py
+++ b/tests/test_cpusetmanager.py
@@ -13,10 +13,10 @@ import os
 import sys
 import subprocess
 import tempfile
+from pathlib import Path
 
 # Add parent directory to path for imports
-sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
-
+sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
 from rteval.cpusetmanager import CpusetManager
 from rteval import cpuset
 from rteval.Log import Log
@@ -209,6 +209,8 @@ class TestCpusetManagerHousekeepingPartitions(unittest.TestCase):
 class TestCpusetManagerCLIIntegration(unittest.TestCase):
     """Test rteval-cmd integration with --housekeeping-isolated"""
 
+    srcdir = str(Path(__file__).resolve().parent.parent)
+
     def setUp(self):
         """Clean up before each test"""
         try:
@@ -226,7 +228,7 @@ class TestCpusetManagerCLIIntegration(unittest.TestCase):
     def test_housekeeping_isolated_requires_cpusets(self):
         """Test that --housekeeping-isolated requires --cpusets"""
         result = subprocess.run(
-            [sys.executable, '/home/jkacur/src/rteval/rteval-cmd',
+            [sys.executable,  f"{self.srcdir}/rteval-cmd",
              '--housekeeping', '0-1', '--housekeeping-isolated',
              '--duration', '1', '--onlyload'],
             capture_output=True,
@@ -241,7 +243,7 @@ class TestCpusetManagerCLIIntegration(unittest.TestCase):
     def test_measurement_member_requires_cpusets(self):
         """Test that --measurement-member requires --cpusets"""
         result = subprocess.run(
-            [sys.executable, '/home/jkacur/src/rteval/rteval-cmd',
+            [sys.executable,  f"{self.srcdir}/rteval-cmd",
              '--measurement-member',
              '--duration', '1', '--onlyload'],
             capture_output=True,
@@ -256,7 +258,7 @@ class TestCpusetManagerCLIIntegration(unittest.TestCase):
     def test_measurement_member_help_text(self):
         """Test that --measurement-member appears in help"""
         result = subprocess.run(
-            [sys.executable, '/home/jkacur/src/rteval/rteval-cmd', '--help'],
+            [sys.executable,  f"{self.srcdir}/rteval-cmd", '--help'],
             capture_output=True,
             text=True
         )
@@ -270,7 +272,7 @@ class TestCpusetManagerCLIIntegration(unittest.TestCase):
     def test_loads_cpuset_requires_cpusets(self):
         """Test that --loads-cpuset requires --cpusets"""
         result = subprocess.run(
-            [sys.executable, '/home/jkacur/src/rteval/rteval-cmd',
+            [sys.executable,  f"{self.srcdir}/rteval-cmd",
              '--loads-cpuset',
              '--duration', '1', '--onlyload'],
             capture_output=True,
@@ -285,7 +287,7 @@ class TestCpusetManagerCLIIntegration(unittest.TestCase):
     def test_loads_cpuset_help_text(self):
         """Test that --loads-cpuset appears in help"""
         result = subprocess.run(
-            [sys.executable, '/home/jkacur/src/rteval/rteval-cmd', '--help'],
+            [sys.executable,  f"{self.srcdir}/rteval-cmd", '--help'],
             capture_output=True,
             text=True
         )
@@ -299,7 +301,7 @@ class TestCpusetManagerCLIIntegration(unittest.TestCase):
     def test_housekeeping_isolated_requires_housekeeping(self):
         """Test that --housekeeping-isolated requires --housekeeping"""
         result = subprocess.run(
-            [sys.executable, '/home/jkacur/src/rteval/rteval-cmd',
+            [sys.executable,  f"{self.srcdir}/rteval-cmd",
              '--cpusets', '--housekeeping-isolated',
              '--duration', '1', '--onlyload'],
             capture_output=True,
@@ -314,7 +316,7 @@ class TestCpusetManagerCLIIntegration(unittest.TestCase):
     def test_housekeeping_isolated_help_text(self):
         """Test that --housekeeping-isolated appears in help"""
         result = subprocess.run(
-            [sys.executable, '/home/jkacur/src/rteval/rteval-cmd', '--help'],
+            [sys.executable,  f"{self.srcdir}/rteval-cmd", '--help'],
             capture_output=True,
             text=True
         )
@@ -328,7 +330,7 @@ class TestCpusetManagerCLIIntegration(unittest.TestCase):
     def test_housekeeping_help_text_accuracy(self):
         """Test that --housekeeping help text is accurate (no longer says 'isolated CPUs')"""
         result = subprocess.run(
-            [sys.executable, '/home/jkacur/src/rteval/rteval-cmd', '--help'],
+            [sys.executable,  f"{self.srcdir}/rteval-cmd", '--help'],
             capture_output=True,
             text=True
         )
-- 
2.54.0


-- 
Sana Sharma <sansshar@redhat.com>
```
