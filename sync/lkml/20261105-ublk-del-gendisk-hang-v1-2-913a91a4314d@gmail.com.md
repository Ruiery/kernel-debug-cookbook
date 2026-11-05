---
title: [PATCH 2/2] ublk: don't take ublk_ctl_mutex in DEL_DEV
list: linux-block
message_id: 20261105-ublk-del-gendisk-hang-v1-2-913a91a4314d@gmail.com
link: https://lore.kernel.org/linux-block/20261105-ublk-del-gendisk-hang-v1-2-913a91a4314d@gmail.com/
---

# [PATCH 2/2] ublk: don't take ublk_ctl_mutex in DEL_DEV

来源：[https://lore.kernel.org/linux-block/20261105-ublk-del-gendisk-hang-v1-2-913a91a4314d@gmail.com/](https://lore.kernel.org/linux-block/20261105-ublk-del-gendisk-hang-v1-2-913a91a4314d@gmail.com/)

```
From: Mark Korenberg <socketpair@gmail.com>

ublk_ctrl_del_dev() holds the global ublk_ctl_mutex across
ublk_remove(). Stopping the device calls del_gendisk(), which syncs the
filesystem on the disk. If that filesystem is stuck, DEL_DEV never
returns, and ADD_DEV and DEL_DEV of every other ublk device wait for
ublk_ctl_mutex behind it, until reboot. This happens with the server
alive, and also when it dies: the release work then hangs in the same
del_gendisk() with ub->mutex held, and DEL_DEV sleeps on ub->mutex
uninterruptibly, holding ublk_ctl_mutex.

DEL_DEV doesn't need the mutex. ADD_DEV is done with the device when
DEL_DEV finds it: the device is found by its id only once it is set up,
since the previous patch. Claiming UB_STATE_DELETED with
test_and_set_bit() lets only one DEL_DEV remove the device, and the
device number is freed under ublk_idr_lock on release. The mutex also
protected unprivileged_ublks_added: make it atomic. ADD_DEV still
checks and increments it under the mutex, so a decrement without it
can only lower the count, and the limit holds.

A second DEL_DEV of the same device used to wait for the first one on
ublk_ctl_mutex. Now it sees UB_STATE_DELETED and, unless it is
DEL_DEV_ASYNC, waits interruptibly for the device number to be freed.
The counter is decremented once the device is removed, so at the limit
ADD_DEV of an unprivileged device fails with -EACCES instead of waiting
for the removal, and the limit is never exceeded, even if the removal
never completes.

Reproducer: XFS on a ublk loop device with an external log on
dm-linear; "dmsetup suspend --nolockfs --noflush" the log device, write
a file and syncfs, SIGKILL the ublk server or not, DEL_DEV the device,
ADD_DEV another one. Before, ADD_DEV hangs on ublk_ctl_mutex until the
log device is resumed. After, it completes; only the DEL_DEV of the
device with the stuck filesystem waits.

Signed-off-by: Mark Korenberg <socketpair@gmail.com>
---
 drivers/block/ublk_drv.c | 37 ++++++++++++++++---------------------
 1 file changed, 16 insertions(+), 21 deletions(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 14d2823a92e5..40f521077bc9 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -881,7 +881,8 @@ static ssize_t ublk_batch_copy_io_tags(struct ublk_batch_fetch_cmd *fcmd,
  * by cgroup.
  */
 static unsigned int unprivileged_ublks_max = 64;
-static unsigned int unprivileged_ublks_added; /* protected by ublk_ctl_mutex */
+/* checked and incremented under ublk_ctl_mutex, decremented without it */
+static atomic_t unprivileged_ublks_added = ATOMIC_INIT(0);
 
 static struct miscdevice ublk_misc;
 
@@ -4486,7 +4487,7 @@ static int ublk_add_chdev(struct ublk_device *ub)
 		goto fail;
 
 	if (ub->dev_info.flags & UBLK_F_UNPRIVILEGED_DEV)
-		unprivileged_ublks_added++;
+		atomic_inc(&unprivileged_ublks_added);
 	return 0;
  fail:
 	put_device(dev);
@@ -4518,15 +4519,9 @@ static int ublk_add_tag_set(struct ublk_device *ub)
 
 static void ublk_remove(struct ublk_device *ub)
 {
-	bool unprivileged;
-
 	ublk_stop_dev(ub);
 	cdev_device_del(&ub->cdev, &ub->cdev_dev);
-	unprivileged = ub->dev_info.flags & UBLK_F_UNPRIVILEGED_DEV;
 	ublk_put_device(ub);
-
-	if (unprivileged)
-		unprivileged_ublks_added--;
 }
 
 static struct ublk_device *ublk_get_device_from_id(int idx)
@@ -4916,7 +4911,7 @@ static int ublk_ctrl_add_dev(const struct ublksrv_ctrl_cmd *header)
 
 	ret = -EACCES;
 	if ((info.flags & UBLK_F_UNPRIVILEGED_DEV) &&
-	    unprivileged_ublks_added >= unprivileged_ublks_max)
+	    atomic_read(&unprivileged_ublks_added) >= unprivileged_ublks_max)
 		goto out_unlock;
 
 	ret = -ENOMEM;
@@ -5042,23 +5037,23 @@ static int ublk_ctrl_del_dev(struct ublk_device **p_ub, bool wait)
 {
 	struct ublk_device *ub = *p_ub;
 	int idx = ub->ub_number;
-	int ret;
-
-	ret = mutex_lock_killable(&ublk_ctl_mutex);
-	if (ret)
-		return ret;
+	bool unprivileged = ub->dev_info.flags & UBLK_F_UNPRIVILEGED_DEV;
 
-	if (!test_bit(UB_STATE_DELETED, &ub->state)) {
+	/*
+	 * Don't take ublk_ctl_mutex: stopping the device may wait for the
+	 * filesystem on its disk indefinitely, and ADD_DEV and DEL_DEV of all
+	 * other ublk devices would wait for that too. ADD_DEV is done with the
+	 * device, it is found by its id only then.
+	 */
+	if (!test_and_set_bit(UB_STATE_DELETED, &ub->state)) {
 		ublk_remove(ub);
-		set_bit(UB_STATE_DELETED, &ub->state);
+		if (unprivileged)
+			atomic_dec(&unprivileged_ublks_added);
 	}
 
-	mutex_unlock(&ublk_ctl_mutex);
-
 	/*
-	 * Drop the reference outside ublk_ctl_mutex: if it is the last one,
-	 * the release frees the tag set, which waits for an SRCU grace period,
-	 * and holding the mutex would serialize concurrent deletions on it.
+	 * If this is the last reference, the release frees the tag set, which
+	 * waits for an SRCU grace period.
 	 */
 	*p_ub = NULL;
 	ublk_put_device(ub);

-- 
2.56.0
```
