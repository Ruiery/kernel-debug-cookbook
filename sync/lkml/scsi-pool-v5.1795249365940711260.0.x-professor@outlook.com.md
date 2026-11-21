---
title: [PATCH v5 0/2] scsi: bsg: Release io_uring requests from end-I/O
list: linux-block
message_id: scsi-pool-v5.1795249365940711260.0.x-professor@outlook.com
link: https://lore.kernel.org/linux-block/scsi-pool-v5.1795249365940711260.0.x-professor@outlook.com/
---

# [PATCH v5 0/2] scsi: bsg: Release io_uring requests from end-I/O

来源：[https://lore.kernel.org/linux-block/scsi-pool-v5.1795249365940711260.0.x-professor@outlook.com/](https://lore.kernel.org/linux-block/scsi-pool-v5.1795249365940711260.0.x-professor@outlook.com/)

```
The BSG io_uring path retains completed requests until task work copies=0A=
sense data and unmaps the data buffer. With DEFER_TASKRUN, the submitter=0A=
may fault on memory backed by the same queue before running that work.=0A=
If completed requests hold all the tags, neither the fault's I/O nor=0A=
the task work can progress.=0A=
=0A=
These two patches save completion state in end-I/O and release the=0A=
request there. Task work uses the saved state, unmaps the independent=0A=
BIO chain and completes the command. They apply on top of the four=0A=
synchronous request-lifetime patches posted as v5:=0A=
=0A=
https://lore.kernel.org/r/scsi-sync-v5.1795249365940711260.0.x-professor@ou=
tlook.com=0A=
=0A=
Patch 1 provides a BSG-owned pool of 64 sense buffers per device,=0A=
allocated when its queue is registered and freed with the BSG device.=0A=
The bitmap and 96-byte buffers use one allocation. Opening the device=0A=
allocates no pool; transport BSG and CONFIG_IO_URING=3Dn allocate none.=0A=
Patch 2 takes a slot before mapping user data and returns it in end-I/O=0A=
when there is no sense data to deliver, or from task work otherwise.=0A=
=0A=
When the pool is empty, the command fails with -EAGAIN instead of waiting.=
=0A=
io_uring may retry a nonblocking attempt in io-wq. An io-wq attempt=0A=
that finds the pool empty completes with -EAGAIN, requiring userspace=0A=
to resubmit. Slots are shared across openers: one opener can retain=0A=
all 64 with unreaped CHECK CONDITION completions, causing other openers=0A=
to receive -EAGAIN. BSG nodes are normally accessible only to privileged=0A=
users, and the series accepts this shared limit to avoid allocating a=0A=
pool on every open. SG_SET_COMMAND_Q does not resize the pool.=0A=
=0A=
Changes in v5, following Yang Xiuwei's review and example patches:=0A=
- Replace the per-file pool with a per-device pool and a bitmap.=0A=
- Return buffers with no sense data in end-I/O; use irqsave locking.=0A=
- Embed the bitmap and buffers in one allocation, remove the redundant=0A=
  buffer-size field, and trim comments.=0A=
- Return quietly on invalid get/put arguments while retaining range=0A=
  checks, double-put and outstanding-buffer diagnostics.=0A=
- Credit Yang's pool implementation with Co-developed-by and retain his=0A=
  Signed-off-by from the posted patch.=0A=
- Drop the unrelated multishot rejection and timeout snapshot.=0A=
- Rebase onto synchronous v5.=0A=
=0A=
Tested in QEMU on 9f9e0b1e5399 plus synchronous v5, with KASAN and=0A=
lockdep. The 960 regression checks and release-order tracing passed:=0A=
completed io_uring requests no longer remained allocated before deferred=0A=
task work ran. Cancellation, linked commands, 256-command pool exhaustion,=
=0A=
64-slot recovery and concurrent use through two opens passed. A rejected=0A=
bounced READ through a second opener left its user buffer unchanged.=0A=
128 successful commands returned all slots before running task work.=0A=
No KASAN or lockdep reports were observed. These tests check ordering=0A=
and behavior; they do not reproduce a same-device page-fault deadlock.=0A=
=0A=
Dropping the multishot rejection restores the base kernel's flag=0A=
handling; the tested multishot-flagged commands completed once on both=0A=
kernels with normal, DEFER_TASKRUN and IOSQE_ASYNC submissions.=0A=
=0A=
Each patch passed affected-object W=3D1 builds. Final configuration checks=
=0A=
also covered i386, CONFIG_IO_URING=3Dn and PREEMPT_RT with SCSI=3Dm. Kernel=
=0A=
selftests were not run.=0A=
=0A=
Successful INQUIRY batches were measured on non-debug kernels, with=0A=
three interleaved boots per variant and five rounds per boot. Both v4=0A=
and v5 used the same synchronous-v5 base. The table shows batch time=0A=
divided by command count, in microseconds, with a 96-byte response=0A=
buffer supplied. Retry time is included; base has no io_uring fix.=0A=
These timings were measured before the multishot rejection and timeout=0A=
snapshot were dropped, and were not rerun; pool allocation, locking and=0A=
early return are unchanged.=0A=
=0A=
  mode    depth   base     v4     v5=0A=
  normal     16  1.587  1.593  1.646=0A=
  normal     64  1.158  1.165  1.195=0A=
  normal     96  1.066  1.231  1.165=0A=
  defer      16  1.582  1.589  1.643=0A=
  defer      64  1.155  1.166  1.198=0A=
  defer      96  1.065  1.228  1.161=0A=
=0A=
Compared with v4, v5 increased time per command by 2.6-3.4% at depths=0A=
16 and 64, mainly due to irqsave locking in the control measurements.=0A=
At depth 96, early buffer return reduced -EAGAIN completions from 32 per=0A=
batch to about 9 and reduced time per command by 5.4-5.5%. These QEMU=0A=
measurements do not establish performance on physical SCSI hardware.=0A=
=0A=
Both patches retain Cc: stable. Patch 1 is a prerequisite for patch 2,=0A=
which fixes 7b6d3255e7f8 ("scsi: bsg: add io_uring passthrough handler").=
=0A=
A backport needs both patches, in order, on top of synchronous patch 4/4=0A=
("scsi: bsg: Release synchronous request before user copyback"), which=0A=
changes the same file. Both pool patches exceed the stable rules'=0A=
100-line limit, including context; if that rules them out, I am fine=0A=
with dropping the tags.=0A=
=0A=
v4: https://lore.kernel.org/r/cover.1795016239.git.x-professor@outlook.com=
=0A=
Yang's pool patch:=0A=
https://lore.kernel.org/r/20261119031751.3471968-2-yangxiuwei@kylinos.cn=0A=
Yang's follow-up:=0A=
https://lore.kernel.org/r/20261120021604.2648220-1-yangxiuwei@kylinos.cn=0A=
=0A=
Yingjie Wang (2):=0A=
  block: bsg: add a per-device pool of uring_cmd completion buffers=0A=
  scsi: bsg: Release io_uring requests from end-I/O=0A=
=0A=
 block/bsg.c             | 109 ++++++++++++++++++++++++++++++++++++++++=0A=
 drivers/scsi/scsi_bsg.c | 109 +++++++++++++++++++++++++++++-----------=0A=
 include/linux/bsg.h     |   3 ++=0A=
 3 files changed, 192 insertions(+), 29 deletions(-)=0A=
=0A=
=0A=
base-commit: 9f9e0b1e5399045982788a954d3461de894e40c7=0A=
prerequisite-patch-id: ef4b390580d84500ee98fcddff0a34e5cd95e40c=0A=
prerequisite-patch-id: 1b98fea4540409102179bfccd2905a686c7f1b5a=0A=
prerequisite-patch-id: ce66c68fb99ef813e5506ba7f3de512c1fd0c832=0A=
prerequisite-patch-id: 73942e82ea57898fb0af8ee1db909b0dfa8b2b77=0A=
-- =0A=
2.43.0=0A=
=0A=
```
