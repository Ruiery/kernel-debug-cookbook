---
title: [PATCH RFC 1/3] x86/uaccess: Split the STAC/CLAC out of copy_user_generic()
list: linux-block
message_id: 20261113-pipe-pool-regression-smap-v1-1-b0dc69558ab3@debian.org
link: https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-1-b0dc69558ab3@debian.org/
---

# [PATCH RFC 1/3] x86/uaccess: Split the STAC/CLAC out of copy_user_generic()

来源：[https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-1-b0dc69558ab3@debian.org/](https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-1-b0dc69558ab3@debian.org/)

```
copy_user_generic() brackets every copy with STAC/CLAC. A caller that
copies several kernel buffers to or from one user range pays for a pair
per buffer, even when one user access section could cover them all.

The x86 unsafe_copy_to_user() works inside such a section, but it moves
8 bytes per store, which is the wrong tool for page sized copies. x86
has no unsafe_copy_from_user() yet, and the one posted with the sframe
unwinder [1] is the same loop for reads.

Move the body of copy_user_generic() into unsafe_copy_user_generic(),
which leaves STAC/CLAC to the caller's user access section, and turn
copy_user_generic() into a STAC/CLAC wrapper around it. The existing
callers get the same code.

Link: https://lore.kernel.org/all/20260821195259.2688377-19-jremus@linux.ibm.com/ [1]
Signed-off-by: Breno Leitao <leitao@debian.org>
---
 arch/x86/include/asm/uaccess_64.h | 20 ++++++++++++++++++--
 1 file changed, 18 insertions(+), 2 deletions(-)

diff --git a/arch/x86/include/asm/uaccess_64.h b/arch/x86/include/asm/uaccess_64.h
index 20de34cc9aa6e7..b2bd40d3768d4c 100644
--- a/arch/x86/include/asm/uaccess_64.h
+++ b/arch/x86/include/asm/uaccess_64.h
@@ -115,10 +115,13 @@ static inline bool __access_ok(const void __user *ptr, unsigned long size)
 __must_check unsigned long
 rep_movs_alternative(void *to, const void *from, unsigned len);
 
+/*
+ * copy_user_generic() without the STAC/CLAC, for several copies inside one
+ * user access section. Returns the number of bytes not copied.
+ */
 static __always_inline __must_check unsigned long
-copy_user_generic(void *to, const void *from, unsigned long len)
+unsafe_copy_user_generic(void *to, const void *from, unsigned long len)
 {
-	stac();
 	/*
 	 * If CPU has FSRM feature, use 'rep movs'.
 	 * Otherwise, use rep_movs_alternative.
@@ -131,6 +134,19 @@ copy_user_generic(void *to, const void *from, unsigned long len)
 		_ASM_EXTABLE_UA(1b, 2b)
 		:"+c" (len), "+D" (to), "+S" (from), ASM_CALL_CONSTRAINT
 		: : "memory", "rax");
+	return len;
+}
+
+/*
+ * Hack: lets generic code test for this helper.
+ */
+#define unsafe_copy_user_generic unsafe_copy_user_generic
+
+static __always_inline __must_check unsigned long
+copy_user_generic(void *to, const void *from, unsigned long len)
+{
+	stac();
+	len = unsafe_copy_user_generic(to, from, len);
 	clac();
 	return len;
 }

-- 
2.53.1-Meta
```
