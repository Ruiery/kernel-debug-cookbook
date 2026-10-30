---
title: [PATCH v1] rteval: Added integration tests multi stressor support in stress-ng
list: linux-rt-users
message_id: auSgczD-qWxJhBbC@fedora
link: https://lore.kernel.org/linux-rt-users/auSgczD-qWxJhBbC@fedora/
---

# [PATCH v1] rteval: Added integration tests multi stressor support in stress-ng

来源：[https://lore.kernel.org/linux-rt-users/auSgczD-qWxJhBbC@fedora/](https://lore.kernel.org/linux-rt-users/auSgczD-qWxJhBbC@fedora/)

```
Added integrations test that checked the single-stressor and
multi-stressor support as well as the cpuset logic in this
context.

Assisted-by: Claude Opus 4.8
Signed-off-by: Sana Sharma <sansshar@redhat.com>
---
 tests/test_stressng.py | 239 ++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 238 insertions(+), 1 deletion(-)

diff --git a/tests/test_stressng.py b/tests/test_stressng.py
index 29291e6..d684ff6 100644
--- a/tests/test_stressng.py
+++ b/tests/test_stressng.py
@@ -6,8 +6,11 @@
 import sys
 import subprocess
 import unittest
+from types import SimpleNamespace
 from unittest.mock import patch, MagicMock
-sys.path.insert(0,'.')
+from pathlib import Path
+
+sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
 from rteval.modules.loads import stressng
 
 class TestGetValidStressors(unittest.TestCase):
@@ -50,6 +53,240 @@ class TestValidateStressor(unittest.TestCase):
         with self.assertRaises(ValueError):    
             stressng.validate_stressors('bogus')
 
+
+"""Integration Tests for stress_ng stressor functionality"""
+
+class TestSingleStressor(unittest.TestCase):
+    """Test suite for single stressor case"""
+
+    def test_no_stressor_single(self):
+        """Test that the single stressor argument with no stressors throws the correct error"""
+        result = subprocess.run(
+            ["./rteval-cmd", "--stressng-stressor"],
+            capture_output=True,
+            text=True
+        )
+        assert result.returncode != 0
+        assert "usage: rteval-cmd" in result.stderr
+        assert "rteval-cmd: error: argument --stressng-stressor: expected one argument" in result.stderr
+
+    def test_default_worker_single(self):
+        """Test that for the single stressor the undefined workers defaults to 0"""
+        result = subprocess.run(
+            ["./rteval-cmd", "--stressng-stressor", "cpu"],
+            capture_output=True,
+            text=True
+        )
+        assert result.returncode == 0
+        assert "stressng: stress-ng --cpu 0 --taskset" in result.stdout
+
+    def test_set_worker_single(self):
+        """Test that single stressor with a set number of workers passes the number through"""
+        result = subprocess.run(
+            ["./rteval-cmd", "--stressng-stressor", "cpu", "--stressng-workers", "3"],
+            capture_output=True,
+            text=True
+        )
+        assert result.returncode == 0
+        assert "stressng: stress-ng --cpu 3 --taskset" in result.stdout
+
+    def test_single_with_multi(self):
+        """Tests that passing multiple stressors with the single stressor argument raises a Value Error """
+        result = subprocess.run(
+            ["./rteval-cmd", "--stressng-stressor", "cpu,vm", "--stressng-workers", "3"],
+            capture_output=True,
+            text=True
+        )
+        assert result.returncode != 0
+        assert "ValueError: Invalid stress-ng stressors: cpu,vm. Run 'stress-ng --stressors' to see valid options." in result.stderr
+
+    def test_multiple_singles(self):
+        """Tests that when multiple single stressors are passed with single arguments the code runs all the stressors """
+        result = subprocess.run(
+            ["./rteval-cmd", "--stressng-stressor", "cpu", "--stressng-stressor", "vm", "--stressng-workers", "3"],
+            capture_output=True,
+            text=True
+        )
+        assert result.returncode == 0
+        assert "stressng: stress-ng --cpu 3 --vm 3 --taskset" in result.stdout
+
+class TestMultiStressor(unittest.TestCase):
+
+    def test_no_stressor_multi(self):
+        """Tests that multi stressors with no stressor name leads to an error"""
+        result = subprocess.run(
+            ["./rteval-cmd", "--stressng-stressors"],
+            capture_output=True,
+            text=True
+        )
+        assert result.returncode != 0
+        assert "usage: rteval-cmd" in result.stderr
+        assert "rteval-cmd: error: argument --stressng-stressors: expected one argument" in result.stderr
+
+    def test_one_stressor_multi(self):
+        """Tests that multiple stressors with one stressor argument works"""
+        result = subprocess.run(
+            ["./rteval-cmd", "--stressng-stressors","cpu"],
+            capture_output=True,
+            text=True
+        )
+        assert result.returncode == 0
+        assert "stressng: stress-ng --cpu 0 --taskset" in result.stdout
+
+    def test_multi_stressor_default_workers(self):
+        """Tests that the default workers is 0"""
+        result = subprocess.run(
+            ["./rteval-cmd", "--stressng-stressors", "cpu,vm"],
+            capture_output=True,
+            text=True
+        )
+        assert result.returncode == 0
+        assert "stressng: stress-ng --cpu 0 --vm 0 --taskset" in result.stdout
+
+    def test_multi_stressor_set_workers(self):
+        """Tests that multiple stressors with a set number of workers passes correctly"""
+        result = subprocess.run(
+            ["./rteval-cmd", "--stressng-stressors", "cpu,vm", "--stressng-workers", "2"],
+            capture_output=True,
+            text=True
+        )
+        assert result.returncode == 0
+        assert "stressng: stress-ng --cpu 2 --vm 2 --taskset" in result.stdout
+
+class TestWorkloadPrepareCpuset(unittest.TestCase):
+    """
+    Integration tests for the cpuset/taskset logic in _WorkloadPrepare.
+
+    Each scenario is exercised for both ways of configuring stressors:
+      * single stressor form  -> cfg.stressors is a list, e.g. ['cpu']
+        (this is what __init__ produces from --stressng-stressor)
+      * multi stressor form   -> cfg.stressors is a comma-separated string,
+        e.g. 'cpu,vm' (this comes from --stressng-stressors)
+    """
+
+    # stressor configs covered by every cpuset scenario: (label, cfg.stressors,
+    # expected --<flag> options that should land in args)
+    STRESSOR_FORMS = (
+        ("single", ['cpu'], ['--cpu']),
+        ("multi", 'cpu,vm', ['--cpu', '--vm']),
+    )
+
+    @staticmethod
+    def make_stressng(stressors, workers='0', timeout=None, cpulist=""):
+        """Build a Stressng instance without running the heavy __init__.
+
+        Only the attributes read by _WorkloadPrepare() are populated. The
+        cfg.stressors attribute mirrors what __init__ would store: a list for
+        the single-stressor flag, or a comma-separated string for the
+        multi-stressor flag.
+        """
+        inst = stressng.Stressng.__new__(stressng.Stressng)
+        inst.cfg = SimpleNamespace(stressors=stressors, workers=workers,
+                                   timeout=timeout)
+        inst.cpulist = cpulist
+        inst._logging = False
+        inst._log = MagicMock()
+        inst.args = None
+        return inst
+
+    @staticmethod
+    def taskset_arg(args):
+        """Return the value following --taskset, or None if not present."""
+        if '--taskset' not in args:
+            return None
+        return args[args.index('--taskset') + 1]
+
+    @patch('rteval.modules.loads.stressng.get_valid_stressors',
+           return_value=['cpu', 'vm', 'matrix', 'io'])
+    @patch('rteval.modules.loads.stressng.os.open', return_value=42)
+    @patch('rteval.modules.loads.stressng.SysTopology')
+    def test_cpulist_restricts_taskset(self, mock_systop, _mock_open, _mock_valid):
+        """A cpulist keeps only its CPUs, intersected per node."""
+        topo = mock_systop.return_value
+        topo.getnodes.return_value = [0, 1]
+        topo.getcpus.side_effect = lambda n: {0: [0, 1, 2, 3],
+                                              1: [4, 5, 6, 7]}[n]
+
+        for label, stressors, flags in self.STRESSOR_FORMS:
+            with self.subTest(form=label):
+                s = self.make_stressng(stressors=stressors, cpulist="0,1,4,5")
+                s._WorkloadPrepare()
+
+                self.assertEqual(self.taskset_arg(s.args), "0,1,4,5")
+                for flag i
```
