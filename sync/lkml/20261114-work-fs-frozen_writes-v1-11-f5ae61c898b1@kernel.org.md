---
title: [PATCH 11/12] bpf: fs/xattr: take freeze protection in the xattr kfuncs
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-11-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-11-f5ae61c898b1@kernel.org/
---

# [PATCH 11/12] bpf: fs/xattr: take freeze protection in the xattr kfuncs

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-11-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-11-f5ae61c898b1@kernel.org/)

```
bpf_set_dentry_xattr() and bpf_remove_dentry_xattr() go through
__vfs_setxattr() and __vfs_removexattr() which leave freeze protection
to the caller. BPF LSM programs call them from sleepable hooks such as
file_open where nobody holds it. So a program can modify a frozen
filesystem.

The hook may already hold freeze protection or locks a frozen
filesystem would make us wait under. So don't wait for a thaw. Fail
with -EBUSY if the filesystem is frozen.

The _locked variants are only used from hooks that run inside setattr,
setxattr, removexattr, unlink and rmdir. Their callers hold freeze
protection already.

Fixes: 56467292794b ("bpf: fs/xattr: Add BPF kfuncs to set and remove xattrs")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/bpf_fs_kfuncs.c | 8 ++++++++
 1 file changed, 8 insertions(+)

diff --git a/fs/bpf_fs_kfuncs.c b/fs/bpf_fs_kfuncs.c
index 35ccd98a4de64..7f61e2efa08ba 100644
--- a/fs/bpf_fs_kfuncs.c
+++ b/fs/bpf_fs_kfuncs.c
@@ -295,9 +295,13 @@ __bpf_kfunc int bpf_set_dentry_xattr(struct dentry *dentry, const char *name__st
 	if (!inode)
 		return -EINVAL;
 
+	/* The hook may hold locks or freeze protection already. */
+	if (!sb_start_write_trylock(inode->i_sb))
+		return -EBUSY;
 	inode_lock(inode);
 	ret = bpf_set_dentry_xattr_locked(dentry, name__str, value_p, flags);
 	inode_unlock(inode);
+	sb_end_write(inode->i_sb);
 	return ret;
 }
 
@@ -323,9 +327,13 @@ __bpf_kfunc int bpf_remove_dentry_xattr(struct dentry *dentry, const char *name_
 	if (!inode)
 		return -EINVAL;
 
+	/* The hook may hold locks or freeze protection already. */
+	if (!sb_start_write_trylock(inode->i_sb))
+		return -EBUSY;
 	inode_lock(inode);
 	ret = bpf_remove_dentry_xattr_locked(dentry, name__str);
 	inode_unlock(inode);
+	sb_end_write(inode->i_sb);
 	return ret;
 }
 

-- 
2.53.0
```
