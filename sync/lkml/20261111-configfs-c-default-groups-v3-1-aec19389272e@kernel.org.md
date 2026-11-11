---
title: [PATCH v3] configfs: rust: add an API for adding default groups from C
list: linux-block
message_id: 20261111-configfs-c-default-groups-v3-1-aec19389272e@kernel.org
link: https://lore.kernel.org/linux-block/20261111-configfs-c-default-groups-v3-1-aec19389272e@kernel.org/
---

# [PATCH v3] configfs: rust: add an API for adding default groups from C

来源：[https://lore.kernel.org/linux-block/20261111-configfs-c-default-groups-v3-1-aec19389272e@kernel.org/](https://lore.kernel.org/linux-block/20261111-configfs-c-default-groups-v3-1-aec19389272e@kernel.org/)

```
Some C subsystems provide a feature to add configfs default groups to the
configfs hierarchy of other drivers or subsystems. Rust abstractions for
these subsystems will want a way to add these default groups via the
configfs Rust API. So add infrastructure to make this possible.

Signed-off-by: Andreas Hindborg <a.hindborg@kernel.org>
---
Changes in v3:
- Acquire a reference on each default group before adding it to its parent
  group. `configfs_add_default_group` does not acquire one, but
  `configfs_remove_default_groups` releases one, so a default group reached
  a zero reference count when its parent was dropped, while the caller
  still owned it.
- Make `CDefaultGroup` an unsafe trait and document the requirements on
  implementers.
- Add `UnattachedGroup`, a token that grants permission to attach a group
  as a default group exactly once, and take that in `Group::new` instead of
  an `Arc`. A `struct config_group` is linked into its parent through a
  single `group_entry` field, so attaching one group to two parents would
  corrupt both lists. The token cannot be cloned and `Group::new` consumes
  it, so this is now rejected at compile time rather than left to the
  caller.
- Allocate the group in `UnattachedGroup::new`, so that uniqueness follows
  from construction. Obtain a handle to the group with `clone_arc` or
  `into_arc`, named after the `ListArc` accessors.
- Initialize `data` before `group` in `Group::new`, so that no fallible
  step runs after the default groups have been attached.
- Drop default groups from the list of unsupported features in the module
  documentation.
- Link to v2: https://msgid.link/20260605-configfs-c-default-groups-v2-1-2e2e4919e402@kernel.org

Changes in v2:
- Drop the spurious `__` prefix on the symbol name of the
  `configfs_remove_default_groups` Rust helper (Alice).
- Wrap the body of `Group::new` in `pin_init::pin_init_scope` so that
  allocation failure from `KVec::push` is propagated with `?` instead
  of panicking via `unwrap` (Danilo).
- Only build configfs rust helpers when configfs is enabled.
- Link to v1: https://msgid.link/20260215-configfs-c-default-groups-v1-1-e967daef6c36@kernel.org
---
 drivers/block/rnull/configfs.rs |   1 +
 rust/helpers/configfs.c         |  20 +++++
 rust/helpers/helpers.c          |   1 +
 rust/kernel/configfs.rs         | 184 +++++++++++++++++++++++++++++++++++++---
 samples/rust/rust_configfs.rs   |   8 +-
 5 files changed, 200 insertions(+), 14 deletions(-)

diff --git a/drivers/block/rnull/configfs.rs b/drivers/block/rnull/configfs.rs
index 34ef96fa125f0..2f5b722927e0d 100644
--- a/drivers/block/rnull/configfs.rs
+++ b/drivers/block/rnull/configfs.rs
@@ -88,6 +88,7 @@ fn make_group(
                     name: name.try_into()?,
                 }),
             }),
+            core::iter::empty(),
         ))
     }
 }
diff --git a/rust/helpers/configfs.c b/rust/helpers/configfs.c
new file mode 100644
index 0000000000000..4c71c33211bf7
--- /dev/null
+++ b/rust/helpers/configfs.c
@@ -0,0 +1,20 @@
+// SPDX-License-Identifier: GPL-2.0
+
+#include <linux/configfs.h>
+
+#ifdef CONFIG_CONFIGFS_FS
+
+__rust_helper void
+rust_helper_configfs_add_default_group(struct config_group *new_group,
+				       struct config_group *group)
+{
+	configfs_add_default_group(new_group, group);
+}
+
+__rust_helper void
+rust_helper_configfs_remove_default_groups(struct config_group *group)
+{
+	configfs_remove_default_groups(group);
+}
+
+#endif
diff --git a/rust/helpers/helpers.c b/rust/helpers/helpers.c
index d62c7be1ca7bd..ab8d38b431176 100644
--- a/rust/helpers/helpers.c
+++ b/rust/helpers/helpers.c
@@ -51,6 +51,7 @@
 #include "build_bug.c"
 #include "clk.c"
 #include "completion.c"
+#include "configfs.c"
 #include "cpu.c"
 #include "cpufreq.c"
 #include "cpumask.c"
diff --git a/rust/kernel/configfs.rs b/rust/kernel/configfs.rs
index dbed72844b31c..a434fc269ef7c 100644
--- a/rust/kernel/configfs.rs
+++ b/rust/kernel/configfs.rs
@@ -11,7 +11,8 @@
 //! - Items. All group children are groups.
 //! - Symlink support.
 //! - `disconnect_notify` hook.
-//! - Default groups.
+//! - Default groups, except for groups allocated and initialized by C code. See
+//!   [`CDefaultGroup`] and [`UnattachedGroup`].
 //!
 //! See the [`rust_configfs.rs`] sample for a full example use of this module.
 //!
@@ -110,6 +111,7 @@
 //! [`rust_configfs.rs`]: srctree/samples/rust/rust_configfs.rs
 
 use crate::alloc::flags;
+use crate::alloc::Flags;
 use crate::container_of;
 use crate::page::PAGE_SIZE;
 use crate::prelude::*;
@@ -242,12 +244,27 @@ unsafe fn container_of(group: *const bindings::config_group) -> *const Self {
 ///
 /// To add a subgroup to configfs, pass this type as `ctype` to
 /// [`crate::configfs_attrs`] when creating a group in [`GroupOperations::make_group`].
-#[pin_data]
+#[pin_data(PinnedDrop)]
 pub struct Group<Data> {
     #[pin]
     group: Opaque<bindings::config_group>,
     #[pin]
     data: Data,
+    default_groups: KVec<Arc<dyn CDefaultGroup>>,
+}
+
+#[pinned_drop]
+impl<Data> PinnedDrop for Group<Data> {
+    fn drop(self: Pin<&mut Self>) {
+        // SAFETY: We have exclusive access to `self` and we know the default groups are alive
+        // because we reference them through `self.default_groups`.
+        //
+        // `configfs_remove_default_groups` releases one reference on each default group. That is
+        // the reference `Self::new` acquired before adding the group, so the references owned by
+        // the `Arc` values in `self.default_groups` are not affected. Those are released when the
+        // field is dropped, which happens after this function returns.
+        unsafe { bindings::configfs_remove_default_groups(self.group.get()) };
+    }
 }
 
 // SAFETY: We do not provide any operations on `Group`.
@@ -262,26 +279,167 @@ impl<Data> Group<Data> {
     ///
     /// When instantiated, the group will appear as a directory with the name
     /// given by `name` and it will contain attributes specified by `item_type`.
+    ///
+    /// Each element of `default_groups` is added as a default group of the new group and will
+    /// appear as a subdirectory of it.
     pub fn new(
         name: CString,
         item_type: &'static ItemType<Group<Data>, Data>,
         data: impl PinInit<Data, Error>,
+        default_groups: impl IntoIterator<Item = UnattachedGroup<dyn CDefaultGroup>>,
     ) -> impl PinInit<Self, Error> {
-        try_pin_init!(Self {
-            group <- pin_init::init_zeroed().chain(|v: &mut Opaque<bindings::config_group>| {
-                let place = v.get();
-                let name = name.to_bytes_with_nul().as_ptr();
-                // SAFETY: It is safe to initialize a group once it has been zeroed.
-                unsafe {
-                    bindings::config_group_init_type_name(place, name.cast(), item_type.as_ptr())
-                };
-                Ok(())
-            }),
-            data <- data,
+        pin_init::pin_init_scope(move || {
+            // Transition the permission tokens into `Arc`s.
+            let mut dg: KVec<Arc<dyn CDefaultGroup>> = KVec::new();
+            for group in default_groups {
+                dg.push(group.into_arc(), GFP_KERNEL)?;
+            }
+
+            Ok(try_pin_init!(Self {
+                // `data` is initialized first because it is the only fallible step. Nothing may
+                // fail after the default groups below have been added to `group`, because the
+                // references acquired for them are only released by the
+                // `configfs_remove_default_groups` call in `PinnedDrop`, which does not run if
+                // initialization fails.
+                data <- data,
+                group <- pin_init::init_zeroed().chain(|v: &mut Opaque<bindings::config_group>| {
+                    let place = v.get();
+                    let name = name.to_bytes_with_nul().as_ptr();
+                    // SAFETY: It is safe to initialize a group o
```
