---
title: [PATCH v2 0/4] Some cleanup for page migration
list: linux-mm
message_id: cover.1629008158.git.baolin.wang@linux.alibaba.com
link: https://lore.kernel.org/linux-mm/cover.1629008158.git.baolin.wang@linux.alibaba.com/
---

# [PATCH v2 0/4] Some cleanup for page migration

来源：[https://lore.kernel.org/linux-mm/cover.1629008158.git.baolin.wang@linux.alibaba.com/](https://lore.kernel.org/linux-mm/cover.1629008158.git.baolin.wang@linux.alibaba.com/)

```
Hi,

This patch set did some cleanup and improvements for the page migration,
please help to review. Thanks a lot.

Changes from v1:
 - Add reviewed-by tags.
 - Add more comments for patch 1.
 - Drop unnecessary patch 5 from this patch set.

Baolin Wang (4):
  mm: migrate: Move the page count validation to the proper place
  mm: migrate: Introduce a local variable to get the number of pages
  mm: migrate: Fix the incorrect function name in comments
  mm: migrate: Change to use bool type for 'page_was_mapped'

 mm/migrate.c | 21 ++++++++++-----------
 1 file changed, 10 insertions(+), 11 deletions(-)

-- 
1.8.3.1
```
