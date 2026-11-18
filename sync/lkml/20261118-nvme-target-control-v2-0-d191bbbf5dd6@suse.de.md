---
title: [PATCH blktests v2 0/9] nvme: make NVME_TARGET_CONTROL work with remote targets
list: linux-block
message_id: 20261118-nvme-target-control-v2-0-d191bbbf5dd6@suse.de
link: https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-0-d191bbbf5dd6@suse.de/
---

# [PATCH blktests v2 0/9] nvme: make NVME_TARGET_CONTROL work with remote targets

来源：[https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-0-d191bbbf5dd6@suse.de/](https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-0-d191bbbf5dd6@suse.de/)

```
Hi all,

this series makes running the nvme tests against a remote target with
NVME_TARGET_CONTROL actually work. The first six patches of v1 have been
applied, this is the rest. It applies on top of the series that makes
tests skip when a program they need is missing.

The first two patches are fixes: nvme/047 looks up the namespace again
after reconnecting, and the nvmet target picks free service IDs for its
ports. The third is a cleanup, nvme/042 and nvme/043 iterate over the
DH-HMAC-CHAP hashes by name.

The remaining patches let tests skip instead of failing when the remote
target lacks a feature they need, including the DH-HMAC-CHAP hashes and
DH groups the target doesn't support, add port and host key support for
remote targets, and add a NetApp ONTAP target as an example of a target
that can do less than nvmet.

Tested against nvmet in a second VM, which also exported other
subsystems on its own ports, and against a NetApp ONTAP array. All tests
that can run against a remote target pass, except nvme/077 against
nvmet, which checks attr_qid_max in the local nvmet configfs. Against
the array, nvme/061 and nvme/070 fail because it refuses the reconnect
after a subsystem is deleted and doesn't support Identify CNS 07h, and
nvme/068 because the host runs a 6.4 kernel. The tests that need the
kernel target still pass with the local target.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
Changes in v2:
- Drop the six patches that were applied.
- Fix nvme/047 to look up the namespace again after reconnecting.
- Pick free service IDs for new nvmet ports.
- Pass the TLS option in the argument array instead of an unquoted
  command substitution; quoting it would pass an empty argument without
  TLS. (Shin'ichiro)
- Check the features with =~, with an SC2076 exception for the literal
  match. (Shin'ichiro)
- List the DH-HMAC-CHAP algorithms a target supports, iterate over them
  by name in nvme/042 and nvme/043 and skip the ones the target lacks.
- Put the fixes first, then the cleanup, then the features.
- Depend on the series that makes tests skip when a program is missing.
- Link to v1: https://patch.msgid.link/20261104-nvme-target-control-v1-0-b31b40537bb4@suse.de

---
Daniel Wagner (9):
      nvme/047: look up the namespace again after reconnecting
      contrib/nvme-target-control: pick a free service ID for new nvmet ports
      nvme/042, nvme/043: iterate over the DH-HMAC-CHAP hashes by name
      nvme: skip tests that need a feature the remote target lacks
      contrib/nvme-target-control: list the DH-HMAC-CHAP algorithms
      nvme: skip the DH-HMAC-CHAP algorithms the target doesn't support
      common/nvme: support the ports of a remote target
      nvme/rc: change the host keys on a remote target
      contrib/nvme-target-control: add a NetApp ONTAP target

 Documentation/running-tests.md                     |  49 ++-
 common/nvme                                        |  88 ++++-
 contrib/nvme-target-control/README.md              |  72 +++-
 .../nvme_target_control/target.py                  |  19 +
 .../nvme_target_control/targets/nvmet.py           |  12 +-
 .../nvme_target_control/targets/nvmet.sh           |   7 +-
 .../nvme_target_control/targets/ontap.py           | 397 +++++++++++++++++++++
 contrib/nvme-target-control/tests/test_ontap.py    | 357 ++++++++++++++++++
 .../tests/test_target_control.py                   |   4 +-
 tests/nvme/031                                     |   1 +
 tests/nvme/041                                     |   1 +
 tests/nvme/042                                     |  12 +-
 tests/nvme/042.out                                 |   8 +-
 tests/nvme/043                                     |   9 +-
 tests/nvme/043.out                                 |   6 +-
 tests/nvme/044                                     |   1 +
 tests/nvme/045                                     |   1 +
 tests/nvme/047                                     |   2 +
 tests/nvme/057                                     |   1 +
 tests/nvme/062                                     |   1 +
 tests/nvme/063                                     |   5 +-
 tests/nvme/rc                                      |  58 +++
 22 files changed, 1069 insertions(+), 42 deletions(-)
---
base-commit: 79c32fb31b7bca6a4383b749030128683cf6b6b4
change-id: 20261104-nvme-target-control-f0b239e68b29
prerequisite-change-id: 20261117-skip-missing-deps-30b4084698c4:v1
prerequisite-patch-id: 9478a4106d922c8432a4d297dcb18ed68a9c8d61
prerequisite-patch-id: 635fcb82ae72c78b84ad593a58d82315a166724d
prerequisite-patch-id: 528ad89bda84f0b0d9cbc0d38b6e1384332f86cd
prerequisite-patch-id: 2758a16b44a326eea5113ff4967e6093ad42e71c
prerequisite-patch-id: 9acbf0ff52b0b46035e4635035662cd9d9309f77

Best regards,
--  
Daniel Wagner <dwagner@suse.de>
```
