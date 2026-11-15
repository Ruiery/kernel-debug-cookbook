---
title: [PATCH 2/2] z2ram: return the allocated Zorro RAM chunks on unload
list: linux-block
message_id: 20261115003327071py2fApRTKzNRqgeSpm03u@zte.com.cn
link: https://lore.kernel.org/linux-block/20261115003327071py2fApRTKzNRqgeSpm03u@zte.com.cn/
---

# [PATCH 2/2] z2ram: return the allocated Zorro RAM chunks on unload

来源：[https://lore.kernel.org/linux-block/20261115003327071py2fApRTKzNRqgeSpm03u@zte.com.cn/](https://lore.kernel.org/linux-block/20261115003327071py2fApRTKzNRqgeSpm03u@zte.com.cn/)

```
From: Shao Mingyin <shao.mingyin@zte.com.cn>

get_z2ram() collects whichever chunks are available in
zorro_unused_z2ram, clearing their original bits and storing their
addresses in z2ram_map. Those chunks need not form a prefix of the
Zorro RAM area: chunks already used by the system remain unavailable.

z2_exit() instead sets bits 0 through z2_count - 1. With holes in the
original bitmap this marks memory owned by other users as available
and leaves some of the driver's own chunks reserved. A later allocation
can then reuse memory that is still in use.

Recover each original chunk number from its saved address when
returning it to the bitmap. Keep advancing the map index so the
following Chip RAM cleanup still starts after the Zorro entries.

Cc: stable@vger.kernel.org
Signed-off-by: Shao Mingyin <shao.mingyin@zte.com.cn>
---
Testing:
Built with W=1 using m68k amiga_defconfig. Exercised the actual
allocation and unload functions in a host test program with substitutes
for the Zorro bitmap, memory addresses and unrelated device teardown.
Of eight bitmaps, the base code returns four incorrectly; the fixed code
restores the original bits in all eight. Cases include holes, entries
above bit 63, empty and prefix controls, and all chunks available.
No Amiga hardware test was performed.

The incorrect bit restoration is already present in the initial Linux
git snapshot; its original introducing commit has not been identified.

 drivers/block/z2ram.c | 6 +++++-
 1 file changed, 5 insertions(+), 1 deletion(-)

diff --git a/drivers/block/z2ram.c b/drivers/block/z2ram.c
index 15ef92a9744414b9387f4520dc3c7b2f42bebc87..57df672f62a1a2d3db0149ecfbfc0d213aa5f016 100644
--- a/drivers/block/z2ram.c
+++ b/drivers/block/z2ram.c
@@ -395,7 +395,11 @@ static void __exit z2_exit(void)
 		i = 0;
 
 		for (j = 0; j < z2_count; j++) {
-			set_bit(i++, zorro_unused_z2ram);
+			unsigned long chunk = (z2ram_map[i++] -
+				(unsigned long)ZTWO_VADDR(Z2RAM_START)) >>
+				Z2RAM_CHUNKSHIFT;
+
+			set_bit(chunk, zorro_unused_z2ram);
 		}
 
 		for (j = 0; j < chip_count; j++) {
-- 
2.43.0
```
