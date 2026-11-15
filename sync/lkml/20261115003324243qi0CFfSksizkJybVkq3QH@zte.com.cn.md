---
title: [PATCH 0/2] z2ram: preserve request data and Zorro RAM ownership
list: linux-block
message_id: 20261115003324243qi0CFfSksizkJybVkq3QH@zte.com.cn
link: https://lore.kernel.org/linux-block/20261115003324243qi0CFfSksizkJybVkq3QH@zte.com.cn/
---

# [PATCH 0/2] z2ram: preserve request data and Zorro RAM ownership

来源：[https://lore.kernel.org/linux-block/20261115003324243qi0CFfSksizkJybVkq3QH@zte.com.cn/](https://lore.kernel.org/linux-block/20261115003324243qi0CFfSksizkJybVkq3QH@zte.com.cn/)

```
Fix two independent data integrity issues in z2ram: completing a whole
request after copying only its first segment, and returning different
Zorro RAM chunks from those allocated when the module is unloaded.
Both changes use the existing backing-memory map. They can be reviewed
and applied separately; the supplied order is the request fix followed
by the bitmap fix.

Built for m68k with amiga_defconfig and W=1. Source-level A/B tests use
the actual request, allocation and unload functions with substitutes for
requests, bitmap state, memory addresses and unrelated teardown. They
cover multi-segment and cross-chunk read/write operations and bitmap
layouts with holes and entries above bit 63. No Amiga hardware testing
was performed.

Shao Mingyin (2):
  z2ram: copy every segment before completing a request
  z2ram: return the allocated Zorro RAM chunks on unload

 drivers/block/z2ram.c | 45 ++++++++++++++++++++++++++++-----------------
 1 file changed, 28 insertions(+), 17 deletions(-)

base-commit: 84abb955b1015477aa11a96e2f3ac1b938b77f48
```
