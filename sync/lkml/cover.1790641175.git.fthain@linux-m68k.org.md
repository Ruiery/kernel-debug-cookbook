---
title: [PATCH v2 0/3] block/swim: Minor fixes
list: linux-block
message_id: cover.1790641175.git.fthain@linux-m68k.org
link: https://lore.kernel.org/linux-block/cover.1790641175.git.fthain@linux-m68k.org/
---

# [PATCH v2 0/3] block/swim: Minor fixes

来源：[https://lore.kernel.org/linux-block/cover.1790641175.git.fthain@linux-m68k.org/](https://lore.kernel.org/linux-block/cover.1790641175.git.fthain@linux-m68k.org/)

```
Two old bugs were reported to me by Stan Johnson while he was testing
my recent patch series, "[PATCH v3] block/swim: Fixes and improvements".
The following patches fix those bugs.

---

Changed since v1:
 - Patch 2/2 was split into two such that each patch alters one driver.
 - 2/3 and 3/3 were revised as described in the commit log entries.
 - Tested-by tags were added.

---

Finn Thain (3):
  swim: Return -EROFS when opened with BLK_OPEN_WRITE flag
  swim: Fix FDEJECT ioctl for exclusive open
  swim3: Fix FDEJECT ioctl for exclusive open

 drivers/block/swim.c  | 10 ++++++----
 drivers/block/swim3.c |  8 +++-----
 2 files changed, 9 insertions(+), 9 deletions(-)
```
