---
title: [PATCH RFC v3 33/44] ovl: refuse data-only layers on pseudo filesystems
list: linux-block
message_id: 20261116-work-loop-pseudo-v3-33-8cbbea1cf34f@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-33-8cbbea1cf34f@kernel.org/
---

# [PATCH RFC v3 33/44] ovl: refuse data-only layers on pseudo filesystems

来源：[https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-33-8cbbea1cf34f@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-loop-pseudo-v3-33-8cbbea1cf34f@kernel.org/)

```
The data of a metacopy file can live in a data-only layer. overlayfs
doesn't look that data up when it looks up the file. It only remembers
the absolute redirect and looks up the data lazily the first time
someone needs it. So until then nothing can tell which filesystem holds
the data of such a file.

But a data-only layer has no business being a pseudo filesystem in the
first place. All it does is hold the data of metacopy files and the
regular files of a pseudo filesystem are kernel interfaces, not storage.
So let's refuse data-only layers on superblocks with SB_I_PSEUDO at
mount time.

Data-only layers can be added via the "::" separator in "lowerdir=" and
via "datadir+" by path or by file descriptor. All of them end up at the
end of ctx->lower. So a single check in ovl_get_lowerstack() covers all
of them.

Note that regular lower layers on pseudo filesystems are left alone.
Stacking overlayfs on top of sysfs keeps working.

Suggested-by: Amir Goldstein <amir73il@gmail.com>
Link: https://lore.kernel.org/all/CAOQ4uxhGxpBtMZ5kfuzR1tQAewiecoX7UjXQRo91QjJHH9T_Yw@mail.gmail.com
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/overlayfs/super.c | 8 ++++++++
 1 file changed, 8 insertions(+)

diff --git a/fs/overlayfs/super.c b/fs/overlayfs/super.c
index 39d4d57dec230..719c2569dfeaf 100644
--- a/fs/overlayfs/super.c
+++ b/fs/overlayfs/super.c
@@ -1237,6 +1237,14 @@ static struct ovl_entry *ovl_get_lowerstack(struct super_block *sb,
 	for (i = 0; i < ctx->nr; i++) {
 		l = &ctx->lower[i];
 
+		/* Pseudo filesystems don't hold data for metacopy files. */
+		if (i >= ctx->nr - ctx->nr_data &&
+		    (l->path.dentry->d_sb->s_iflags & SB_I_PSEUDO)) {
+			pr_err("filesystem on %s not supported as data-only layer\n",
+			       l->name);
+			return ERR_PTR(-EINVAL);
+		}
+
 		err = ovl_lower_dir(l->name, &l->path, ofs, &sb->s_stack_depth);
 		if (err)
 			return ERR_PTR(err);

-- 
2.53.0
```
