---
title: [PATCH 09/12] coredump: take freeze protection for the truncate
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-9-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-9-f5ae61c898b1@kernel.org/
---

# [PATCH 09/12] coredump: take freeze protection for the truncate

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-9-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-9-f5ae61c898b1@kernel.org/)

```
coredump_file() truncates the core file after filp_open() returned.
The open took freeze protection for the create but dropped it again
before returning and coredump_write() only takes it for the dump
itself. So a freeze that lands in between lets the truncate modify a
frozen filesystem.

Take freeze protection around the truncate like do_ftruncate() does.

Fixes: 14da9200140f ("fs: Protect write paths by sb_start_write - sb_end_write")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/coredump.c | 6 ++++--
 1 file changed, 4 insertions(+), 2 deletions(-)

diff --git a/fs/coredump.c b/fs/coredump.c
index 82ef9d115999a..cc6a0c7e48ce2 100644
--- a/fs/coredump.c
+++ b/fs/coredump.c
@@ -1060,8 +1060,10 @@ static bool coredump_file(struct core_name *cn, struct coredump_params *cprm,
 	}
 	if (!(file->f_mode & FMODE_CAN_WRITE))
 		return false;
-	if (do_truncate(idmap, file->f_path.dentry, 0, 0, file))
-		return false;
+	scoped_guard(super_write, inode->i_sb) {
+		if (do_truncate(idmap, file->f_path.dentry, 0, 0, file))
+			return false;
+	}
 
 	cprm->file = no_free_ptr(file);
 	return true;

-- 
2.53.0
```
