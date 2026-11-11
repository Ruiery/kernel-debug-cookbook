---
title: [PATCH 0/4] ublk: report recovery test failures and fix the exposed defects
list: linux-block
message_id: 202611112257529855AMDZLzg8ZmFDQ3fBstbi@zte.com.cn
link: https://lore.kernel.org/linux-block/202611112257529855AMDZLzg8ZmFDQ3fBstbi@zte.com.cn/
---

# [PATCH 0/4] ublk: report recovery test failures and fix the exposed defects

来源：[https://lore.kernel.org/linux-block/202611112257529855AMDZLzg8ZmFDQ3fBstbi@zte.com.cn/](https://lore.kernel.org/linux-block/202611112257529855AMDZLzg8ZmFDQ3fBstbi@zte.com.cn/)

```
The four patches make the ublk recovery tests report failures from their
workers, and then fix the two defects that the stricter tests exposed.
They are one series because the later work came out of the earlier
patches: patch 2 applies on top of patch 1, and patches 3 and 4 are the
two independent fixes that patch 2's testing uncovered.

Patch 1 waits for the recorded recovery worker PIDs and reports their
status from the parent, so a failed worker no longer ends in PASS.  It is
a v2 of the patch posted separately on 11-09; the only change is the
simplified wait loop Ming Lei asked for, and his Reviewed-by is kept.

Patch 2 generalizes that collector for the stress scripts, which used a
bare wait in nine of them and could print PASS after a worker failed.

Patch 3 cancels a command that is committed after the quiesce
cancellation scan has passed its slot; without it the server waits for a
completion that never comes and the device stays LIVE.  This is the
kernel fix and carries Fixes: and Cc: stable.

Patch 4 clears the uring_cmd flag word when a selftest batch SQE is
reused, so a recycled slot no longer carries the multishot flag of the
previous batch fetch and is rejected with -EINVAL.

Tested on next-20261105 with CONFIG_BLK_DEV_UBLK=y in a local QEMU/KVM
VM (4 vCPUs, 4 GiB), with real ublk devices, kublk and fio.  Patch 1
keeps its 71-scenario stub matrix.  For patch 2, all nine stress scripts
passed before and after; with an injected ADD_DEV failure all nine
previously reported PASS with exit status 0, and now report FAIL with
255.  For patch 3, a test-only server hook held one COMMIT across a
successful quiesce: the original kernel stayed LIVE until a second
quiesce, the patched kernel reached QUIESCED directly, two runs per
version.  For patch 4, the original kublk rejected the reused batch SQE
with -EINVAL and its daemon exited, the patched kublk kept the device
LIVE.  With both fixes applied the four recovery scripts passed twice
per version.

Shao Mingyin (4):
  selftests: ublk: propagate recovery worker failures
  selftests: ublk: propagate stress worker failures
  ublk: cancel commits arriving after the quiesce scan
  selftests: ublk: clear reused batch SQE command flags

 drivers/block/ublk_drv.c                        | 40 ++++++++++++++++---------
 tools/testing/selftests/ublk/batch.c            |  1 +
 tools/testing/selftests/ublk/test_common.sh     | 30 ++++++++++++++-----
 tools/testing/selftests/ublk/test_recover_01.sh | 20 ++++++++++---
 tools/testing/selftests/ublk/test_recover_02.sh | 20 ++++++++++---
 tools/testing/selftests/ublk/test_recover_03.sh | 20 ++++++++++---
 tools/testing/selftests/ublk/test_recover_04.sh | 14 +++++++--
 tools/testing/selftests/ublk/test_stress_01.sh  |  9 ++++--
 tools/testing/selftests/ublk/test_stress_02.sh  |  9 ++++--
 tools/testing/selftests/ublk/test_stress_03.sh  | 23 +++++++++++---
 tools/testing/selftests/ublk/test_stress_04.sh  | 23 +++++++++++---
 tools/testing/selftests/ublk/test_stress_05.sh  | 28 ++++++++++++-----
 tools/testing/selftests/ublk/test_stress_06.sh  | 15 ++++++++--
 tools/testing/selftests/ublk/test_stress_07.sh  | 15 ++++++++--
 tools/testing/selftests/ublk/test_stress_08.sh  | 10 +++++--
 tools/testing/selftests/ublk/test_stress_09.sh  | 10 +++++--
 16 files changed, 221 insertions(+), 66 deletions(-)

---
base-commit: ddfe51b0a0f5dc9e415cc2c8ad8db17532dd426b
```
