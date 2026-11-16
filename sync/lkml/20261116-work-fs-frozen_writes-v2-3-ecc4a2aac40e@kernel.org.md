---
title: [PATCH v2 03/17] fs: add file_write guard
list: linux-block
message_id: 20261116-work-fs-frozen_writes-v2-3-ecc4a2aac40e@kernel.org
link: https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-3-ecc4a2aac40e@kernel.org/
---

# [PATCH v2 03/17] fs: add file_write guard

来源：[https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-3-ecc4a2aac40e@kernel.org/](https://lore.kernel.org/linux-block/20261116-work-fs-frozen_writes-v2-3-ecc4a2aac40e@kernel.org/)

```
Add a guard for file_start_write() and file_end_write().

Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 include/linux/fs.h | 5 +++++
 1 file changed, 5 insertions(+)

diff --git a/include/linux/fs.h b/include/linux/fs.h
index 0b66a09fb686a..c156a326e8c89 100644
--- a/include/linux/fs.h
+++ b/include/linux/fs.h
@@ -2782,6 +2782,11 @@ static inline void file_end_write(struct file *file)
 	sb_end_write(file_inode(file)->i_sb);
 }
 
+DEFINE_GUARD(file_write,
+	     struct file *,
+	     file_start_write(_T),
+	     file_end_write(_T))
+
 /**
  * kiocb_start_write - get write access to a superblock for async file io
  * @iocb: the io context we want to submit the write with

-- 
2.53.0
```
