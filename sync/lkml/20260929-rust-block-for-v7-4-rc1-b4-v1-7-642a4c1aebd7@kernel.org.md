---
title: [PATCH GIT PULL 7/9] rnull: fix geometry store check-then-act across lock scopes
list: linux-block
message_id: 20260929-rust-block-for-v7-4-rc1-b4-v1-7-642a4c1aebd7@kernel.org
link: https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-7-642a4c1aebd7@kernel.org/
---

# [PATCH GIT PULL 7/9] rnull: fix geometry store check-then-act across lock scopes

来源：[https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-7-642a4c1aebd7@kernel.org/](https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-7-642a4c1aebd7@kernel.org/)

```
From: Qingxiao Xu <qingxiao@tamu.edu>

The blocksize/rotational/capacity/irqmode stores check powered under one
Mutex acquisition, drop the guard, then update under a second acquisition.
A concurrent power-on can create the live disk from stale geometry in
between, leaving powered==true with config != live disk.

Hold one guard for the powered check and the field update.

Signed-off-by: Qingxiao Xu <qingxiao@tamu.edu>
Link: https://msgid.link/20260908200845.405112-1-qingxiao@tamu.edu
Signed-off-by: Andreas Hindborg <a.hindborg@kernel.org>
---
 drivers/block/rnull/configfs.rs | 20 ++++++++++++--------
 1 file changed, 12 insertions(+), 8 deletions(-)

diff --git a/drivers/block/rnull/configfs.rs b/drivers/block/rnull/configfs.rs
index 9b28be215093..24b02256b4cd 100644
--- a/drivers/block/rnull/configfs.rs
+++ b/drivers/block/rnull/configfs.rs
@@ -186,7 +186,8 @@ impl configfs::AttributeOperations<1> for DeviceConfig {
     }
 
     fn store(this: &DeviceConfig, page: &[u8]) -> Result {
-        if this.data.lock().powered {
+        let mut guard = this.data.lock();
+        if guard.powered {
             return Err(EBUSY);
         }
 
@@ -194,7 +195,7 @@ fn store(this: &DeviceConfig, page: &[u8]) -> Result {
         let value = text.parse::<u32>().map_err(|_| EINVAL)?;
 
         GenDiskBuilder::validate_block_size(value)?;
-        this.data.lock().block_size = value;
+        guard.block_size = value;
         Ok(())
     }
 }
@@ -216,11 +217,12 @@ impl configfs::AttributeOperations<2> for DeviceConfig {
     }
 
     fn store(this: &DeviceConfig, page: &[u8]) -> Result {
-        if this.data.lock().powered {
+        let mut guard = this.data.lock();
+        if guard.powered {
             return Err(EBUSY);
         }
 
-        this.data.lock().rotational = kstrtobool_bytes(page)?;
+        guard.rotational = kstrtobool_bytes(page)?;
 
         Ok(())
     }
@@ -237,14 +239,15 @@ impl configfs::AttributeOperations<3> for DeviceConfig {
     }
 
     fn store(this: &DeviceConfig, page: &[u8]) -> Result {
-        if this.data.lock().powered {
+        let mut guard = this.data.lock();
+        if guard.powered {
             return Err(EBUSY);
         }
 
         let text = core::str::from_utf8(page)?.trim();
         let value = text.parse::<u64>().map_err(|_| EINVAL)?;
 
-        this.data.lock().capacity_mib = value;
+        guard.capacity_mib = value;
         Ok(())
     }
 }
@@ -260,14 +263,15 @@ impl configfs::AttributeOperations<4> for DeviceConfig {
     }
 
     fn store(this: &DeviceConfig, page: &[u8]) -> Result {
-        if this.data.lock().powered {
+        let mut guard = this.data.lock();
+        if guard.powered {
             return Err(EBUSY);
         }
 
         let text = core::str::from_utf8(page)?.trim();
         let value = text.parse::<u8>().map_err(|_| EINVAL)?;
 
-        this.data.lock().irq_mode = IRQMode::try_from(value)?;
+        guard.irq_mode = IRQMode::try_from(value)?;
         Ok(())
     }
 }

-- 
2.54.0
```
