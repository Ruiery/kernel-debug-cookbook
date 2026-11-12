---
title: [PATCH] block: fix PF_BLOCK_TS/current->plug ordering in blk_finish_plug()
list: linux-block
message_id: 20261112-blk-plug-fix-v1-1-7fa2a6215b8d@mediatek.com
link: https://lore.kernel.org/linux-block/20261112-blk-plug-fix-v1-1-7fa2a6215b8d@mediatek.com/
---

# [PATCH] block: fix PF_BLOCK_TS/current->plug ordering in blk_finish_plug()

来源：[https://lore.kernel.org/linux-block/20261112-blk-plug-fix-v1-1-7fa2a6215b8d@mediatek.com/](https://lore.kernel.org/linux-block/20261112-blk-plug-fix-v1-1-7fa2a6215b8d@mediatek.com/)

```
From: Zi-Hao Huang <zi-hao.huang@mediatek.com>

blk_plug_invalidate_ts() runs on context switch and assumes that
PF_BLOCK_TS set implies current->plug != NULL. blk_finish_plug() breaks
this: it clears PF_BLOCK_TS in __blk_flush_plug() and then sets
current->plug = NULL, with plain accesses.

clang inlines __blk_flush_plug() and emits the store to current->plug
before the store that clears the flag (arm64, Android common kernel):

  ldr  w8, [x20, #0x44]     // w8 = current->flags
  str  xzr, [x20, #0xaa8]   // current->plug = NULL
  and  w8, w8, #0xdfffffff  // w8 &= ~PF_BLOCK_TS  <- preempted here
  str  w8, [x20, #0x44]     // current->flags = w8

If an interrupt hits there and preempts the task, the task is later
scheduled back in with PF_BLOCK_TS set and no plug, and
blk_plug_invalidate_ts() writes to NULL + 0x20 (plug->cur_ktime):

  Unable to handle kernel NULL pointer dereference at 0000000000000020
  pc : __schedule+0x108c
   preempt_schedule_irq+0x48/0xa8
   el1_interrupt+0x48/0x8c
   blk_finish_plug+0x6c/0x18c
   ext4_do_writepages+0xd3c/0xef8

The window is only a few instructions wide, so this is rare. It was hit
at cycle 127 of a warm reboot stress test.

Add a compiler barrier so the flag is cleared before the plug is
dropped. A compiler barrier is enough because the race is with
preemption of the same task on the same CPU. With the barrier, the same
build stores current->flags before current->plug.

Fixes: 06b23f92af87 ("block: update cached timestamp post schedule/preemption")
Cc: stable@vger.kernel.org # v6.9+
Signed-off-by: Zi-Hao Huang <zi-hao.huang@mediatek.com>
---
 block/blk-core.c | 6 ++++++
 1 file changed, 6 insertions(+)

diff --git a/block/blk-core.c b/block/blk-core.c
index 8836c7028568..ad2a8e4fe7a8 100644
--- a/block/blk-core.c
+++ b/block/blk-core.c
@@ -1299,6 +1299,12 @@ void blk_finish_plug(struct blk_plug *plug)
 {
 	if (plug == current->plug) {
 		__blk_flush_plug(plug, false);
+		/*
+		 * blk_plug_invalidate_ts() runs on context switch and expects a
+		 * plug whenever PF_BLOCK_TS is set, so clear the flag (done in
+		 * __blk_flush_plug()) before dropping the plug.
+		 */
+		barrier();
 		current->plug = NULL;
 	}
 }

---
base-commit: 067c5c24cef23d913b67eaaf71ae67e7169a6620
change-id: 20261112-blk-plug-fix-f068b0223b80

Best regards,
-- 
Zi-Hao Huang <zi-hao.huang@mediatek.com>
```
