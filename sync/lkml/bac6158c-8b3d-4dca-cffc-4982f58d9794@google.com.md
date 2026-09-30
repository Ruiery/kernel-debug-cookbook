---
title: [PATCH 9/9] shmem: shmem_writepage() split unlikely i915 THP
list: linux-mm
message_id: bac6158c-8b3d-4dca-cffc-4982f58d9794@google.com
link: https://lore.kernel.org/linux-mm/bac6158c-8b3d-4dca-cffc-4982f58d9794@google.com/
---

# [PATCH 9/9] shmem: shmem_writepage() split unlikely i915 THP

来源：[https://lore.kernel.org/linux-mm/bac6158c-8b3d-4dca-cffc-4982f58d9794@google.com/](https://lore.kernel.org/linux-mm/bac6158c-8b3d-4dca-cffc-4982f58d9794@google.com/)

```
drivers/gpu/drm/i915/gem/i915_gem_shmem.c contains a shmem_writeback()
which calls shmem_writepage() from a shrinker: that usually works well
enough; but if /sys/kernel/mm/transparent_hugepage/shmem_enabled has been
set to "always" (intended to be usable) or "force" (forces huge everywhere
for easy testing), shmem_writepage() is surprised to be called with a huge
page, and crashes on the VM_BUG_ON_PAGE(PageCompound) (I did not find out
where the crash happens when CONFIG_DEBUG_VM is off).

LRU page reclaim always splits the shmem huge page first: I'd prefer not
to demand that of i915, so check and split compound in shmem_writepage().

Patch history: when first sent last year
http://lkml.kernel.org/r/alpine.LSU.2.11.2008301401390.5954@eggly.anvils
https://lore.kernel.org/linux-mm/20200919042009.bomzxmrg7%25akpm@linux-foundation.org/
Matthew Wilcox noticed that tail pages were wrongly left clean.  This
version brackets the split with Set and Clear PageDirty as he suggested:
which works very well, even if it falls short of our aspirations.  And
recently I realized that the crash is not limited to the testing option
"force", but affects "always" too: which is more important to fix.

Fixes: 2d6692e642e7 ("drm/i915: Start writeback from the shrinker")
Signed-off-by: Hugh Dickins <hughd@google.com>
Reviewed-by: Shakeel Butt <shakeelb@google.com>
Acked-by: Yang Shi <shy828301@gmail.com>
---
 mm/shmem.c | 14 +++++++++++++-
 1 file changed, 13 insertions(+), 1 deletion(-)

diff --git a/mm/shmem.c b/mm/shmem.c
index b60a7abff27d..a1ba03f39eaa 100644
--- a/mm/shmem.c
+++ b/mm/shmem.c
@@ -1349,7 +1349,19 @@ static int shmem_writepage(struct page *page, struct writeback_control *wbc)
 	swp_entry_t swap;
 	pgoff_t index;
 
-	VM_BUG_ON_PAGE(PageCompound(page), page);
+	/*
+	 * If /sys/kernel/mm/transparent_hugepage/shmem_enabled is "always" or
+	 * "force", drivers/gpu/drm/i915/gem/i915_gem_shmem.c gets huge pages,
+	 * and its shmem_writeback() needs them to be split when swapping.
+	 */
+	if (PageTransCompound(page)) {
+		/* Ensure the subpages are still dirty */
+		SetPageDirty(page);
+		if (split_huge_page(page) < 0)
+			goto redirty;
+		ClearPageDirty(page);
+	}
+
 	BUG_ON(!PageLocked(page));
 	mapping = page->mapping;
 	index = page->index;
-- 
2.26.2
```
