---
title: [PATCH 0/4] nbd: revalidate startup state after queue updates
list: linux-block
message_id: cover.1792399225.git.liuyun01@kylinos.cn
link: https://lore.kernel.org/linux-block/cover.1792399225.git.liuyun01@kylinos.cn/
---

# [PATCH 0/4] nbd: revalidate startup state after queue updates

来源：[https://lore.kernel.org/linux-block/cover.1792399225.git.liuyun01@kylinos.cn/](https://lore.kernel.org/linux-block/cover.1792399225.git.liuyun01@kylinos.cn/)

```
From: Jackie Liu <liuyun01@kylinos.cn>

Hi,

Commit 8b428f42f3ed ("nbd: fix lockdep deadlock warning") drops
config_lock around blk_mq_update_nr_hw_queues(). The initial checks for a
running device and NBD_FLAG_CAN_MULTI_CONN can become stale while the
lock is dropped.

Two NBD_DO_IT callers can both pass the PID check. After the first caller
starts the device, the loser overwrites nbd->pid before failing to create
the existing sysfs pid attribute. Concurrent NBD_SET_SOCK or NBD_SET_FLAGS
can also leave multiple connections without NBD_FLAG_CAN_MULTI_CONN,
which the queue-count retry does not validate.

Recheck both conditions after reacquiring config_lock. Reject an already
started device with EBUSY, and reject unsupported multiple connections
with EINVAL before retrying the queue update or starting receive workers.

Each fix is followed by its regression test. The tests prime the hardware
queue count before each attempt and use socket pairs, so no external NBD
server is needed. They require CAP_SYS_ADMIN, at least two online CPUs
and unused NBD devices. To build and run them:

  modprobe nbd nbds_max=4 max_part=0
  make -C tools/testing/selftests TARGETS=nbd
  make -C tools/testing/selftests TARGETS=nbd run_tests

For longer runs with a reproducible random seed:

  tools/testing/selftests/nbd/nbd_pid_race --rounds 100 --seed 123
  tools/testing/selftests/nbd/nbd_multi_conn --rounds 100 --seed 123

These tests use scheduling stress rather than kernel instrumentation. A
passing run means that no regression was observed during that run; it
does not guarantee that every interleaving was exercised. The flags test
excludes changes observed after PID publication.

Testing on the v7.3 base below:

  - ARM64 kernel Image and modules built with GCC.
  - Both selftests built with GCC and Clang; kselftest installation passed.
  - In QEMU TCG with two CPUs, all three cases passed 100 rounds with seed
    123, with no reported regressions or test errors.
  - Both tests passed through the standard kselftest runner.
  - Removing both fixes made all three cases detect their regression.
    With only the PID fix, the PID case passed and both multi-connection
    cases still detected their regression.
  - The fixed-kernel run had no WARN/BUG/Oops reports and remained
    untainted. Missing-device skips emitted one TAP plan per test.
  - Fault injection checked PID-read error propagation, EINTR retry and
    attribute disappearance handling in the test helper.
  - In-tree checkpatch --strict reported no errors or checks. The generic
    new-file MAINTAINERS warning on patch 4 was reviewed: patch 2 already
    registers the entire NBD selftest directory.

Both driver fixes carry the upstream Fixes tag and a stable Cc for
v6.17 and later. The selftest patches do not request stable backports.

Thanks,
Jackie

Jackie Liu (4):
  nbd: reject concurrent device starts
  selftests: nbd: test concurrent device starts
  nbd: recheck multi-connection support on startup
  selftests: nbd: test multi-connection startup races

 MAINTAINERS                                  |   1 +
 drivers/block/nbd.c                          |   7 +
 tools/testing/selftests/Makefile             |   1 +
 tools/testing/selftests/nbd/.gitignore       |   2 +
 tools/testing/selftests/nbd/Makefile         |   8 +
 tools/testing/selftests/nbd/config           |   7 +
 tools/testing/selftests/nbd/nbd_common.c     | 465 +++++++++++++++++++
 tools/testing/selftests/nbd/nbd_common.h     |  53 +++
 tools/testing/selftests/nbd/nbd_multi_conn.c | 147 ++++++
 tools/testing/selftests/nbd/nbd_pid_race.c   |  86 ++++
 10 files changed, 777 insertions(+)
 create mode 100644 tools/testing/selftests/nbd/.gitignore
 create mode 100644 tools/testing/selftests/nbd/Makefile
 create mode 100644 tools/testing/selftests/nbd/config
 create mode 100644 tools/testing/selftests/nbd/nbd_common.c
 create mode 100644 tools/testing/selftests/nbd/nbd_common.h
 create mode 100644 tools/testing/selftests/nbd/nbd_multi_conn.c
 create mode 100644 tools/testing/selftests/nbd/nbd_pid_race.c


base-commit: c03c1a14507dfaf8b856c2608f9ac216021fc222
```
