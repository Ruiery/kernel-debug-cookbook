---
title: [PATCH 0/9] ublk: fix dispatch to canceled io commands
list: linux-block
message_id: 20260928-b4-ublk-cancel-stop-v1-0-4a4360232a46@toxicpanda.com
link: https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-0-4a4360232a46@toxicpanda.com/
---

# [PATCH 0/9] ublk: fix dispatch to canceled io commands

来源：[https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-0-4a4360232a46@toxicpanda.com/](https://lore.kernel.org/linux-block/20260928-b4-ublk-cancel-stop-v1-0-4a4360232a46@toxicpanda.com/)

```
ublk can dispatch a block request to an io command which is completed
already, and the kernel oopses in ublk_queue_rq() on a NULL io->cmd.
Before commit f7700a4415af ("ublk: fix use-after-free in
ublk_cancel_cmd()") it is a freed io_uring request instead. Commit
1133b93fc7f6 ("ublk: set canceling flag even when disk is not
allocated") fixed the io_uring exit route before the first start.
These are the routes next to it:

  1. STOP_DEV on a device which is ready but not started, then
     START_DEV. ublk_stop_dev() cancels the fetched commands after
     dropping ub->mutex, without marking the queues as canceling.
  2. A partial FETCH round whose task exits, once another task
     completes the round.
  3. During recovery, the task of a queue which is ready already
     exiting before the last queue is ready.

Patch 1 keeps a queue canceling at its ready transition when one of its
commands was canceled after the fetch, which closes route 2. Patch 2
clears ub->canceling as soon as a queue clears its own flag, so that a
later cancel marks and quiesces the queues again.

Patches 3 to 6 prepare for the control paths claiming commands while
the server still commits requests. Patches 3 and 4 put the switch of
io->cmd in the commit paths and the reads of a cancel under io->lock.
Patch 5 has the issue path complete a command which a cancel took
before io_uring put it on its list of cancelable commands, and patch 6
splits the claim of a command from its completion.

Patch 7 makes ublk_uring_cmd_cancel_fn() mark the queues and the
command in one cancel_mutex section, so that the ready transition of
route 3 cannot come in between. Patch 8 marks the queues and claims the
commands in ublk_stop_dev() before ub->mutex is dropped and completes
them afterwards, for route 1. Setting ->canceling there is not enough
on its own, the last FETCH of the round can still come in before any
command is marked and clear it again.

Patch 9 changes behaviour and is the one I would like feedback on. With
patches 1 to 8, as with 1133b93fc7f6 alone, START_DEV brings up a disk
on which every request fails. With UBLK_F_USER_RECOVERY and without
UBLK_F_USER_RECOVERY_FAIL_IO the requests are requeued and never
kicked, which leaves the partition scan hanging under
disk->open_mutex. Patch 9 makes START_DEV and END_USER_RECOVERY return
-ENODEV instead. The server cannot fetch those commands again anyway. If
that is not wanted, patches 1 to 8 stand on their own.

UBLK_CMD_QUIESCE_DEV has problems of its own, which this series does
not fix. Its one cancel pass skips a command whose request is with the
server or still started at that moment, a COMMIT_AND_FETCH then queues
a new command on the canceling queue, nothing completes it, and the
server never exits, so the device stays LIVE. The path is the same on
for-next, but with this series the hang shows up about twice as often
in my testing, roughly 4% of quiesces under fio against 2%, possibly
because the claim now takes io->lock for each command. Sent again after
a new server fetched its commands, QUIESCE_DEV can also leave some of
them canceled. I am working on those separately, tying the cancel to
the server it is meant for.

ublk_batch_attach() publishing a fetch command before io_uring marks it
cancelable is not touched either, it is the same on for-next and I will
send a separate fix for it.

Tested under QEMU with KASAN and lockdep, and in a KCSAN build: a small
io_uring reproducer for each route, with restart after a server exit
and a full USER_RECOVERY cycle as controls, the ublk selftests, and a
script racing ADD_DEV against STOP_DEV and DEL_DEV and running both
under fio, on each commit path including UBLK_F_BATCH_IO. On for-next
the reproducers oops. With the series they end in -ENODEV or pass.

Thanks,

Josef

---
Josef Bacik (9):
      ublk: keep queue canceling over canceled commands
      ublk: clear ub->canceling with the queue's own flag
      ublk: publish io->cmd under io->lock in the commit paths
      ublk: read the io under io->lock in ublk_cancel_cmd()
      ublk: complete a command canceled before it was marked from its issuer
      ublk: split ublk_claim_cmd() out of ublk_cancel_cmd()
      ublk: mark queues and command in one cancel_mutex hold
      ublk: claim commands under ub->mutex in ublk_stop_dev()
      ublk: refuse to go live over canceled io commands

 Documentation/block/ublk.rst |  15 +-
 drivers/block/ublk_drv.c     | 394 ++++++++++++++++++++++++++++++++++++-------
 2 files changed, 344 insertions(+), 65 deletions(-)
---
base-commit: d70609a2f68c9c89231fbce6600c90feca65e262
change-id: 20260924-b4-ublk-cancel-stop-d640af9fa9af
```
