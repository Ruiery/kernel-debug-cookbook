---
title: [PATCH GIT PULL 6/9] rust: block: Fix GenDiskBuilder block size documentation
list: linux-block
message_id: 20260929-rust-block-for-v7-4-rc1-b4-v1-6-642a4c1aebd7@kernel.org
link: https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-6-642a4c1aebd7@kernel.org/
---

# [PATCH GIT PULL 6/9] rust: block: Fix GenDiskBuilder block size documentation

来源：[https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-6-642a4c1aebd7@kernel.org/](https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-6-642a4c1aebd7@kernel.org/)

```
From: Sophon Z <aiqubits@hotmail.com>

GenDiskBuilder::validate_block_size() accepts powers of two from 512
through PAGE_SIZE, but the documentation for logical_block_size() and
physical_block_size() states that the maximum is 4096.

Use PAGE_SIZE for both documented upper bounds so that the documentation
matches validation on architectures with larger page sizes.

Signed-off-by: Sophon Z <aiqubits@hotmail.com>
Acked-by: Andreas Hindborg <a.hindborg@kernel.org>
Link: https://msgid.link/20260831-fix-gendisk-block-size-docs-v1-1-900546005799@hotmail.com
Signed-off-by: Andreas Hindborg <a.hindborg@kernel.org>
---
 rust/kernel/block/mq/gen_disk.rs | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/rust/kernel/block/mq/gen_disk.rs b/rust/kernel/block/mq/gen_disk.rs
index 90d364ab3bf2..0fe640f3aec6 100644
--- a/rust/kernel/block/mq/gen_disk.rs
+++ b/rust/kernel/block/mq/gen_disk.rs
@@ -75,7 +75,7 @@ pub fn validate_block_size(size: u32) -> Result {
     /// Set the logical block size of the device to be built.
     ///
     /// This method will check that block size is a power of two and between 512
-    /// and 4096. If not, an error is returned and the block size is not set.
+    /// and `PAGE_SIZE`. If not, an error is returned and the block size is not set.
     ///
     /// This is the smallest unit the storage device can address. It is
     /// typically 4096 bytes.
@@ -88,7 +88,7 @@ pub fn logical_block_size(mut self, block_size: u32) -> Result<Self> {
     /// Set the physical block size of the device to be built.
     ///
     /// This method will check that block size is a power of two and between 512
-    /// and 4096. If not, an error is returned and the block size is not set.
+    /// and `PAGE_SIZE`. If not, an error is returned and the block size is not set.
     ///
     /// This is the smallest unit a physical storage device can write
     /// atomically. It is usually the same as the logical block size but may be

-- 
2.54.0
```
