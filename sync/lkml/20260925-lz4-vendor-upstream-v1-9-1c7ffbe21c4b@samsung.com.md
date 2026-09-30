---
title: [PATCH RFC 9/9] MAINTAINERS: add an entry for the LZ4 compression library
list: linux-block
message_id: 20260925-lz4-vendor-upstream-v1-9-1c7ffbe21c4b@samsung.com
link: https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-9-1c7ffbe21c4b@samsung.com/
---

# [PATCH RFC 9/9] MAINTAINERS: add an entry for the LZ4 compression library

来源：[https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-9-1c7ffbe21c4b@samsung.com/](https://lore.kernel.org/linux-block/20260925-lz4-vendor-upstream-v1-9-1c7ffbe21c4b@samsung.com/)

```
lib/lz4/ has never had one: get_maintainer.pl returns only the LKML
fallback for every file in it, including include/linux/lz4.h, which eight
subsystems build against.

This matters more now than it did. With the previous patches lib/lz4 is
vendored upstream sources, and someone has to bump them to new upstream
releases and decide what the kernel-side glue may do. I am willing to do
that, so add myself as its maintainer.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 MAINTAINERS | 6 ++++++
 1 file changed, 6 insertions(+)

diff --git a/MAINTAINERS b/MAINTAINERS
index cc3cae2e378b34aeb705cef654c720ca9f2ba223..989e1b5fab21432dd7042d1e60c4bbad85beb925 100644
--- a/MAINTAINERS
+++ b/MAINTAINERS
@@ -15606,6 +15606,12 @@ S:	Supported
 F:	drivers/net/pcs/pcs-lynx.c
 F:	include/linux/pcs-lynx.h
 
+LZ4 COMPRESSION LIBRARY
+M:	Michal Wilczynski <m.wilczynski@samsung.com>
+S:	Maintained
+F:	include/linux/lz4.h
+F:	lib/lz4/
+
 M68K ARCHITECTURE
 M:	Geert Uytterhoeven <geert@linux-m68k.org>
 L:	linux-m68k@lists.linux-m68k.org

-- 
2.34.1
```
