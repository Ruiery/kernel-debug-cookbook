---
title: [PATCH 00/12] fs: take freeze protection for writes to backing files
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-0-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-0-f5ae61c898b1@kernel.org/
---

# [PATCH 00/12] fs: take freeze protection for writes to backing files

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-0-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-0-f5ae61c898b1@kernel.org/)

```
While testing the pseudo filesystem series I noticed that zloop, the
nvme target's file backend and the fileio backend of the scsi target
with fd_async_io=1 call ->write_iter() of their backing files without
taking freeze protection. So their writes go straight through to a
frozen filesystem. ext4 complains loudly:

    WARNING: fs/ext4/ext4_jbd2.c:90 at ext4_journal_check_start+0x1f6/0x2d0

Loop doesn't get it right for discard and write zeroes. Those end up
calling ->fallocate() of the backing file directly. The fileio backend
does the same for UNMAP. And zloop records its write pointers on flush
with vfs_setxattr() which leaves freeze protection to the caller. So all
of them modify a frozen filesystem just the same. Fix them too.

Looking for more of the same turned up a few simple ones. coredump
truncates the core file, overlayfs stores its uuid xattr on mount, nfsd
truncates on OPEN and the BPF xattr kfuncs modify xattrs, all without
freeze protection. Fix those as well. The ones that need more work in
their subsystems I have reported separately.

The fileio backend also frees its aio command in the completion handler
while the filesystem may still be using the kiocb. KASAN catches ext4
doing that for direct reads on v7.4-rc1. ext4 gets its own fix (cf. [1])
but fileio should hold a reference across the submission like loop,
zloop and fs/backing-file.c do.

[1]: https://lore.kernel.org/r/20261113-work-ext4-dio_read_kiocb-v1-1-172a88be803c@kernel.org

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
Christian Brauner (12):
      fs: add kiocb_start_write_trylock()
      zloop: take freeze protection for writes
      nvmet: take freeze protection for writes to files
      target: fileio: don't free the aio command under the filesystem
      target: fileio: take freeze protection for aio writes
      loop: take freeze protection for discard and write zeroes
      zloop: take freeze protection when recording write pointers
      target: fileio: take freeze protection for unmap
      coredump: take freeze protection for the truncate
      ovl: take freeze protection when storing the uuid
      bpf: fs/xattr: take freeze protection in the xattr kfuncs
      nfsd: take freeze protection for the truncate on open

 drivers/block/loop.c              |  2 ++
 drivers/block/zloop.c             | 31 ++++++++++++++++++++-------
 drivers/nvme/target/io-cmd-file.c | 37 +++++++++++++++++++++++++-------
 drivers/target/target_core_file.c | 44 ++++++++++++++++++++++++++++++++-------
 fs/bpf_fs_kfuncs.c                |  8 +++++++
 fs/coredump.c                     |  6 ++++--
 fs/nfsd/nfs4state.c               | 10 ++++++++-
 fs/overlayfs/util.c               |  8 +++++--
 include/linux/fs.h                | 22 ++++++++++++++++++++
 io_uring/rw.c                     |  9 +-------
 10 files changed, 142 insertions(+), 35 deletions(-)
---
base-commit: 6628e7d4c6b25c8d18f1345e3a20d21829aae7e4
change-id: 20261113-work-fs-frozen_writes-042ca762bfb8
```
