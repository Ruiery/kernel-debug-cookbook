---
title: [PATCH GIT PULL 8/9] rnull: configfs: add power to configfs features
list: linux-block
message_id: 20260929-rust-block-for-v7-4-rc1-b4-v1-8-642a4c1aebd7@kernel.org
link: https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-8-642a4c1aebd7@kernel.org/
---

# [PATCH GIT PULL 8/9] rnull: configfs: add power to configfs features

来源：[https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-8-642a4c1aebd7@kernel.org/](https://lore.kernel.org/linux-block/20260929-rust-block-for-v7-4-rc1-b4-v1-8-642a4c1aebd7@kernel.org/)

```
From: Malte Wechter <maltewechter@gmail.com>

features displayed by configfs for rnull was inconsistent with the
actual features available. This correctly exposes `power` as a feature,
which is also consistent with the C null_blk driver.

Fixes: d969d504bc13 ("rnull: enable configuration via `configfs`")

Signed-off-by: Malte Wechter <maltewechter@gmail.com>
Link: https://msgid.link/20260924-upstream-v7-3-rc3-v2-1-ca56ae7a73e9@gmail.com
Signed-off-by: Andreas Hindborg <a.hindborg@kernel.org>
---
 drivers/block/rnull/configfs.rs | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/drivers/block/rnull/configfs.rs b/drivers/block/rnull/configfs.rs
index 24b02256b4cd..34ef96fa125f 100644
--- a/drivers/block/rnull/configfs.rs
+++ b/drivers/block/rnull/configfs.rs
@@ -47,7 +47,7 @@ impl AttributeOperations<0> for Config {
 
     fn show(_this: &Config, page: &mut [u8; PAGE_SIZE]) -> Result<usize> {
         let mut writer = kernel::str::Formatter::new(page);
-        writer.write_str("blocksize,size,rotational,irqmode\n")?;
+        writer.write_str("blocksize,size,rotational,irqmode,power\n")?;
         Ok(writer.bytes_written())
     }
 }

-- 
2.54.0
```
