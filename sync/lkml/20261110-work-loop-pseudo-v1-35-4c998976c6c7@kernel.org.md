---
title: [PATCH RFC 35/41] zloop: refuse zone files on pseudo filesystems
list: linux-block
message_id: 20261110-work-loop-pseudo-v1-35-4c998976c6c7@kernel.org
link: https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-35-4c998976c6c7@kernel.org/
---

# [PATCH RFC 35/41] zloop: refuse zone files on pseudo filesystems

来源：[https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-35-4c998976c6c7@kernel.org/](https://lore.kernel.org/linux-block/20261110-work-loop-pseudo-v1-35-4c998976c6c7@kernel.org/)

```
zloop opens its zone files by name below the base directory but a bind
mount can put any file there, including a procfs or sysfs file. Refuse
files on pseudo filesystems as zone files just like loop does.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/block/zloop.c | 5 +++++
 1 file changed, 5 insertions(+)

diff --git a/drivers/block/zloop.c b/drivers/block/zloop.c
index 65634a39b0bf..dcc06dd47b04 100644
--- a/drivers/block/zloop.c
+++ b/drivers/block/zloop.c
@@ -1137,6 +1137,11 @@ static int zloop_init_zone(struct zloop_device *zlo, struct zloop_options *opts,
 		goto out_fput;
 	}
 
+	if (file_is_pseudo(zone->file)) {
+		ret = -EINVAL;
+		goto out_fput;
+	}
+
 	if (zlo->block_size) {
 		ret = zloop_get_block_size(zlo, zone);
 		if (ret)

-- 
2.53.0
```
