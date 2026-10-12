---
title: [PATCH] loop: remove support for swapping loop fds
list: linux-block
message_id: 20261012-work-loop-change_fd-v1-1-3cf4ec349bbb@kernel.org
link: https://lore.kernel.org/linux-block/20261012-work-loop-change_fd-v1-1-3cf4ec349bbb@kernel.org/
---

# [PATCH] loop: remove support for swapping loop fds

来源：[https://lore.kernel.org/linux-block/20261012-work-loop-change_fd-v1-1-3cf4ec349bbb@kernel.org/](https://lore.kernel.org/linux-block/20261012-work-loop-change_fd-v1-1-3cf4ec349bbb@kernel.org/)

```
LOOP_CHANGE_FD swaps the backing file of a bound read-only loop device
for another file of the same size. The comment above loop_change_fd()
says this is for installers that want to free the original image and
for HA setups that want to switch to another copy of the image. When we
discussed deprecating it in 2023 (cf. [1]) we found no users at all:
zero hits on codesearch.debian.net, GitHub code search and
cs.android.com. The only things that exercise it are strace, LTP,
stress-ng and blktests. Everyone agreed to drop it. I just never sent
the patch.

Since then we found several more problems with it and all of them are
structural. The ioctl changes what a block device is backed by after a
filesystem has been mounted on it and nothing else in the kernel does
that.

(1) It creates a lock order cycle.

    loop_change_fd() is the only loop operation that calls
    disk_force_media_change() on a bound device while a filesystem can
    be mounted on it. loop_configure() calls it before the device is
    bound and __loop_clr_fd() after the last opener is gone. And it
    calls it with lo->lo_mutex held.

    Since v6.6 disk_force_media_change() doesn't just bump the disk
    sequence number. It calls bdev_mark_dead() which calls into the
    holder, i.e., fs_bdev_mark_dead(), which takes sb->s_umount of
    every superblock on that device. So LOOP_CHANGE_FD gives us:

        lo_mutex -> s_umount

    Mounting a filesystem takes s_umount in sget_fc() and then opens
    the block device in setup_bdev_super(). That takes
    disk->open_mutex and calls lo_open() which takes lo_mutex:

        s_umount -> open_mutex -> lo_mutex

    That's a cycle. Lockdep reports it as soon as LOOP_CHANGE_FD is
    used on a device that has a filesystem mounted on it. This was
    recently hit with erofs where LOOP_CHANGE_FD raced with umount and
    a concurrent open of the loop device. And it is a real deadlock:
    the mounter holds s_umount and waits for open_mutex, the opener
    holds open_mutex and waits in lo_open() for lo_mutex, and the
    LOOP_CHANGE_FD caller holds lo_mutex and waits in
    fs_bdev_mark_dead() for that superblock.

    Note that we went through the block layer in v6.7 to guarantee
    that s_umount is never taken under open_mutex. LOOP_CHANGE_FD is
    the reverse direction and it was simply never considered.

(2) The use-case it was added for doesn't work anymore.

    fs_bdev_mark_dead() shuts the filesystem down. For ext4, xfs and
    btrfs that means ->shutdown() is called and the mounted filesystem
    returns -EIO from then on. So swapping the image under a mounted
    filesystem can't work for any filesystem that implements shutdown.
    It only survives on erofs because erofs deliberately doesn't
    implement ->shutdown() and ->remove_bdev(). Commit 69139a62a918
    ("erofs: open via dedicated fs bdev helpers") explicitly cites
    loop_change_fd() as the reason why it shouldn't. IOW, an ioctl
    without users dictates what a filesystem is allowed to do on
    device removal.

    And it never worked on partitions. disk_force_media_change() only
    acts on disk->part0 so a filesystem mounted on loop0p1 isn't told
    anything when the image under it is swapped.

(3) It can create superblock pin cycles.

    loop_validate_file() only guards against loop-on-loop recursion.
    It doesn't stop LOOP_CHANGE_FD from pointing a bound device at a
    file on the filesystem that is mounted from that very device, or
    two devices at files on each other's filesystems, or a device at a
    file on a fuse mount whose passthrough backing file lives on the
    loop mount. Static setups can't form these cycles because the
    backing file is opened before the filesystem on top of it exists.
    LOOP_CHANGE_FD is the only block layer path where the edge is
    added afterwards.

    The result is a cycle of superblocks: the backing file pins the
    mount, the mount pins the superblock, the superblock holds the
    device open and the device holds the backing file. umount detaches
    the mounts but nothing ever frees them and the mount namespace
    they live in leaks with them. This is not a cycle of mounts so
    nothing in mount teardown can break it. It's root-only, but it is
    a permanent leak that can't be undone.

(4) It makes filesystem stacking dynamic.

    s_stack_depth assumes that the dependencies between filesystems
    are fixed when a filesystem is mounted. With LOOP_CHANGE_FD the
    image of a mounted filesystem can be moved onto another filesystem
    at any later time, so a loop-mounted filesystem is at stacking
    depth 0 no matter what its image ends up on. That is the hole in
    the stacking deadlock discussion for fanotify pre-content events
    (cf. [2]).

The partition handling of LOOP_CHANGE_FD has been broken since v7.1
and nobody noticed until Daan ran into it in August (cf. [3]). That's
about the level of use this ioctl sees.

So let's remove it. LOOP_CHANGE_FD now returns -EOPNOTSUPP.

[1]: https://lore.kernel.org/r/20231023-biberbau-spatzen-282ccea0825a@brauner
     https://lore.kernel.org/r/20231024-entfuhr-sachbezogen-aab33dec4087@brauner
[2]: https://lore.kernel.org/r/CAOQ4uxi2Mx4ZB48DhQJWOvt6UBur3LnrkttgRjo72U4+Cu81iQ@mail.gmail.com
     https://lore.kernel.org/r/20260617-vorfahren-haften-nullnummer-b0d6fccadae3@brauner
[3]: https://lore.kernel.org/r/20260806-b4-loop-nbd-stale-partitions-v1-1-67bb75a8d7be@amutable.com

Signed-off-by: Christian Brauner <brauner@kernel.org>
---
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/block/loop.c | 112 ++-------------------------------------------------
 1 file changed, 4 insertions(+), 108 deletions(-)

diff --git a/drivers/block/loop.c b/drivers/block/loop.c
index 758c20678bf6..aabaaacdb4fa 100644
--- a/drivers/block/loop.c
+++ b/drivers/block/loop.c
@@ -105,7 +105,7 @@ static DEFINE_MUTEX(loop_validate_mutex);
  *
  * Since loop_validate_file() traverses on other "struct loop_device" if
  * is_loop_device() is true, we need a global lock for serializing concurrent
- * loop_configure()/loop_change_fd()/__loop_clr_fd() calls.
+ * loop_configure()/__loop_clr_fd() calls.
  */
 static int loop_global_lock_killable(struct loop_device *lo, bool global)
 {
@@ -537,109 +537,6 @@ static int loop_check_backing_file(struct file *file)
 	return 0;
 }
 
-/*
- * loop_change_fd switched the backing store of a loopback device to
- * a new file. This is useful for operating system installers to free up
- * the original file and in High Availability environments to switch to
- * an alternative location for the content in case of server meltdown.
- * This can only work if the loop device is used read-only, and if the
- * new backing store is the same size and type as the old backing store.
- */
-static int loop_change_fd(struct loop_device *lo, struct block_device *bdev,
-			  unsigned int arg)
-{
-	struct file *file = fget(arg);
-	struct file *old_file;
-	unsigned int memflags;
-	int error;
-	bool partscan;
-	bool is_loop;
-
-	if (!file)
-		return -EBADF;
-
-	error = loop_check_backing_file(file);
-	if (error) {
-		fput(file);
-		return error;
-	}
-
-	/* suppress uevents while reconfiguring the device */
-	dev_set_uevent_suppress(disk_to_dev(lo->lo_disk), 1);
-
-	is_loop = is_loop_device(file);
-	error = loop_global_lock_killable(lo, is_loop);
-	if (error)
-		goto out_putf;
-	error = -ENXIO;
-	if (lo->lo_state != Lo_bound)
-		goto out_err;
-
-	/* the loop device has to be read-only */
-	error = -EINVAL;
-	if (!(lo->lo_flags & LO_FLAGS_READ_ONLY))
-		goto out_err;
-
-	error = loop_validate_file(file, bdev);
-	if (error)
-		goto out_err;
-
-	old_file = lo->lo_backing_file;
-
-	error = -EINVAL;
-
-	/* size of the new backing store needs to be the same */
-	if (lo_calculate_size(lo, file) != lo_calculate_size(lo, old_file))
-		goto out_err;
-
-	/*
-	 * We might switch to direct I/O mode for the loop device, write back
-	 * all dirty data the page cache now th
```
