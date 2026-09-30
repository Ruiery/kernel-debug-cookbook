---
title: [PATCH v4] rt-eval: Adding stressor validation for stress-ng
list: linux-rt-users
message_id: ao8MMPPQAnmLMHi3@fedora
link: https://lore.kernel.org/linux-rt-users/ao8MMPPQAnmLMHi3@fedora/
---

# [PATCH v4] rt-eval: Adding stressor validation for stress-ng

来源：[https://lore.kernel.org/linux-rt-users/ao8MMPPQAnmLMHi3@fedora/](https://lore.kernel.org/linux-rt-users/ao8MMPPQAnmLMHi3@fedora/)

```
Previously stressor names were unvalidated.
This has been changed so that now if the user inputs an invalid
stressor name, they get an error message telling them to check
"stress-ng --help". The list of stressors is created dynamically
during "WorkloadPrepare()"

Added error handling for when stress-ng is not installed

Signed-off-by: Sana Sharma <sansshar@redhat.com>
---
 rteval/modules/loads/stressng.py | 23 +++++++++++++++++++++++
 1 file changed, 23 insertions(+)

diff --git a/rteval/modules/loads/stressng.py b/rteval/modules/loads/stressng.py
index 32e2dbd..df4685e 100644
--- a/rteval/modules/loads/stressng.py
+++ b/rteval/modules/loads/stressng.py
@@ -5,11 +5,33 @@ import os.path
 import time
 import subprocess
 import signal
+import sys
 from rteval.modules.loads import CommandLineLoad
 from rteval.Log import Log
 from rteval.systopology import SysTopology
 from rteval.cpulist_utils import CpuList
 
+def get_valid_stressors():
+    """Query stress-ng for list of valid stressor names."""
+    try:
+        result = subprocess.run(['stress-ng', '--stressors'],
+                                capture_output=True, text=True, check=True)
+        return result.stdout.strip().split()
+    except FileNotFoundError:
+        print("stress-ng is not installed. Please install the stress-ng package.")
+        sys.exit(1)
+    except subprocess.CalledProcessError as e:
+        print(f"Failed to query stress-ng stressors: {e}")
+        sys.exit(1)
+
+def validate_stressor(stressor_name):
+    """Validate a single stressor name against stress-ng's available stressors."""
+    valid = get_valid_stressors()
+    if stressor_name not in valid:
+        print(f"Invalid stress-ng stressor: '{stressor_name}'. "
+              f"Run 'stress-ng --stressors' to see valid options.")
+        sys.exit(1)
+
 class Stressng(CommandLineLoad):
     " This class creates a load module that runs stress-ng "
     def __init__(self, config, logger):
@@ -51,6 +73,7 @@ class Stressng(CommandLineLoad):
 
         # stress-ng is only run if the user specifies an stressor
         self.args = ['stress-ng']
+        validate_stressor(self.cfg.stressor)
         self.args.append(f'--{str(self.cfg.stressor)}')
         if self.cfg.workers is not None:
             self.args.append(self.cfg.workers) #default is 0
-- 
2.54.0


-- 
Sana Sharma <sansshar@redhat.com>
```
