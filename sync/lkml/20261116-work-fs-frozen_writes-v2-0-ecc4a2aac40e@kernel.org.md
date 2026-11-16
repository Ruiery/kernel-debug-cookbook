---
title: [PATCH v2 00/17] fs: take freeze protection for writes to backing files
list: linux-block
message_id: 20261116-work-fs-frozen_writes-v2-0-ecc4a2aac40e@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-0-ecc4a2aac40e@kernel.org/
---

# [PATCH v2 00/17] fs: take freeze protection for writes to backing files

来源：[https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-0-ecc4a2aac40e@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-0-ecc4a2aac40e@kernel.org/)

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
[2]: https://lore.kernel.org/r/20261116064654.GA2964@lst.de

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
Changes in v2:
- Add kiocb_write_iter() and kiocb_end_write_iter() and use them for
  zloop, the nvme target and fileio as per Christoph's suggestion.
- Add a file_write guard and use it for loop discard and write zeroes
  and fileio unmap.
- Convert loop, vfs_iocb_iter_write() and fs/backing-file.c to the new
  helpers.
- Only complete the fileio target command when the last reference to
  the aio command is dropped.
- Link to v1: https://patch.msgid.link/20261114-work-fs-frozen_writes-v1-0-f5ae61c898b1@kernel.org

---
Christian Brauner (17):
      fs: add kiocb_start_write_trylock()
      fs: add kiocb_write_iter() and kiocb_end_write_iter()
      fs: add file_write guard
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
      loop: use kiocb_write_iter()
      fs: use kiocb_write_iter() in vfs_iocb_iter_write()
      backing-file: use kiocb_end_write_iter()

 drivers/block/loop.c              | 13 ++++---
 drivers/block/zloop.c             | 12 +++++--
 drivers/nvme/target/io-cmd-file.c | 20 +++++++----
 drivers/target/target_core_file.c | 31 +++++++++++-----
 fs/backing-file.c                 |  8 ++---
 fs/bpf_fs_kfuncs.c                |  8 +++++
 fs/coredump.c                     |  6 ++--
 fs/nfsd/nfs4state.c               | 10 +++++-
 fs/overlayfs/util.c               |  8 +++--
 fs/read_write.c                   |  7 ++--
 include/linux/fs.h                | 75 +++++++++++++++++++++++++++++++++++++++
 io_uring/rw.c                     |  9 +----
 12 files changed, 158 insertions(+), 49 deletions(-)
---
base-commit: 6628e7d4c6b25c8d18f1345e3a20d21829aae7e4
change-id: 20261113-work-fs-frozen_writes-042ca762bfb8
```
