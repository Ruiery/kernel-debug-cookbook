---
title: [PATCH 8/9] huge tmpfs: decide stat.st_blksize by shmem_is_huge()
list: linux-mm
message_id: af7fb3f9-4415-9e8e-fdac-b1a5253ad21@google.com
link: https://lore.kernel.org/linux-mm/af7fb3f9-4415-9e8e-fdac-b1a5253ad21@google.com/
---

# [PATCH 8/9] huge tmpfs: decide stat.st_blksize by shmem_is_huge()

来源：[https://lore.kernel.org/linux-mm/af7fb3f9-4415-9e8e-fdac-b1a5253ad21@google.com/](https://lore.kernel.org/linux-mm/af7fb3f9-4415-9e8e-fdac-b1a5253ad21@google.com/)

```
4.18 commit 89fdcd262fd4 ("mm: shmem: make stat.st_blksize return huge
page size if THP is on") added is_huge_enabled() to decide st_blksize:
if hugeness is to be defined per file, that will need to be replaced by
shmem_is_huge().

This does give a different answer (No) for small files on a
"huge=within_size" mount: but that can be considered a minor bugfix.
And a different answer (No) for default files on a "huge=advise" mount:
I'm reluctant to complicate it, just to reproduce the same debatable
answer as before.

Signed-off-by: Hugh Dickins <hughd@google.com>
Reviewed-by: Yang Shi <shy828301@gmail.com>
---
 mm/shmem.c | 12 +-----------
 1 file changed, 1 insertion(+), 11 deletions(-)

diff --git a/mm/shmem.c b/mm/shmem.c
index 56ee56b1cab6..b60a7abff27d 100644
--- a/mm/shmem.c
+++ b/mm/shmem.c
@@ -689,15 +689,6 @@ static unsigned long shmem_unused_huge_shrink(struct shmem_sb_info *sbinfo,
 }
 #endif /* CONFIG_TRANSPARENT_HUGEPAGE */
 
-static inline bool is_huge_enabled(struct shmem_sb_info *sbinfo)
-{
-	if (IS_ENABLED(CONFIG_TRANSPARENT_HUGEPAGE) &&
-	    (shmem_huge == SHMEM_HUGE_FORCE || sbinfo->huge) &&
-	    shmem_huge != SHMEM_HUGE_DENY)
-		return true;
-	return false;
-}
-
 /*
  * Like add_to_page_cache_locked, but error if expected item has gone.
  */
@@ -1078,7 +1069,6 @@ static int shmem_getattr(struct user_namespace *mnt_userns,
 {
 	struct inode *inode = path->dentry->d_inode;
 	struct shmem_inode_info *info = SHMEM_I(inode);
-	struct shmem_sb_info *sb_info = SHMEM_SB(inode->i_sb);
 
 	if (info->alloced - info->swapped != inode->i_mapping->nrpages) {
 		spin_lock_irq(&info->lock);
@@ -1087,7 +1077,7 @@ static int shmem_getattr(struct user_namespace *mnt_userns,
 	}
 	generic_fillattr(&init_user_ns, inode, stat);
 
-	if (is_huge_enabled(sb_info))
+	if (shmem_is_huge(NULL, inode, 0))
 		stat->blksize = HPAGE_PMD_SIZE;
 
 	return 0;
-- 
2.26.2
```
