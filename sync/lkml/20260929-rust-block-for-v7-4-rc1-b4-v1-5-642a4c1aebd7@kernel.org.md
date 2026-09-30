---
title: [PATCH GIT PULL 5/9] rust: block: gen_disk: set fops.owner from driver module pointer
list: linux-block
message_id: 20260929-rust-block-for-v7-4-rc1-b4-v1-5-642a4c1aebd7@kernel.org
link: https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-5-642a4c1aebd7@kernel.org/
---

# [PATCH GIT PULL 5/9] rust: block: gen_disk: set fops.owner from driver module pointer

来源：[https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-5-642a4c1aebd7@kernel.org/](https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-5-642a4c1aebd7@kernel.org/)

```
From: Alvin Sun <alvin.sun@linux.dev>

Set `fops.owner` from the driver module pointer via
`this_module::<T::OwnerModule>().as_ptr()` instead of defaulting to
null, so the module cannot be unloaded while a block device is still
in use.

Signed-off-by: Alvin Sun <alvin.sun@linux.dev>
Link: https://msgid.link/20260811-fix-gendisk-owner-v1-1-c0fe4a449ecb@linux.dev
Signed-off-by: Andreas Hindborg <a.hindborg@kernel.org>
---
 rust/kernel/block/mq/gen_disk.rs | 34 ++++++++++------------------------
 1 file changed, 10 insertions(+), 24 deletions(-)

diff --git a/rust/kernel/block/mq/gen_disk.rs b/rust/kernel/block/mq/gen_disk.rs
index 080dedb5d5d9..90d364ab3bf2 100644
--- a/rust/kernel/block/mq/gen_disk.rs
+++ b/rust/kernel/block/mq/gen_disk.rs
@@ -137,30 +137,9 @@ pub fn build<T: Operations>(
             )
         })?;
 
-        const TABLE: bindings::block_device_operations = bindings::block_device_operations {
-            submit_bio: None,
-            open: None,
-            release: None,
-            ioctl: None,
-            compat_ioctl: None,
-            check_events: None,
-            unlock_native_capacity: None,
-            getgeo: None,
-            set_read_only: None,
-            swap_slot_free_notify: None,
-            report_zones: None,
-            devnode: None,
-            alternative_gpt_sector: None,
-            get_unique_id: None,
-            // TODO: Set to `THIS_MODULE`.
-            owner: core::ptr::null_mut(),
-            pr_ops: core::ptr::null_mut(),
-            free_disk: None,
-            poll_bio: None,
-        };
-
-        // SAFETY: `gendisk` is a valid pointer as we initialized it above
-        unsafe { (*gendisk).fops = &TABLE };
+        // SAFETY: `gendisk` is a valid pointer. We have exclusive access,
+        // since the disk is not added to the VFS yet.
+        unsafe { (*gendisk).fops = &GenDisk::<T>::VTABLE };
 
         let cleanup_failure = ScopeGuard::new_with_data((gendisk, data), |(gendisk, data)| {
             // SAFETY: `gendisk` came from `__blk_mq_alloc_disk()` above and
@@ -223,6 +202,13 @@ pub struct GenDisk<T: Operations> {
     gendisk: *mut bindings::gendisk,
 }
 
+impl<T: Operations> GenDisk<T> {
+    const VTABLE: bindings::block_device_operations = bindings::block_device_operations {
+        owner: crate::module::this_module::<T::OwnerModule>().as_ptr(),
+        ..pin_init::zeroed()
+    };
+}
+
 // SAFETY: `GenDisk` is an owned pointer to a `struct gendisk` and an `Arc` to a
 // `TagSet`. It is safe to send this to other threads as long as these two are `Send`.
 unsafe impl<T> Send for GenDisk<T>

-- 
2.54.0
```
