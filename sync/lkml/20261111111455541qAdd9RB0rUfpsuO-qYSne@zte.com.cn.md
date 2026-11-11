---
title: [PATCH v2] ublk: stop reporting zones on an empty response
list: linux-block
message_id: 20261111111455541qAdd9RB0rUfpsuO-qYSne@zte.com.cn
link: https://lore.kernel.org/linux-block/20261111111455541qAdd9RB0rUfpsuO-qYSne@zte.com.cn/
---

# [PATCH v2] ublk: stop reporting zones on an empty response

来源：[https://lore.kernel.org/linux-block/20261111111455541qAdd9RB0rUfpsuO-qYSne@zte.com.cn/](https://lore.kernel.org/linux-block/20261111111455541qAdd9RB0rUfpsuO-qYSne@zte.com.cn/)

```
From: Shao Mingyin <shao.mingyin@zte.com.cn>

ublk_report_zones() treats a zero-length zone as the end of the current
server response and keeps asking for the remaining zones from the sector
after the last reported one.  A response that carries no zone at all
therefore advances neither done_zones nor sector, and the driver issues
REPORT ZONES requests for the same sector forever.  Both BLKREPORTZONE
and the zone revalidation done when the device starts hang, and the task
cannot be killed.

Only a response with no zone cannot make progress.  Terminate the whole
report in that case, and keep following up on a short but non-empty
response as before, which is what sd_zbc and virtio_blk do.

Fixes: 29802d7ca33b ("ublk: enable zoned storage support")
Suggested-by: Ming Lei <tom.leiming@gmail.com>
Cc: stable@vger.kernel.org
Signed-off-by: Shao Mingyin <shao.mingyin@zte.com.cn>
---
v2:
- Stop only when a response carries no zone at all, so that a short but
  non-empty response is still followed up from the advanced sector.
  The v1 form ended the whole report at the first zero-length zone and
  truncated such reports (reported by Ming Lei).
v1: https://lore.kernel.org/all/20261109225110056QQJAEflTHzwYHzwXlMBb_@zte.com.cn/

 drivers/block/ublk_drv.c | 7 ++++++-
 1 file changed, 6 insertions(+), 1 deletion(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -661,6 +661,7 @@ static int ublk_report_zones(struct gendisk *disk, sector_t sector,
 		struct request *req;
 		struct ublk_zoned_report_desc desc;
 		blk_status_t status;
+		unsigned int i;
 
 		memset(buffer, 0, buffer_length);
 
@@ -689,7 +690,7 @@ static int ublk_report_zones(struct gendisk *disk, sector_t sector,
 		if (ret)
 			goto out;
 
-		for (unsigned int i = 0; i < zones_in_request; i++) {
+		for (i = 0; i < zones_in_request; i++) {
 			struct blk_zone *zone = buffer + i;
 
 			/* A zero length zone means no more zones in this response */
@@ -704,6 +705,10 @@ static int ublk_report_zones(struct gendisk *disk, sector_t sector,
 			sector += zone_size_sectors;
 
 		}
+
+		/* An empty response cannot make progress, stop asking. */
+		if (!i)
+			break;
 	}
 
 	ret = done_zones;
-- 
2.27.0
```
