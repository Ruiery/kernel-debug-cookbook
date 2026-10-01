---
title: [PATCH] rust: block: implement `Send` and `Sync` for `TagSet`
list: linux-block
message_id: 20260930-tag-set-send-sync-v1-1-51acdb36f4bb@kernel.org
link: https://lore.kernel.org/linux-block/20260930-tag-set-send-sync-v1-1-51acdb36f4bb@kernel.org/
---

# [PATCH] rust: block: implement `Send` and `Sync` for `TagSet`

来源：[https://lore.kernel.org/linux-block/20260930-tag-set-send-sync-v1-1-51acdb36f4bb@kernel.org/](https://lore.kernel.org/linux-block/20260930-tag-set-send-sync-v1-1-51acdb36f4bb@kernel.org/)

```
`TagSet` never implemented `Send` or `Sync`. This did not matter until
commit "rust: block: fix `Send` bound for `GenDisk`" made `GenDisk: Send`
depend on `Arc<TagSet<T>>: Send`, which in turn requires `TagSet<T>: Send +
Sync`. With that bound unsatisfiable, `GenDisk` is never `Send`, and the
rnull driver fails to build once configfs requires `GroupOperations::Child:
Send`.

`TagSet` owns no data typed by `T`. It only wraps the C `struct
blk_mq_tag_set`, which can be dropped from any thread by calling
`blk_mq_free_tag_set`. Thus, implement `Send` and `Sync` for `TagSet`
unconditionally.

Reported-by: Thorsten Leemhuis <linux@leemhuis.info>
Closes: https://lore.kernel.org/r/d1381ed8-eab8-4fd7-8b15-1e94876d7099@leemhuis.info
Suggested-by: Gary Guo <gary@garyguo.net>
Signed-off-by: Andreas Hindborg <a.hindborg@kernel.org>
---
Hi Jens,

Please pick this patch to resolve a problematic rust configfs/block
interaction in linux-next [1].

Best regards,
Andreas Hindborg

[1] https://lore.kernel.org/r/d1381ed8-eab8-4fd7-8b15-1e94876d7099@leemhuis.info
---
 rust/kernel/block/mq/tag_set.rs | 7 +++++++
 1 file changed, 7 insertions(+)

diff --git a/rust/kernel/block/mq/tag_set.rs b/rust/kernel/block/mq/tag_set.rs
index dae9df408a86..00d29688f920 100644
--- a/rust/kernel/block/mq/tag_set.rs
+++ b/rust/kernel/block/mq/tag_set.rs
@@ -83,3 +83,10 @@ fn drop(self: Pin<&mut Self>) {
         unsafe { bindings::blk_mq_free_tag_set(self.inner.get()) };
     }
 }
+
+// SAFETY: It is safe to transfer ownership of `TagSet` between threads.
+unsafe impl<T: Operations> Send for TagSet<T> {}
+
+// SAFETY: It is safe to share `&TagSet` across threads. `TagSet` exposes no
+// `&self` methods that mutate the contained `blk_mq_tag_set`.
+unsafe impl<T: Operations> Sync for TagSet<T> {}

---
base-commit: df2908090cda368b01ff43709f51890076c56157
change-id: 20260930-tag-set-send-sync-c4d64515e1e0

Best regards,
--  
Andreas Hindborg <a.hindborg@kernel.org>
```
