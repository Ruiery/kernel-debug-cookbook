---
title: [PATCH RFC v2 35/42] zloop: refuse zone files on pseudo filesystems
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-35-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-35-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 35/42] zloop: refuse zone files on pseudo filesystems

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-35-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-35-98639a2286fb@kernel.org/)

```
zloop opens its zone files by name below the base directory but a bind
mount can put any file there, including a procfs or sysfs file. Refuse
files on pseudo filesystems as zone files just like loop does by
switching to file_check_backing().

Note that the helper only accepts regular files. So far zloop took
anything with ->read_iter() and ->write_iter() as a zone file. That
includes character devices, FIFOs and block devices if someone put them
where zloop expects a zone file. Zone files are created by zloop itself
and zloop truncates them to size and to reset and finish zones which
only works for regular files. So refuse everything else.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/block/zloop.c | 5 ++---
 1 file changed, 2 insertions(+), 3 deletions(-)

diff --git a/drivers/block/zloop.c b/drivers/block/zloop.c
index 65634a39b0bfc..6f79b9ddbbe00 100644
--- a/drivers/block/zloop.c
+++ b/drivers/block/zloop.c
@@ -1132,10 +1132,9 @@ static int zloop_init_zone(struct zloop_device *zlo, struct zloop_options *opts,
 		return PTR_ERR(zone->file);
 	}
 
-	if (!zone->file->f_op->read_iter || !zone->file->f_op->write_iter) {
-		ret = -EINVAL;
+	ret = file_check_backing(zone->file, FMODE_READ | FMODE_WRITE, 0);
+	if (ret)
 		goto out_fput;
-	}
 
 	if (zlo->block_size) {
 		ret = zloop_get_block_size(zlo, zone);

-- 
2.53.0
```
