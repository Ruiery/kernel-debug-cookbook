---
title: [PATCH RFC v2 36/42] nvmet: refuse files on pseudo filesystems as namespace backing files
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-36-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-36-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 36/42] nvmet: refuse files on pseudo filesystems as namespace backing files

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-36-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-36-98639a2286fb@kernel.org/)

```
The file backend takes any file that can be opened for reading and
writing. With buffered_io=1 that includes files on procfs or sysfs which
then get read and written by a kernel worker on behalf of the host.
Refuse files on pseudo filesystems just like loop does by switching to
file_check_backing().

Note that the helper only accepts regular files and block devices. A
block device ends up in the file backend when buffered_io is set. But
so far the file backend also took anything else with ->read_iter() and
->write_iter() such as character devices and FIFOs. The size of the
namespace is the size of the inode which is zero for all of them. So
such a namespace was unusable anyway. Refuse them.

Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/nvme/target/io-cmd-file.c | 5 ++---
 1 file changed, 2 insertions(+), 3 deletions(-)

diff --git a/drivers/nvme/target/io-cmd-file.c b/drivers/nvme/target/io-cmd-file.c
index dfa8aa46188c8..2249ad3bb46d8 100644
--- a/drivers/nvme/target/io-cmd-file.c
+++ b/drivers/nvme/target/io-cmd-file.c
@@ -47,10 +47,9 @@ int nvmet_file_ns_enable(struct nvmet_ns *ns)
 		return ret;
 	}
 
-	if (!ns->file->f_op->read_iter || !ns->file->f_op->write_iter) {
-		ret = -EINVAL;
+	ret = file_check_backing(ns->file, FMODE_READ | FMODE_WRITE, S_IFBLK);
+	if (ret)
 		goto err;
-	}
 
 	nvmet_file_ns_revalidate(ns);
 

-- 
2.53.0
```
