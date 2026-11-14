---
title: [PATCH RFC v2 00/42] fs: don't use pseudo filesystem files as storage
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-0-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-0-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 00/42] fs: don't use pseudo filesystem files as storage

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-0-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-0-98639a2286fb@kernel.org/)

```
Loop happily takes any regular file with ->read_iter() as a backing
file and any file that also has ->write_iter() as a writable one. A few
examples:

* /proc/kcore attaches read-only as a loop device the size of the
  kernel's virtual address space (64 PiB with 5-level paging)
* sysfs attributes attach read-write as 4096 byte loop devices
* using /sys/kernel/mm/transparent_hugepage/enabled for the loop device
  and writing a block to the loop device changes the THP setting

It's not just silly. It's abusable (is that a word?). Loop calls
->read_iter() and ->write_iter() of the backing file directly from its
kworker which runs with kernel credentials.

But pseudo files enforce part of their access rules at read and write
against the caller. So dozens of sysfs ->show() and ->store() methods
call capable().

But setting up a loop device requires no capabilities. It only requires
access to the device nodes. So whoever has a loop device skips all of
the capable() checks.

A couple of fun examples:

On v7.4-rc1 uid 0 without any capabilities can't kill a process of uid
1000 and can't poison its memory either:

    $ grep CapEff /proc/self/status
    CapEff: 0000000000000000
    $ kill -9 327
    bash: kill: (327) - Operation not permitted
    $ echo 0x220689000 > /sys/devices/system/memory/hard_offline_page
    bash: echo: write error: Operation not permitted

But put hard_offline_page behind a loop device, write a block
containing 0x220689000 to the loop device and the loop worker happily
does it:

    Memory failure: 0x220689: recovery action for dirty LRU page: Recovered
    MCE: Killing victim:327 due to hardware memory corruption fault at 7f468e972000

That hard_offline_page is a write-only file doesn't stop loop from
using it as a writable backing file either.

Other fun examples:

(1) soft-block radios via /sys/class/rfkill/rfkill*/soft
    (CAP_NET_ADMIN)

(2) change the reboot mode via /sys/kernel/reboot/mode (CAP_SYS_BOOT)

(3) reconfigure md arrays via /sys/block/md*/md/. md_attr_store()
    requires CAP_SYS_ADMIN for every md attribute.

(4) reconfigure scsi disks via /sys/class/scsi_disk/*/allow_restart and
    friends (CAP_SYS_ADMIN)

(5) read dmi-sysfs attributes (CAP_SYS_ADMIN)

And an unprivileged container that was handed a loop device can change
gro_flush_timeout of its own network devices. That usually requires
CAP_NET_ADMIN in the initial user namespace (via sysfs and via netlink).

I've reproduced that all on v7.4-rc1.

Aaaand zloop, the nvme target's file backend, the scsi target's fileio
backend, fuse passthrough and the usb mass storage gadget have the same
problem. erofs takes pseudo files as images for file-backed mounts as
well. It reads them with the mounter's credentials though so that's just
silly and not abusable.

Fwiw, device mapper doesn't need anything. It only takes block devices.
md's deprecated bitmap file is fine as well. It maps the file with
bmap() which no pseudo filesystem implements.

So this series adds SB_I_PSEUDO to state that the regular files of a
filesystem are kernel interfaces and not storage and makes all seven
refuse such files.

I didn't want to sprinkle SB_I_PSEUDO over all pseudo filesystems one by
one. Instead there's now a common initialization point for all of them
via fc_init_pseudo().

init_pseudo() uses it for the internal pseudo filesystems and all
mountable pseudo filesystems call it from their ->init_fs_context().

kernfs does it once in kernfs_get_tree(). It raises SB_I_PSEUDO,
SB_I_NOEXEC and SB_I_NODEV. Pseudo filesystems never hold executables or
device nodes. Some of them raised SB_I_NOEXEC and SB_I_NODEV already,
most didn't.

I went through every single one of them. None of them needs to execute
anything. The files that can be mmap()ed map data and the tracing ring
buffer refuses VM_EXEC anyway.

SB_I_NODEV is cleared again by devpts, binderfs and selinuxfs. The first
two did that already. selinuxfs needs it because Android init opens
/sys/fs/selinux/null by path as /dev/null doesn't exist yet at that
point. Note that systemd mounts most of these filesystems with noexec
and nodev already.

file_check_backing() looks at d_real_inode(). overlayfs happily stacks on
top of sysfs, cgroup2, debugfs, tracefs, configfs and securityfs and
reads of such overlayfs files are served by the pseudo file. Only procfs
and binfmt_misc are refused as they set s_stack_depth to
FILESYSTEM_MAX_STACK_DEPTH.

Whether all pseudo filesystems should refuse stacking is a separate
discussion. overlayfs reads the lower file with the mounter's
credentials so a root-mounted overlayfs on top of a sysfs directory
hands capability gated reads to every reader. With SB_I_PSEUDO overlayfs
could easily refuse them.

The first three patches are independent fixes. Loop never checked
whether its backing file is open for reading. It relied on
vfs_iter_read() refusing such files. Direct I/O never went through
vfs_iter_read() and since v6.15 buffered I/O doesn't either. So whoever
has a loop device can read files they could only open for writing. And
the nvme target's file backend and the scsi target's fileio backend call
->read_iter() and ->write_iter() without checking that they exist.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
Changes in v2:
- Add file_check_backing() and use it in all consumers. It replaces
  file_is_pseudo() and the open-coded file type, open mode and method
  checks.
- nvmet, fileio and zloop refuse everything that isn't a regular file
  or, for nvmet and fileio, a block device.
- fileio: check the protection file as well. (sashiko)
- acct: refuse files on all pseudo filesystems. (Alexander)
- selftests: add nvmet (Bui), fileio, zloop, link, FIFO and character
  device tests.
- Collect tags. They are dropped on the patches that changed.
- Link to v1: https://patch.msgid.link/20261110-work-loop-pseudo-v1-0-4c998976c6c7@kernel.org

---
Christian Brauner (42):
      loop: refuse backing files that aren't open for reading
      nvmet: check that the file backend supports ->{read,write}_iter
      target: fileio: check that the backing file supports ->{read,write}_iter
      fs: add SB_I_PSEUDO
      kernfs: use fc_init_pseudo()
      proc: use fc_init_pseudo()
      binfmt_misc: use fc_init_pseudo()
      mqueue: use fc_init_pseudo()
      bpf: use fc_init_pseudo() for bpffs
      nullfs: use fc_init_pseudo()
      failfs: use fc_init_pseudo()
      rust_binderfs: use fc_init_pseudo()
      devpts: use fc_init_pseudo()
      debugfs: use fc_init_pseudo()
      tracefs: use fc_init_pseudo()
      configfs: use fc_init_pseudo()
      securityfs: use fc_init_pseudo()
      selinux: use fc_init_pseudo() for selinuxfs
      smack: use fc_init_pseudo() for smackfs
      apparmor: use fc_init_pseudo() for apparmorfs
      nfsd: use fc_init_pseudo()
      sunrpc: use fc_init_pseudo() for rpc_pipefs
      fuse: use fc_init_pseudo() for fusectl
      efivarfs: use fc_init_pseudo()
      pstore: use fc_init_pseudo()
      xenfs: use fc_init_pseudo()
      openpromfs: use fc_init_pseudo()
      ocfs2: use fc_init_pseudo() for dlmfs
      s390/hypfs: use fc_init_pseudo()
      powerpc/spufs: use fc_init_pseudo()
      usb: gadget: f_fs: use fc_init_pseudo()
      usb: gadget: gadgetfs: use fc_init_pseudo()
      fs: add file_check_backing()
      loop: refuse files on pseudo filesystems as backing files
      zloop: refuse zone files on pseudo filesystems
      nvmet: refuse files on pseudo filesystems as namespace backing files
      target: fileio: refuse files on pseudo filesystems as backing files
      fuse: refuse files on pseudo filesystems as passthrough backing files
      usb: gadget: f_mass_storage: refuse files on pseudo filesystems
      erofs: refuse files on pseudo filesystems as backing files
      acct: refuse files on pseudo filesystems
      selftests/filesystems: add backing file tests for pseudo files

 arch/powerpc/platforms/cell/spufs/inode.c          |   2 +
 arch/s390
```
