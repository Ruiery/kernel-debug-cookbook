---
title: [PATCH 1/2] block: don't request a module for the none elevator
list: linux-block
message_id: 20261111-bug-block-elevator-unchanged-v1-1-583198bd4e21@linux.dev
link: https://lore.kernel.org/linux-block/20261111-bug-block-elevator-unchanged-v1-1-583198bd4e21@linux.dev/
---

# [PATCH 1/2] block: don't request a module for the none elevator

来源：[https://lore.kernel.org/linux-block/20261111-bug-block-elevator-unchanged-v1-1-583198bd4e21@linux.dev/](https://lore.kernel.org/linux-block/20261111-bug-block-elevator-unchanged-v1-1-583198bd4e21@linux.dev/)

```
elv_iosched_store() calls elv_iosched_load_module() for the requested
name before anything else, and loads "<name>-iosched" if no elevator
type of that name is registered. "none" never is, so every write of
"none" to queue/scheduler ends up in request_module("none-iosched").

That runs a modprobe helper which can never find the module, and adds
several milliseconds to every switch to "none", including rewrites of
it by udev rules or tuning tools that set the scheduler on each disk.

Return early for "none", like elevator_change() did before the module
loading moved into elv_iosched_load_module().

Writing queue/scheduler of a null_blk disk 20 times takes (median):

  operation             before (ms)  after (ms)  change
  none -> none                13.09        9.06    -31%
  mq-deadline -> none         11.99        7.96    -34%

Fixes: 734e1a8603128 ("block: Prevent deadlocks when switching elevators")
Signed-off-by: Qiliang Yuan <qiliang.yuan@linux.dev>
---
 block/elevator.c | 3 +++
 1 file changed, 3 insertions(+)

diff --git a/block/elevator.c b/block/elevator.c
index 66edf1a5768a8..9d9b2e84a1288 100644
--- a/block/elevator.c
+++ b/block/elevator.c
@@ -775,6 +775,9 @@ static void elv_iosched_load_module(const char *elevator_name)
 {
 	struct elevator_type *found;
 
+	if (!strncmp(elevator_name, "none", 4))
+		return;
+
 	spin_lock(&elv_list_lock);
 	found = __elevator_find(elevator_name);
 	spin_unlock(&elv_list_lock);

-- 
2.43.0
```
