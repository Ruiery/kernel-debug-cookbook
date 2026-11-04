---
title: [PATCH blktests 00/10] nvme: make NVME_TARGET_CONTROL work with remote targets
list: linux-block
message_id: 20261104-nvme-target-control-v1-0-b31b40537bb4@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-0-b31b40537bb4@suse.de/
---

# [PATCH blktests 00/10] nvme: make NVME_TARGET_CONTROL work with remote targets

来源：[https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-0-b31b40537bb4@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-0-b31b40537bb4@suse.de/)

```
Running the nvme fabrics tests against a remote target with
NVME_TARGET_CONTROL doesn't work in current upstream:

- contrib/nvme_target_control.py configures the target with nvmetcli
  through a REST API which only exists in an nvmetcli branch that was
  never merged, and its nvmetcli client crashes with configshell-fb 2.0.
  The target is never set up and the tests fail to connect.

- With a target set up by other means, the tests pass without testing
  anything: _nvme_ns_ready waits for the namespaces in the local nvmet
  configfs, which doesn't exist for a remote target. _nvme_connect_subsys
  returns an error after every connect, the tests skip their I/O and the
  disconnect, and the harness reports leftover controllers.

- The tests which use more than one port configure the ports in the
  local nvmet configfs, and add-ports is a stub. The authentication
  tests change the host keys there too.

Patch 1 makes common/nvme pass the controller key as --ctrlkey, the
option the script interface documents, instead of --ctrkey.

Patch 2 makes _nvme_ns_ready wait for the namespace the controller
reports when NVME_TARGET_CONTROL is set.

Patch 3 fixes the subsystem check of _nvmet_target_add_ports for the
local target.

Patch 4 skips nvme/038, nvme/051, nvme/058, nvme/060 and nvme/065 with a
remote target. They need the local nvmet target.

Patch 5 skips nvme/029 if its largest I/O exceeds the maximum transfer
size, e.g. with 4 KiB blocks and a 1 MiB MDTS.

Patch 6 replaces the script with contrib/nvme-target-control, a
standalone project in the style of nvme-cli's scripts/fuzz. It keeps the
command line blktests calls. The configuration only says how to reach
the target:

  [target]
  remote = "root@10.0.0.1"

The values blktests reads with config --show-* are worked out on the
host, each can be overridden. The target is a plugin: the built-in nvmet
target writes to configfs over ssh and backs the namespace with a loop
device it creates and removes. Other targets, e.g. a storage array with a
management API, and other channels than ssh can be added without
changing the project. The nvmet target also creates, removes and lists
ports, sets their ANA state and changes the DH-CHAP attributes of the
host.

Patch 7 makes the port helpers of common/nvme use the port commands with
a remote target.

Patch 8 makes the host key helpers of tests/nvme/rc use the set-host
command with a remote target.

Patch 9 lets the tests skip if the remote target lacks a feature they
need. config --show-features lists the optional commands the target
implements, e.g. a storage array with fixed ports and ANA states managed
by the array lists neither add-port nor set-ana.

Patch 10 adds such a target: a NetApp ONTAP storage virtual machine,
configured through the ONTAP REST API. It shows how the parts work
together with a target which can do less than nvmet: it implements
list-ports, show-port and set-host, and the tests which need more skip.

Tested with two QEMU VMs, the host running the nvme group against
nvmet (Debian 6.12 kernel) in the target VM over tcp:

- passed: 003-006, 008, 010, 012, 014, 018, 019, 021-023, 025-029, 031,
  040-045, 047, 057 (ANA failover over four ports), 061, 068, 069, 075,
  and 076, 079 and 080 of the isolcpus series
- failed: 070, the regression test for Identify CNS 07h; the 6.12
  target fails the command
- not run: tests for loop or fc only, tests which need the kernel
  target, local nvmet features (attr_qid_max, reservations), tlshd or
  ULP_DDP

nvme/029, nvme/038, nvme/051, nvme/058, nvme/060 and nvme/065 still pass
with the local target.

With the ontap target of patch 10, NVMe/TCP over the four LIFs of an
SVM and the host on SLES 15 SP7, 003-006, 008, 010, 012, 014, 018, 019,
021-023, 025-028, 040, 041, 044, 045 and 047 pass, and nvme/029, nvme/031,
nvme/057, nvme/062 and nvme/063 skip on the missing features. nvme/042
and nvme/043 fail only on SHA-384, which ONTAP doesn't support.

Unit tests, ruff, mypy and shellcheck are clean.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
Daniel Wagner (10):
      common/nvme: pass --ctrlkey to the target control script
      common/nvme: wait for the namespace of a remote target
      common/nvme: check the subsystem in _nvmet_target_add_ports
      nvme: skip the tests which need the kernel target with a remote target
      nvme/029: skip if the I/O exceeds the maximum transfer size
      contrib: make nvme-target-control a standalone project
      common/nvme: support the ports of a remote target
      nvme/rc: change the host keys on a remote target
      nvme: skip the tests which need a feature the remote target lacks
      contrib/nvme-target-control: add a NetApp ONTAP target

 Documentation/running-tests.md                     |  48 +++
 common/nvme                                        |  83 ++++-
 contrib/nvme-target-control/.gitignore             |   1 +
 contrib/nvme-target-control/README.md              | 177 ++++++++++
 contrib/nvme-target-control/nvme-target-control    |  19 +
 .../nvme_target_control/__init__.py                |   3 +
 .../nvme_target_control/channel.py                 | 113 ++++++
 .../nvme-target-control/nvme_target_control/cli.py | 205 +++++++++++
 .../nvme_target_control/plugin.py                  |  35 ++
 .../nvme_target_control/target.py                  | 222 ++++++++++++
 .../nvme_target_control/targets/__init__.py        |   3 +
 .../nvme_target_control/targets/nvmet.py           | 107 ++++++
 .../nvme_target_control/targets/nvmet.sh           | 246 +++++++++++++
 .../nvme_target_control/targets/ontap.py           | 392 +++++++++++++++++++++
 contrib/nvme-target-control/pyproject.toml         |  42 +++
 contrib/nvme-target-control/tests/test_ontap.py    | 340 ++++++++++++++++++
 .../tests/test_target_control.py                   | 380 ++++++++++++++++++++
 contrib/nvme_target_control.py                     | 204 -----------
 contrib/nvmet-subsys.jinja2                        |  71 ----
 tests/nvme/029                                     |  15 +-
 tests/nvme/031                                     |   1 +
 tests/nvme/038                                     |   1 +
 tests/nvme/042                                     |   1 +
 tests/nvme/043                                     |   1 +
 tests/nvme/044                                     |   1 +
 tests/nvme/045                                     |   1 +
 tests/nvme/051                                     |   1 +
 tests/nvme/057                                     |   1 +
 tests/nvme/058                                     |   1 +
 tests/nvme/060                                     |   1 +
 tests/nvme/062                                     |   1 +
 tests/nvme/063                                     |   1 +
 tests/nvme/065                                     |   1 +
 tests/nvme/rc                                      |  38 ++
 34 files changed, 2466 insertions(+), 291 deletions(-)
---
base-commit: a65cf6bdca19cf98e80ba379bffbf3a67f86fba3
change-id: 20261104-nvme-target-control-f0b239e68b29

Best regards,
--  
Daniel Wagner <dwagner@suse.de>
```
