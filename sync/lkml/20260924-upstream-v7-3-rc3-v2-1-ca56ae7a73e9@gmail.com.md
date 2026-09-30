---
title: [PATCH v2] rnull: configfs: add power to configfs features
list: linux-block
message_id: 20260924-upstream-v7-3-rc3-v2-1-ca56ae7a73e9@gmail.com
link: https://lore.kernel.org/linux-block/20260924-upstream-v7-3-rc3-v2-1-ca56ae7a73e9@gmail.com/
---

# [PATCH v2] rnull: configfs: add power to configfs features

来源：[https://lore.kernel.org/linux-block/20260924-upstream-v7-3-rc3-v2-1-ca56ae7a73e9@gmail.com/](https://lore.kernel.org/linux-block/20260924-upstream-v7-3-rc3-v2-1-ca56ae7a73e9@gmail.com/)

```
features displayed by configfs for rnull was inconsistent with the
actual features available. This correctly exposes `power` as a feature,
which is also consistent with the C null_blk driver.

Fixes: d969d504bc13 ("rnull: enable configuration via `configfs`")

Signed-off-by: Malte Wechter <maltewechter@gmail.com>
---
Changes in v2:
- Add fixes tag
- Link to v1: https://patch.msgid.link/20260917-upstream-v7-3-rc3-v1-1-d0b620bf82c9@gmail.com

To: Andreas Hindborg <a.hindborg@kernel.org>
To: Boqun Feng <boqun@kernel.org>
To: Jens Axboe <axboe@kernel.dk>
To: Alice Ryhl <aliceryhl@google.com>
To: Daniel Almeida <daniel.almeida@collabora.com>
Cc: linux-block@vger.kernel.org
Cc: rust-for-linux@vger.kernel.org
Cc: linux-kernel@vger.kernel.org
---
 drivers/block/rnull/configfs.rs | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/drivers/block/rnull/configfs.rs b/drivers/block/rnull/configfs.rs
index 32c10c3f4d0fd7..5f1cdd54cf48aa 100644
--- a/drivers/block/rnull/configfs.rs
+++ b/drivers/block/rnull/configfs.rs
@@ -35,7 +35,7 @@ impl AttributeOperations<0> for Config {
 
     fn show(_this: &Config, page: &mut [u8; PAGE_SIZE]) -> Result<usize> {
         let mut writer = kernel::str::Formatter::new(page);
-        writer.write_str("blocksize,size,rotational,irqmode\n")?;
+        writer.write_str("blocksize,size,rotational,irqmode,power\n")?;
         Ok(writer.bytes_written())
     }
 }

---
base-commit: fd73f4a6659897191fa0d40695fe370925dd3780
change-id: 20260917-upstream-v7-3-rc3-0db5699dab30

Best regards,
--  
Malte Wechter <maltewechter@gmail.com>
```
