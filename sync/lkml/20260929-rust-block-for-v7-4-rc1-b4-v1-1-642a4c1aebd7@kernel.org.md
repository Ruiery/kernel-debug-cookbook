---
title: [PATCH GIT PULL 1/9] rust: block: mq: use vertical import style
list: linux-block
message_id: 20260929-rust-block-for-v7-4-rc1-b4-v1-1-642a4c1aebd7@kernel.org
link: https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-1-642a4c1aebd7@kernel.org/
---

# [PATCH GIT PULL 1/9] rust: block: mq: use vertical import style

来源：[https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-1-642a4c1aebd7@kernel.org/](https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-1-642a4c1aebd7@kernel.org/)

```
From: Alvin Sun <alvin.sun@linux.dev>

Convert `use` imports to vertical layout for better readability and
maintainability.

Reviewed-by: Onur Özkan <work@onurozkan.dev>
Signed-off-by: Alvin Sun <alvin.sun@linux.dev>
Link: https://msgid.link/20260521-miscdev-use-format-v3-4-56240ca70d0c@linux.dev
Signed-off-by: Andreas Hindborg <a.hindborg@kernel.org>
---
 rust/kernel/block/mq/gen_disk.rs   | 21 +++++++++++++++++----
 rust/kernel/block/mq/operations.rs | 17 +++++++++++++----
 rust/kernel/block/mq/request.rs    | 14 ++++++++++----
 rust/kernel/block/mq/tag_set.rs    | 24 +++++++++++++++++++-----
 4 files changed, 59 insertions(+), 17 deletions(-)

diff --git a/rust/kernel/block/mq/gen_disk.rs b/rust/kernel/block/mq/gen_disk.rs
index fc97dd873974..31cc7a77c2b5 100644
--- a/rust/kernel/block/mq/gen_disk.rs
+++ b/rust/kernel/block/mq/gen_disk.rs
@@ -7,14 +7,27 @@
 
 use crate::{
     bindings,
-    block::mq::{Operations, TagSet},
-    error::{self, from_err_ptr, Result},
-    fmt::{self, Write},
+    block::mq::{
+        Operations,
+        TagSet, //
+    },
+    error::{
+        self,
+        from_err_ptr,
+        Result, //
+    },
+    fmt::{
+        self,
+        Write, //
+    },
     prelude::*,
     static_lock_class,
     str::NullTerminatedFormatter,
     sync::Arc,
-    types::{ForeignOwnable, ScopeGuard},
+    types::{
+        ForeignOwnable,
+        ScopeGuard, //
+    }, //
 };
 
 /// A builder for [`GenDisk`].
diff --git a/rust/kernel/block/mq/operations.rs b/rust/kernel/block/mq/operations.rs
index 861903e18fbf..64bcb31666c0 100644
--- a/rust/kernel/block/mq/operations.rs
+++ b/rust/kernel/block/mq/operations.rs
@@ -6,11 +6,20 @@
 
 use crate::{
     bindings,
-    block::mq::{request::RequestDataWrapper, Request},
-    error::{from_result, Result},
+    block::mq::{
+        request::RequestDataWrapper,
+        Request, //
+    },
+    error::{
+        from_result,
+        Result, //
+    },
     prelude::*,
-    sync::{aref::ARef, Refcount},
-    types::ForeignOwnable,
+    sync::{
+        aref::ARef,
+        Refcount, //
+    },
+    types::ForeignOwnable, //
 };
 use core::marker::PhantomData;
 
diff --git a/rust/kernel/block/mq/request.rs b/rust/kernel/block/mq/request.rs
index ce3e30c81cb5..66254d02bba6 100644
--- a/rust/kernel/block/mq/request.rs
+++ b/rust/kernel/block/mq/request.rs
@@ -9,13 +9,19 @@
     block::mq::Operations,
     error::Result,
     sync::{
-        aref::{ARef, AlwaysRefCounted},
+        aref::{
+            ARef,
+            AlwaysRefCounted, //
+        },
         atomic::Relaxed,
-        Refcount,
+        Refcount, //
     },
-    types::Opaque,
+    types::Opaque, //
+};
+use core::{
+    marker::PhantomData,
+    ptr::NonNull, //
 };
-use core::{marker::PhantomData, ptr::NonNull};
 
 /// A wrapper around a blk-mq [`struct request`]. This represents an IO request.
 ///
diff --git a/rust/kernel/block/mq/tag_set.rs b/rust/kernel/block/mq/tag_set.rs
index dae9df408a86..c1fd3e047af5 100644
--- a/rust/kernel/block/mq/tag_set.rs
+++ b/rust/kernel/block/mq/tag_set.rs
@@ -8,13 +8,27 @@
 
 use crate::{
     bindings,
-    block::mq::{operations::OperationsVTable, request::RequestDataWrapper, Operations},
-    error::{self, Result},
+    block::mq::{
+        operations::OperationsVTable,
+        request::RequestDataWrapper,
+        Operations, //
+    },
+    error::{
+        self,
+        Result, //
+    },
     prelude::try_pin_init,
-    types::Opaque,
+    types::Opaque, //
+};
+use core::{
+    convert::TryInto,
+    marker::PhantomData, //
+};
+use pin_init::{
+    pin_data,
+    pinned_drop,
+    PinInit, //
 };
-use core::{convert::TryInto, marker::PhantomData};
-use pin_init::{pin_data, pinned_drop, PinInit};
 
 /// A wrapper for the C `struct blk_mq_tag_set`.
 ///

-- 
2.54.0
```
