---
title: [PATCH RFC v2 01/42] loop: refuse backing files that aren't open for reading
list: linux-block
message_id: 20261114-work-loop-pseudo-v2-1-98639a2286fb@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-1-98639a2286fb@kernel.org/
---

# [PATCH RFC v2 01/42] loop: refuse backing files that aren't open for reading

来源：[https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-1-98639a2286fb@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-loop-pseudo-v2-1-98639a2286fb@kernel.org/)

```
loop_configure() takes any file as long as it implements ->read_iter().
Loop itself never checked whether the file was actually opened for
reading. Buffered I/O went through vfs_iter_read() which refuses files
without FMODE_READ. Direct I/O has called ->read_iter() of the backing
file directly ever since loop grew support for it.

Since commit f2fed441c69b ("loop: stop using vfs_iter_{read,write} for
buffered I/O") buffered I/O calls ->read_iter() directly as well. That
commit was about O_DIRECT handling and the FMODE_READ check went away
as a side effect.

So whoever can set up a loop device can read a file it was only allowed
to open for writing. Open the file O_WRONLY, configure a loop device
with it and read the contents through the loop device.

Refuse backing files that aren't open for reading. Loop always reads
from its backing file so a write-only backing file never made sense in
the first place.

Fixes: bc07c10a3603 ("block: loop: support DIO & AIO")
Fixes: f2fed441c69b ("loop: stop using vfs_iter_{read,write} for buffered I/O")
Cc: stable@vger.kernel.org
Reviewed-by: Jan Kara <jack@suse.cz>
Reviewed-by: Christoph Hellwig <hch@lst.de>
Reviewed-by: Alexander Mikhalitsyn <alex@amutable.com>
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 drivers/block/loop.c | 3 +++
 1 file changed, 3 insertions(+)

diff --git a/drivers/block/loop.c b/drivers/block/loop.c
index a3325ceab484a..c96e35c3ef423 100644
--- a/drivers/block/loop.c
+++ b/drivers/block/loop.c
@@ -528,6 +528,9 @@ static void loop_assign_backing_file(struct loop_device *lo, struct file *file)
 
 static int loop_check_backing_file(struct file *file)
 {
+	if (!(file->f_mode & FMODE_READ))
+		return -EBADF;
+
 	if (!file->f_op->read_iter)
 		return -EINVAL;
 

-- 
2.53.0
```
