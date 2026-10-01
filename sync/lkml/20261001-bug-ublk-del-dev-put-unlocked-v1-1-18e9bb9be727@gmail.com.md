---
title: [PATCH] ublk: drop the device reference outside ublk_ctl_mutex in DEL_DEV
list: linux-block
source: lkml
message_id: 20261001-bug-ublk-del-dev-put-unlocked-v1-1-18e9bb9be727@gmail.com
link: https://lore.kernel.org/linux-block/20261001-bug-ublk-del-dev-put-unlocked-v1-1-18e9bb9be727@gmail.com/
---

# [PATCH] ublk: drop the device reference outside ublk_ctl_mutex in DEL_DEV

来源：[https://lore.kernel.org/linux-block/20261001-bug-ublk-del-dev-put-unlocked-v1-1-18e9bb9be727@gmail.com/](https://lore.kernel.org/linux-block/20261001-bug-ublk-del-dev-put-unlocked-v1-1-18e9bb9be727@gmail.com/)

```
ublk_ctrl_del_dev() drops its reference to the device while holding the
global ublk_ctl_mutex. When this is the last reference, ublk_cdev_rel()
frees the tag set, and blk_mq_free_tag_set() waits for the pending SRCU
callbacks of the tag set with srcu_barrier(). Every DEL_DEV thus waits
for an SRCU grace period with the mutex held, and deleting devices from
several threads serializes on it.

The release path doesn't need ublk_ctl_mutex. The device number is freed
under ublk_idr_lock, and the last reference is already dropped without
the mutex when the ublk server still has the char device open at
DEL_DEV time, from ublk_ch_release_work_fn().

Drop the reference after unlocking ublk_ctl_mutex.

ublk null target, 4000 single-queue devices, STOP_DEV + DEL_DEV issued
from N threads, 16 vCPU KVM guest:

  threads     before      after
        1     77.6 s     77.6 s
        4     20.1 s     19.4 s
        8     19.3 s      9.0 s
       16     19.2 s      4.1 s

Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
 drivers/block/ublk_drv.c | 9 +++++++--
 1 file changed, 7 insertions(+), 2 deletions(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 66eb55e7162e5..5d237aae51b7b 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -4901,10 +4901,15 @@ static int ublk_ctrl_del_dev(struct ublk_device **p_ub, bool wait)
 		set_bit(UB_STATE_DELETED, &ub->state);
 	}
 
-	/* Mark the reference as consumed */
+	mutex_unlock(&ublk_ctl_mutex);
+
+	/*
+	 * Drop the reference outside ublk_ctl_mutex: if it is the last one,
+	 * the release frees the tag set, which waits for an SRCU grace period,
+	 * and holding the mutex would serialize concurrent deletions on it.
+	 */
 	*p_ub = NULL;
 	ublk_put_device(ub);
-	mutex_unlock(&ublk_ctl_mutex);
 
 	/*
 	 * Wait until the idr is removed, then it can be reused after

---
base-commit: 551c722f40809618230001baccf219193e22fc5a
change-id: 20261001-bug-ublk-del-dev-put-unlocked-a9cc10e60a89

Best regards,
-- 
Qiliang Yuan <odys.yuan@gmail.com>
```
