---
title: [PATCH GIT PULL 3/9] rust: block: rnull: use vertical import style
list: linux-block
message_id: 20260929-rust-block-for-v7-4-rc1-b4-v1-3-642a4c1aebd7@kernel.org
link: https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-3-642a4c1aebd7@kernel.org/
---

# [PATCH GIT PULL 3/9] rust: block: rnull: use vertical import style

来源：[https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-3-642a4c1aebd7@kernel.org/](https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-3-642a4c1aebd7@kernel.org/)

```
From: Alvin Sun <alvin.sun@linux.dev>

Convert `use` imports to vertical layout for better readability and
maintainability.

Signed-off-by: Alvin Sun <alvin.sun@linux.dev>
Link: https://msgid.link/20260521-miscdev-use-format-v3-6-56240ca70d0c@linux.dev
Signed-off-by: Andreas Hindborg <a.hindborg@kernel.org>
---
 drivers/block/rnull/configfs.rs | 22 +++++++++++++++++-----
 drivers/block/rnull/rnull.rs    | 15 +++++++++++----
 2 files changed, 28 insertions(+), 9 deletions(-)

diff --git a/drivers/block/rnull/configfs.rs b/drivers/block/rnull/configfs.rs
index 32c10c3f4d0f..9b28be215093 100644
--- a/drivers/block/rnull/configfs.rs
+++ b/drivers/block/rnull/configfs.rs
@@ -2,15 +2,27 @@
 
 use super::NullBlkDevice;
 use kernel::{
-    block::mq::gen_disk::{GenDisk, GenDiskBuilder},
-    configfs::{self, AttributeOperations},
+    block::mq::gen_disk::{
+        GenDisk,
+        GenDiskBuilder, //
+    },
+    configfs::{
+        self,
+        AttributeOperations, //
+    },
     configfs_attrs,
-    fmt::{self, Write as _},
+    fmt::{
+        self,
+        Write as _, //
+    },
     new_mutex,
     page::PAGE_SIZE,
     prelude::*,
-    str::{kstrtobool_bytes, CString},
-    sync::Mutex,
+    str::{
+        kstrtobool_bytes,
+        CString, //
+    },
+    sync::Mutex, //
 };
 
 pub(crate) fn subsystem() -> impl PinInit<kernel::configfs::Subsystem<Config>, Error> {
diff --git a/drivers/block/rnull/rnull.rs b/drivers/block/rnull/rnull.rs
index 0ca8715febe8..13048cea8bb0 100644
--- a/drivers/block/rnull/rnull.rs
+++ b/drivers/block/rnull/rnull.rs
@@ -10,12 +10,19 @@
         self,
         mq::{
             self,
-            gen_disk::{self, GenDisk},
-            Operations, TagSet,
-        },
+            gen_disk::{
+                self,
+                GenDisk, //
+            },
+            Operations,
+            TagSet, //
+        }, //
     },
     prelude::*,
-    sync::{aref::ARef, Arc},
+    sync::{
+        aref::ARef,
+        Arc, //
+    }, //
 };
 
 module! {

-- 
2.54.0
```
