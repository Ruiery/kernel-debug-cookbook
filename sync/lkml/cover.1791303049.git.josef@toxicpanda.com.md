---
title: [PATCH 0/4] ublk: fix UBLK_CMD_QUIESCE_DEV leaving commands behind
list: linux-block
message_id: cover.1791303049.git.josef@toxicpanda.com
link: https://lore.kernel.org/linux-block/cover.1791303049.git.josef@toxicpanda.com/
---

# [PATCH 0/4] ublk: fix UBLK_CMD_QUIESCE_DEV leaving commands behind

来源：[https://lore.kernel.org/linux-block/cover.1791303049.git.josef@toxicpanda.com/](https://lore.kernel.org/linux-block/cover.1791303049.git.josef@toxicpanda.com/)

```
UBLK_CMD_QUIESCE_DEV has two problems the fixes for STOP_DEV and the
FETCH rounds don't touch.

Sent to a device that is not LIVE, it still cancels after it returns 0.
A device whose server died is QUIESCED, and a new server may be
fetching its commands for recovery at that point, so the cancel takes
them without marking anything and END_USER_RECOVERY brings the device
up over NULL io->cmd. Patch 1 makes it cancel nothing then.

On a LIVE device it cancels in one pass, which skips every command
whose request is with the server. The server's COMMIT_AND_FETCH arms
the command again right after, nothing ever completes it, and the
server, which waits for all its commands, never exits. The device stays
LIVE. Same for the active fetch command of a UBLK_F_BATCH_IO queue. The
kublk selftest server hangs this way within a few quiesce and recover
cycles under fio, on every kind of queue.

Patch 2 drops ublk_wait_for_idle_io(), which never waited and would
hold ub->mutex against a stalled server if it did. Patch 3 has
COMMIT_AND_FETCH and NEED_GET_DATA give their new command back on a
canceling queue instead of publishing it, deciding inside an RCU read
section, so the I/O path gains no lock or barrier. Patch 4 has
QUIESCE_DEV wait for that with synchronize_rcu() and then keep taking
the armed commands until the server owes none, bounded by its timeout,
and stop once the server's FETCH round is over, so the next server's
commands are left alone.

QUIESCE_DEV now returns -EBUSY or -EINTR when its timeout or a signal
ends that wait with commands still owed, where it returned 0 after one
pass before.

This applies on top of Ming's "[PATCH 0/8] ublk: don't dispatch to
canceled io commands" [1] and my "ublk: refuse to go live after an io
command was canceled" [2].

Tested under QEMU with KASAN and lockdep. Without the series, 20
quiesce and recover cycles under fio hang in every round on getdata,
zero copy and user copy devices and in some on batch ones, and the
quiesce-twice reproducer oopses. With it, 3 rounds of 20 cycles on each
kind of device pass, the reproducer is fine, and the ublk selftests
including generic_18 pass.

[1] https://lore.kernel.org/linux-block/20261001125422.1364260-1-tom.leiming@gmail.com/
[2] https://lore.kernel.org/linux-block/9b876f2c061abc401ec4b9b3c2529eda.josef@toxicpanda.com/

Thanks,
Josef

Josef Bacik (4):
  ublk: don't cancel commands in QUIESCE_DEV on a device that isn't live
  ublk: drop QUIESCE_DEV's wait for an idle command
  ublk: give the command back from COMMIT_AND_FETCH on a canceling queue
  ublk: keep canceling in QUIESCE_DEV until the server's commands are
    taken

 drivers/block/ublk_drv.c | 286 +++++++++++++++++++++++++++++++--------
 1 file changed, 230 insertions(+), 56 deletions(-)

-- 
2.55.0
```
