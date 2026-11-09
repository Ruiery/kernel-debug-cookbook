---
title: [PATCH] ublk: stop reporting zones on an empty response
list: linux-block
message_id: 20261109225110056QQJAEflTHzwYHzwXlMBb_@zte.com.cn
link: https://lore.kernel.org/linux-block/20261109225110056QQJAEflTHzwYHzwXlMBb_@zte.com.cn/
---

# [PATCH] ublk: stop reporting zones on an empty response

来源：[https://lore.kernel.org/linux-block/20261109225110056QQJAEflTHzwYHzwXlMBb_@zte.com.cn/](https://lore.kernel.org/linux-block/20261109225110056QQJAEflTHzwYHzwXlMBb_@zte.com.cn/)

```
From: Shao Mingyin <shao.mingyin@zte.com.cn>

ublk_report_zones() treats a zero-length zone as the end of a server
response, but only breaks out of the inner loop.  If the server returns
an empty report, done_zones and sector do not advance, so the driver
keeps issuing REPORT ZONES requests at the same sector indefinitely.

Finish the report when the zero-length marker is encountered and return
the number of zones already reported.  Use the existing exit path to
release the report buffer, including when the first response is empty.

Fixes: 29802d7ca33b ("ublk: enable zoned storage support")
Cc: stable@vger.kernel.org
Signed-off-by: Shao Mingyin <shao.mingyin@zte.com.cn>
---
 drivers/block/ublk_drv.c | 6 ++++--
 1 file changed, 4 insertions(+), 2 deletions(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 3d322fa1bc83..5c14daeaebbf 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -693,8 +693,10 @@ static int ublk_report_zones(struct gendisk *disk, sector_t sector,
 			struct blk_zone *zone = buffer + i;
 
 			/* A zero length zone means no more zones in this response */
-			if (!zone->len)
-				break;
+			if (!zone->len) {
+				ret = done_zones;
+				goto out;
+			}
 
 			ret = disk_report_zone(disk, zone, done_zones, args);
 			if (ret)
```
