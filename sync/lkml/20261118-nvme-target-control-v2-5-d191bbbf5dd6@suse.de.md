---
title: [PATCH blktests v2 5/9] contrib/nvme-target-control: list the DH-HMAC-CHAP algorithms
list: linux-block
message_id: 20261118-nvme-target-control-v2-5-d191bbbf5dd6@suse.de
link: https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-5-d191bbbf5dd6@suse.de/
---

# [PATCH blktests v2 5/9] contrib/nvme-target-control: list the DH-HMAC-CHAP algorithms

来源：[https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-5-d191bbbf5dd6@suse.de/](https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-5-d191bbbf5dd6@suse.de/)

```
Not all targets support all DH-HMAC-CHAP hashes and DH groups, e.g.
ONTAP doesn't support SHA-384. List the ones a target supports as
features, e.g. dhchap-sha384 or dhchap-ffdhe2048, so that the tests can
check for them. The nvmet target lists all of them.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 contrib/nvme-target-control/README.md                  | 11 +++++++----
 .../nvme-target-control/nvme_target_control/target.py  | 18 ++++++++++++++++++
 .../nvme_target_control/targets/nvmet.py               | 12 +++++++++++-
 .../nvme-target-control/tests/test_target_control.py   |  4 +++-
 4 files changed, 39 insertions(+), 6 deletions(-)

diff --git a/contrib/nvme-target-control/README.md b/contrib/nvme-target-control/README.md
index 9abd7f30932d..8afbfc0be322 100644
--- a/contrib/nvme-target-control/README.md
+++ b/contrib/nvme-target-control/README.md
@@ -118,10 +118,13 @@ channel is a subclass of `Channel` which returns the command running
 The port commands and `set-host` are optional. A target implements them
 by overriding `add_ports`, `add_port`, `remove_port`, `list_ports`,
 `show_port`, `set_ana` and `set_host`. `config --show-features` lists the
-ones it overrides, followed by the class attribute `extra_features`, e.g.
-`tls`. blktests skips the tests which need a feature the target doesn't
-list. Without `list-ports` and `show-port`, blktests connects to `traddr`
-and `trsvid`.
+ones it overrides, followed by the class attribute `extra_features`: the
+DH-HMAC-CHAP hashes and DH groups the target supports, e.g.
+`dhchap-sha256` or `dhchap-ffdhe2048` (`dhchap_features()` builds them),
+and `tls` if it sets up TLS. blktests skips the tests which need a
+feature the target doesn't list, and the steps of nvme/042 and nvme/043
+which use an algorithm the target doesn't list. Without `list-ports` and
+`show-port`, blktests connects to `traddr` and `trsvid`.
 
 ## Development
 
diff --git a/contrib/nvme-target-control/nvme_target_control/target.py b/contrib/nvme-target-control/nvme_target_control/target.py
index d648826e0386..1b3576bffbbf 100644
--- a/contrib/nvme-target-control/nvme_target_control/target.py
+++ b/contrib/nvme-target-control/nvme_target_control/target.py
@@ -11,6 +11,7 @@ API, can be added as 'package.module:Class' in the [target] 'type' option.
 
 import socket
 from abc import ABC, abstractmethod
+from collections.abc import Iterable
 from dataclasses import dataclass
 from pathlib import Path
 from typing import Any, ClassVar
@@ -23,6 +24,23 @@ DEF_SUBSYSNQN = 'blktests-subsystem-1'
 DEF_SUBSYS_UUID = '91fdba0d-f87b-4c25-b80f-db7be1418b9e'
 DEF_TRSVCID = '4420'
 
+# The DH-HMAC-CHAP hashes and DH groups, named as in the nvmet configfs
+# without hmac() around the hash
+DHCHAP_HASHES = ('sha256', 'sha384', 'sha512')
+DHCHAP_DHGROUPS = (
+    'null',
+    'ffdhe2048',
+    'ffdhe3072',
+    'ffdhe4096',
+    'ffdhe6144',
+    'ffdhe8192',
+)
+
+
+def dhchap_features(algorithms: Iterable[str]) -> tuple[str, ...]:
+    """Return the features for the DH-HMAC-CHAP hashes and DH groups."""
+    return tuple(f'dhchap-{alg}' for alg in algorithms)
+
 
 @dataclass(frozen=True)
 class Subsystem:
diff --git a/contrib/nvme-target-control/nvme_target_control/targets/nvmet.py b/contrib/nvme-target-control/nvme_target_control/targets/nvmet.py
index f5f2e8cc2a62..468417f2ca7e 100644
--- a/contrib/nvme-target-control/nvme_target_control/targets/nvmet.py
+++ b/contrib/nvme-target-control/nvme_target_control/targets/nvmet.py
@@ -24,7 +24,15 @@ from pathlib import Path
 from typing import Any
 
 from .. import channel
-from ..target import Port, Subsystem, Target, resolve
+from ..target import (
+    DHCHAP_DHGROUPS,
+    DHCHAP_HASHES,
+    Port,
+    Subsystem,
+    Target,
+    dhchap_features,
+    resolve,
+)
 
 SCRIPT = Path(__file__).resolve().parent / 'nvmet.sh'
 
@@ -40,6 +48,8 @@ HOST_ATTRS = {
 class NvmetTarget(Target):
     """Linux nvmet target."""
 
+    extra_features = dhchap_features(DHCHAP_HASHES + DHCHAP_DHGROUPS)
+
     def __init__(self, config: dict[str, Any]) -> None:
         super().__init__(config)
         self.channel = channel.create(config)
diff --git a/contrib/nvme-target-control/tests/test_target_control.py b/contrib/nvme-target-control/tests/test_target_control.py
index 730d6c8a9b69..c6d8933b6212 100644
--- a/contrib/nvme-target-control/tests/test_target_control.py
+++ b/contrib/nvme-target-control/tests/test_target_control.py
@@ -160,7 +160,9 @@ type = "fake_array:RecordingTarget"
         self.assertEqual(
             self.show('features'),
             'add-ports add-port remove-port list-ports show-port set-ana '
-            'set-host',
+            'set-host dhchap-sha256 dhchap-sha384 dhchap-sha512 dhchap-null '
+            'dhchap-ffdhe2048 dhchap-ffdhe3072 dhchap-ffdhe4096 '
+            'dhchap-ffdhe6144 dhchap-ffdhe8192',
         )
         self.config.write_text(PLUGIN)
         self.assertEqual(self.show('features'), '')

-- 
2.56.1
```
