---
title: [PATCH v2 15/15] MAINTAINERS: add an entry for the LZ4 compression library
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-15-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-15-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 15/15] MAINTAINERS: add an entry for the LZ4 compression library

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-15-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-15-ee04c3f0d7dc@samsung.com/)

```
lib/lz4/ has never had one: get_maintainer.pl returns only the LKML
fallback for every file in it, including include/linux/lz4.h, which eight
subsystems build against.

The entry also takes lib/decompress_unlz4.c and its header, which
decode LZ4 kernel images and initramfs through lib/lz4, the way XZ
EMBEDDED covers its own equivalents, and crypto/lz4.c and crypto/lz4hc.c,
the crypto API wrappers zswap uses, as ZSTD takes crypto/zstd.c.

This matters more now than it did. With the previous patches lib/lz4 is
vendored upstream sources, and someone has to bump them to new upstream
releases and decide what the kernel-side glue may do. I am willing to do
that, so add myself as its maintainer.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 MAINTAINERS | 10 ++++++++++
 1 file changed, 10 insertions(+)

diff --git a/MAINTAINERS b/MAINTAINERS
index cc3cae2e378b34aeb705cef654c720ca9f2ba223..598d87ca772eecbb1ed169d51ff0eb8cdd2e50ad 100644
--- a/MAINTAINERS
+++ b/MAINTAINERS
@@ -15606,6 +15606,16 @@ S:	Supported
 F:	drivers/net/pcs/pcs-lynx.c
 F:	include/linux/pcs-lynx.h
 
+LZ4 COMPRESSION LIBRARY
+M:	Michal Wilczynski <m.wilczynski@samsung.com>
+S:	Maintained
+F:	crypto/lz4.c
+F:	crypto/lz4hc.c
+F:	include/linux/decompress/unlz4.h
+F:	include/linux/lz4.h
+F:	lib/decompress_unlz4.c
+F:	lib/lz4/
+
 M68K ARCHITECTURE
 M:	Geert Uytterhoeven <geert@linux-m68k.org>
 L:	linux-m68k@lists.linux-m68k.org

-- 
2.34.1
```
