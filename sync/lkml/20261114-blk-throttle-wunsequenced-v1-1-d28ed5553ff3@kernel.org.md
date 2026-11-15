---
title: [PATCH] blk-throttle: Avoid unsequenced accesses to jiffies in throtl_schedule_pending_timer()
list: linux-block
message_id: 20261114-blk-throttle-wunsequenced-v1-1-d28ed5553ff3@kernel.org
link: https://lore.kernel.org/linux-block/20261114-blk-throttle-wunsequenced-v1-1-d28ed5553ff3@kernel.org/
---

# [PATCH] blk-throttle: Avoid unsequenced accesses to jiffies in throtl_schedule_pending_timer()

来源：[https://lore.kernel.org/linux-block/20261114-blk-throttle-wunsequenced-v1-1-d28ed5553ff3@kernel.org/](https://lore.kernel.org/linux-block/20261114-blk-throttle-wunsequenced-v1-1-d28ed5553ff3@kernel.org/)

```
After a recent improvement in clang to warn on unsequenced accesses to
volatile variables [1], two instances appear in
throtl_schedule_pending_timer(), which can break the build with
CONFIG_WERROR=y / W=e:

  block/blk-throttle.c:469:25: error: unsequenced accesses to volatile qualified 'jiffies' [-Werror,-Wunsequenced]
    469 |                    expires - jiffies, jiffies);
        |                              ~~~~~~~  ^
  block/blk-throttle.c:469:25: error: unsequenced accesses to volatile qualified 'jiffies' [-Werror,-Wunsequenced]
    469 |                    expires - jiffies, jiffies);
        |                              ~~~~~~~  ^

Per C11 5.1.2.3.2, accessing a volatile object is a side effect. Per C11
6.5.2, unsequenced side effects on the same scalar object are undefined
behavior. Per C11 6.5.2.2.10/12, the evaluation of arguments in a
function call is indeterminately sequenced, meaning any side effects in
the arguments are unsequenced.

Add a local variable to hold the value of jiffies before the function
call so that there are no unsequenced side effects, clearing up the
warning.

Cc: stable@vger.kernel.org
Fixes: 69df0ab030c9 ("blk-throttle: separate out throtl_service_queue->pending_timer from throtl_data->dispatch_work")
Closes: https://github.com/ClangBuiltLinux/linux/issues/2191
Link: https://github.com/llvm/llvm-project/commit/955715460eaf9188c241c74750637fc82dfcc423 [1]
Signed-off-by: Nathan Chancellor <nathan@kernel.org>
---
 block/blk-throttle.c | 4 +++-
 1 file changed, 3 insertions(+), 1 deletion(-)

diff --git a/block/blk-throttle.c b/block/blk-throttle.c
index c5e26551956a..a1db2babd846 100644
--- a/block/blk-throttle.c
+++ b/block/blk-throttle.c
@@ -454,6 +454,7 @@ static void throtl_schedule_pending_timer(struct throtl_service_queue *sq,
 					  unsigned long expires)
 {
 	unsigned long max_expire = jiffies + 8 * DFL_THROTL_SLICE;
+	unsigned long j;
 
 	/*
 	 * Since we are adjusting the throttle limit dynamically, the sleep
@@ -465,8 +466,9 @@ static void throtl_schedule_pending_timer(struct throtl_service_queue *sq,
 	if (time_after(expires, max_expire))
 		expires = max_expire;
 	mod_timer(&sq->pending_timer, expires);
+	j = jiffies;
 	throtl_log(sq, "schedule timer. delay=%lu jiffies=%lu",
-		   expires - jiffies, jiffies);
+		   expires - j, j);
 }
 
 /**

---
base-commit: ab43ec385580b8f8abf72d70fa3acbf4e4f098a5
change-id: 20261114-blk-throttle-wunsequenced-ccf308a23c1b

Best regards,
--  
Cheers,
Nathan
```
