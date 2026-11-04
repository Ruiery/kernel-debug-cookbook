---
title: [PATCH blktests 10/10] contrib/nvme-target-control: add a NetApp ONTAP target
list: linux-block
message_id: 20261104-nvme-target-control-v1-10-b31b40537bb4@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-10-b31b40537bb4@suse.de/
---

# [PATCH blktests 10/10] contrib/nvme-target-control: add a NetApp ONTAP target

来源：[https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-10-b31b40537bb4@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-10-b31b40537bb4@suse.de/)

```
A storage array is a target NVME_TARGET_CONTROL is meant for, and it
doesn't do everything the Linux nvmet target does. Add the ontap target,
which configures a NetApp ONTAP storage virtual machine through the
ONTAP REST API.

On first use the target creates a volume with one namespace. Setup
creates an NVMe subsystem, allows the host and maps the namespace. The
ports are the NVMe/TCP LIFs of the SVM. The target implements
list-ports, show-port and set-host, the tests which need other commands
or TLS skip. README.md documents the configuration and the limits.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 Documentation/running-tests.md                     |   3 +-
 contrib/nvme-target-control/README.md              |  48 +++
 .../nvme_target_control/target.py                  |   1 +
 .../nvme_target_control/targets/ontap.py           | 392 +++++++++++++++++++++
 contrib/nvme-target-control/tests/test_ontap.py    | 340 ++++++++++++++++++
 5 files changed, 783 insertions(+), 1 deletion(-)

diff --git a/Documentation/running-tests.md b/Documentation/running-tests.md
index 9ac55f2c6724..15c7672fade5 100644
--- a/Documentation/running-tests.md
+++ b/Documentation/running-tests.md
@@ -303,5 +303,6 @@ the tests which need a feature the list lacks.
   --dhgroup DHGROUP
 
 contrib/nvme-target-control implements this interface. It configures a Linux
-nvmet target over ssh and can be extended for other targets, see
+nvmet target over ssh or a NetApp ONTAP storage virtual machine through its
+REST API, and can be extended for other targets, see
 contrib/nvme-target-control/README.md.
diff --git a/contrib/nvme-target-control/README.md b/contrib/nvme-target-control/README.md
index dc421b00b788..5bd532cd7c2f 100644
--- a/contrib/nvme-target-control/README.md
+++ b/contrib/nvme-target-control/README.md
@@ -49,6 +49,7 @@ nothing, to run against a target which is configured already.
 | Type | Target |
 | --- | --- |
 | `nvmet` (default) | Linux nvmet target, configured through configfs |
+| `ontap` | NetApp ONTAP storage virtual machine, through the REST API |
 | `package.module:Class` | A `Target` subclass outside this package |
 
 ### nvmet
@@ -80,6 +81,53 @@ The target needs sshd, configfs, losetup and the nvmet modules for the
 transport. The ssh destination may be an alias from the ssh config, `traddr`
 is then its `HostName`.
 
+### ontap
+
+Configures a storage virtual machine (SVM) of a NetApp ONTAP cluster through
+the ONTAP REST API. blktests connects over NVMe/TCP to the LIFs of the SVM:
+
+    [target]
+    type = "ontap"
+    host = "192.0.2.100"
+    user = "admin"
+    password_file = "/root/.config/blktests/ontap-password"
+    svm = "svm1"
+    aggregate = "aggr1"
+
+The first time blktests asks for the subsystem UUID, the target creates the
+volume and the namespace `/vol/VOLUME/ns1` unless they exist. The volume
+gets no snapshots: the tests rewrite the namespace, snapshots would fill
+the volume. Setup creates the subsystem, allows the host and maps the
+namespace to it. Cleanup deletes the subsystem. The volume and namespace
+stay for the next run. The target caches the namespace UUID, the SVM UUID
+and the LIFs in `cache_dir`, and the DH-HMAC-CHAP secrets of the hosts,
+which ONTAP doesn't return.
+
+ONTAP derives the subsystem NQN from the subsystem name: `config
+--show-subsysnqn` shows the NQN of the subsystem `blktests`. The tests which
+use other NQNs need the NQN prefix of the SVM. The ports are the NVMe/TCP
+LIFs, numbered 1 to N by LIF name, each subsystem is reachable on all of
+them. The target implements `list-ports`, `show-port` and `set-host`.
+ONTAP can't modify the DH-HMAC-CHAP settings of a host: `set-host` removes
+the host and adds it again, which drops its connections. ONTAP manages the
+ANA states and doesn't support SHA-384. The target doesn't set up TLS.
+
+| Option | Meaning |
+| --- | --- |
+| `host` | cluster management address |
+| `user` | ONTAP user |
+| `password_file` | file with the password of `user` in its first line, mode 0600 |
+| `svm` | the SVM |
+| `aggregate` | aggregate for the volume, needed if it doesn't exist |
+| `volume` | volume of the namespace, default `blktests` |
+| `volume_size` | size of a new volume, default `4G` |
+| `ns_size` | size of a new namespace, default `2G` |
+| `verify_tls` | verify the certificate of `host`, default true |
+| `cache_dir` | default `~/.cache/nvme-target-control` |
+
+The user needs the rights to manage volumes, namespaces and NVMe
+subsystems of the SVM.
+
 ## Adding a target
 
 A target is a subclass of `nvme_target_control.target.Target`. It gets the
diff --git a/contrib/nvme-target-control/nvme_target_control/target.py b/contrib/nvme-target-control/nvme_target_control/target.py
index d648826e0386..8b2df2e6d6ac 100644
--- a/contrib/nvme-target-control/nvme_target_control/target.py
+++ b/contrib/nvme-target-control/nvme_target_control/target.py
@@ -210,6 +210,7 @@ OPTIONAL_COMMANDS = {
 
 TARGETS = {
     'nvmet': 'nvme_target_control.targets.nvmet:NvmetTarget',
+    'ontap': 'nvme_target_control.targets.ontap:OntapTarget',
 }
 
 
diff --git a/contrib/nvme-target-control/nvme_target_control/targets/ontap.py b/contrib/nvme-target-control/nvme_target_control/targets/ontap.py
new file mode 100644
index 000000000000..198303d1360e
--- /dev/null
+++ b/contrib/nvme-target-control/nvme_target_control/targets/ontap.py
@@ -0,0 +1,392 @@
+# SPDX-License-Identifier: GPL-3.0+
+# Copyright (c) 2026 SUSE LLC and contributors
+"""NetApp ONTAP storage virtual machine (SVM), through the ONTAP REST API.
+
+blktests connects over NVMe/TCP to the LIFs of the SVM. [target] options:
+
+  host           cluster management address
+  user           ONTAP user
+  password_file  file with the password of user in the first line
+  svm            the SVM
+  aggregate      aggregate for the volume, needed if it doesn't exist
+  volume         volume of the namespace, default 'blktests'
+  volume_size    size of the volume if it is created, default 4G
+  ns_size        size of the namespace if it is created, default 2G
+  verify_tls     verify the certificate of host, default true
+  cache_dir      default ~/.cache/nvme-target-control
+
+The first time blktests asks for the subsystem UUID, the target creates the
+volume, without snapshots, and the namespace /vol/VOLUME/ns1 unless they
+exist, and caches the namespace UUID, the SVM UUID and the LIFs. Setup
+creates an NVMe subsystem, allows the host and maps the namespace to it.
+Cleanup deletes the subsystem. The volume and namespace stay.
+
+ONTAP derives the subsystem NQN from the subsystem name and the SVM.
+'config --show-subsysnqn' shows the NQN of the subsystem 'blktests'. Other
+NQNs only work with the NQN prefix of the SVM.
+
+The ports are the NVMe/TCP LIFs, numbered 1..N by LIF name. Every
+subsystem is reachable on all of them. Ports can't be added or removed and
+ONTAP manages the ANA states. ONTAP can't modify the DH-HMAC-CHAP settings
+of a host: set-host removes the host and adds it again, which drops its
+connections. The target doesn't set up TLS.
+"""
+
+import base64
+import json
+import ssl
+import time
+import urllib.error
+import urllib.parse
+import urllib.request
+from pathlib import Path
+from typing import Any
+
+from ..target import Port, Subsystem, Target
+
+NQN_PREFIX = 'nqn.1992-08.com.netapp:sn.{}:subsystem.'
+DEF_SUBSYSTEM = 'blktests'
+
+# The names blktests uses for the DH-HMAC-CHAP hash and DH group, and the
+# ones ONTAP uses. ONTAP doesn't support SHA-384.
+HASHES = {
+    'hmac(sha256)': 'sha_256',
+    'hmac(sha512)': 'sha_512',
+}
+DHGROUPS = {
+    'null': 'none',
+    'ffdhe2048': '2048_bit',
+    'ffdhe3072': '3072_bit',
+    'ffdhe4096': '4096_bit',
+    'ffdhe6144': '6144_bit',
+    'ffdhe8192': '8192_bit',
+}
+
+
+class OntapError(OSError):
+    """An ONTAP REST request failed, status is its HTTP status."""
+
+    def __init__(self, message: str, status: int = 0) -> None:
+        super().__i
```
