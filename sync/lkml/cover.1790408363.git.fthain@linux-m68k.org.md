---
title: [PATCH 0/2] block/swim: Minor fixes
list: linux-block
message_id: cover.1790408363.git.fthain@linux-m68k.org
link: https://lore.kernel.org/linux-block/cover.1790408363.git.fthain@linux-m68k.org/
---

# [PATCH 0/2] block/swim: Minor fixes

来源：[https://lore.kernel.org/linux-block/cover.1790408363.git.fthain@linux-m68k.org/](https://lore.kernel.org/linux-block/cover.1790408363.git.fthain@linux-m68k.org/)

```
Two old bugs were reported to me by Stan Johnson while he was testing
my recent patch series, "[PATCH v3] block/swim: Fixes and improvements".
The following patches fix those bugs.

---

Finn Thain (2):
  swim: Return -EROFS when opened with BLK_OPEN_WRITE flag
  swim: Fix FDEJECT ioctl for exclusive open

 drivers/block/swim.c  | 5 +++--
 drivers/block/swim3.c | 2 +-
 2 files changed, 4 insertions(+), 3 deletions(-)

-- 
2.52.0
```
