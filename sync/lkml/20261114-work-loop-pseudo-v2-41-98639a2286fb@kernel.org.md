---
title: [PATCH RFC v2 41/42] acct: refuse files on pseudo filesystems
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-41-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-41-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 41/42] acct: refuse files on pseudo filesystems

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-41-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-41-98639a2286fb@kernel.org/)

```
acct(2) already refuses to write its records to files on kernel internal
filesystems and to procfs and sysfs files. It recognizes the latter two
by FS_USERNS_MOUNT_RESTRICTED which misses every other pseudo
filesystem. So a cgroup2 or binfmt_misc file is accepted as the
accounting file.

The records are written with the credentials of whoever turned on
accounting so this isn't abusable the way loop is. But files on pseudo
filesystems aren't a place to store accounting records. Use
file_check_backing() to refuse all of them.

SB_NOUSER doesn't need to be checked separately anymore. It is only
raised by pseudo filesystems and by tmpfs instances that are either
kernel internal or can't be mounted.

Suggested-by: Alexander Mikhalitsyn <alex@amutable.com>
Link: https://lore.kernel.org/r/ae189903d4cda27130317a9312d94b53d07415ba.camel@amutable.com
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 kernel/acct.c | 6 +++---
 1 file changed, 3 insertions(+), 3 deletions(-)

diff --git a/kernel/acct.c b/kernel/acct.c
index c440d43479ca5..0c502f778fde0 100644
--- a/kernel/acct.c
+++ b/kernel/acct.c
@@ -245,11 +245,11 @@ static int acct_on(const char __user *name)
 		return -EACCES;
 
 	/* Exclude kernel internal filesystems. */
-	if (file_inode(file)->i_sb->s_flags & (SB_NOUSER | SB_KERNMOUNT))
+	if (file_inode(file)->i_sb->s_flags & SB_KERNMOUNT)
 		return -EINVAL;
 
-	/* Exclude procfs and sysfs. */
-	if (file_inode(file)->i_sb->s_type->fs_flags & FS_USERNS_MOUNT_RESTRICTED)
+	/* Exclude pseudo filesystems. */
+	if (file_check_backing(file, 0, 0))
 		return -EINVAL;
 
 	if (!(file->f_mode & FMODE_CAN_WRITE))

-- 
2.53.0
```
