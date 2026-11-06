---
title: [PATCH v2 07/15] lib/lz4: backport upstream's match length limit fix
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-7-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-7-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 07/15] lib/lz4: backport upstream's match length limit fix

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-7-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-7-ee04c3f0d7dc@samsung.com/)

```
v1.10.0 lets a match length's extension bytes run to four bytes before
the end of the block, which leaves room for only a token and three
literals where the format requires five. The fork rejected such blocks,
v1.10.0 decodes them: 1f 41 01 00 ff 00 30 7a 7a 7a decodes to 278
bytes instead of failing.

Upstream fixed this in 587ed9557708 ("add comments explaining
read_variable_length() ilimit bounds, fix match length limit"), on top
of a read_variable_length() rework v1.10.0 does not have. Both versions
accept the same final ip for a given limit, so change the limit at the
two match length call sites to iend - (1 + LASTLITERALS), as upstream
does. This is one byte stricter than the fork; no compressor produces
the blocks it newly rejects.

This goes away at the next re-sync.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 lib/lz4/upstream/lz4.c | 4 ++--
 1 file changed, 2 insertions(+), 2 deletions(-)

diff --git a/lib/lz4/upstream/lz4.c b/lib/lz4/upstream/lz4.c
index ee69d57aae112f4057c050bbdab4cc0f2d30f9d9..a45f3828141eec9baea59a5e97a3ff37d6474d6e 100644
--- a/lib/lz4/upstream/lz4.c
+++ b/lib/lz4/upstream/lz4.c
@@ -2120,7 +2120,7 @@ LZ4_decompress_generic(
             DEBUGLOG(7, "  match length token = %u (len==%u)", (unsigned)length, (unsigned)length+MINMATCH);
 
             if (length == ML_MASK) {
-                size_t const addl = read_variable_length(&ip, iend - LASTLITERALS + 1, 0);
+                size_t const addl = read_variable_length(&ip, iend - (1 + LASTLITERALS), 0);
                 if (addl == rvl_error) {
                     DEBUGLOG(5, "error reading long match length");
                     goto _output_error;
@@ -2338,7 +2338,7 @@ LZ4_decompress_generic(
 
     _copy_match:
             if (length == ML_MASK) {
-                size_t const addl = read_variable_length(&ip, iend - LASTLITERALS + 1, 0);
+                size_t const addl = read_variable_length(&ip, iend - (1 + LASTLITERALS), 0);
                 if (addl == rvl_error) { goto _output_error; }
                 length += addl;
                 if (unlikely((uptrval)(op)+length<(uptrval)op)) goto _output_error;   /* overflow detection */

-- 
2.34.1
```
