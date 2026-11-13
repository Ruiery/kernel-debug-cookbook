---
title: [PATCH RFC 2/3] iov_iter: add copy_bvecs_to_iter_full()
list: linux-block
message_id: 20261113-pipe-pool-regression-smap-v1-2-b0dc69558ab3@debian.org
link: https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-2-b0dc69558ab3@debian.org/
---

# [PATCH RFC 2/3] iov_iter: add copy_bvecs_to_iter_full()

来源：[https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-2-b0dc69558ab3@debian.org/](https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-2-b0dc69558ab3@debian.org/)

```
copy_page_to_iter() opens and closes a user access section for every
page it copies to a user buffer. On x86 that is a STAC/CLAC pair per
page, even when the caller holds a batch of pages, as anon_pipe_read()
does, that one section could cover.

Add copy_bvecs_to_iter_full(), which copies an array of pages to an
iov_iter like a copy_page_to_iter() loop, but all or nothing: after a
short copy the iterator is reverted, as copy_from_iter_full() does.

For a plain user buffer (ITER_UBUF) on architectures that provide
unsafe_copy_user_generic(), all the copies run inside one scoped user
write access. It keeps the usercopy fault injection and the
instrumentation that copy_to_user_iter() does for every copy. Every
other destination gets the copy_page_to_iter() loop.

Signed-off-by: Breno Leitao <leitao@debian.org>
---
 include/linux/uio.h |  2 ++
 lib/iov_iter.c      | 61 +++++++++++++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 63 insertions(+)

diff --git a/include/linux/uio.h b/include/linux/uio.h
index 76e4103b9ec423..7ab25080b0edea 100644
--- a/include/linux/uio.h
+++ b/include/linux/uio.h
@@ -197,6 +197,8 @@ size_t fault_in_iov_iter_writeable(const struct iov_iter *i, size_t bytes);
 size_t iov_iter_single_seg_count(const struct iov_iter *i);
 size_t copy_page_to_iter(struct page *page, size_t offset, size_t bytes,
 			 struct iov_iter *i);
+bool copy_bvecs_to_iter_full(const struct bio_vec *bv, unsigned int nr,
+			     struct iov_iter *i);
 size_t copy_page_from_iter(struct page *page, size_t offset, size_t bytes,
 			 struct iov_iter *i);
 size_t copy_folio_from_iter_atomic(struct folio *folio, size_t offset,
diff --git a/lib/iov_iter.c b/lib/iov_iter.c
index de7a48205e0117..2df0539228be84 100644
--- a/lib/iov_iter.c
+++ b/lib/iov_iter.c
@@ -387,6 +387,67 @@ size_t copy_page_to_iter(struct page *page, size_t offset, size_t bytes,
 }
 EXPORT_SYMBOL(copy_page_to_iter);
 
+#ifdef unsafe_copy_user_generic
+static bool copy_bvecs_to_ubuf_full(const struct bio_vec *bv, unsigned int nr,
+				    struct iov_iter *i)
+{
+	char __user *dst = i->ubuf + i->iov_offset;
+	size_t len = 0, off = 0;
+	unsigned int k;
+
+	for (k = 0; k < nr; k++)
+		len += bv[k].bv_len;
+	if (len > iov_iter_count(i) || should_fail_usercopy())
+		return false;
+
+	might_fault();
+	scoped_user_write_access_size(dst, len, efault) {
+		for (k = 0; k < nr; off += bv[k].bv_len, k++) {
+			void *src = page_address(bv[k].bv_page) +
+				    bv[k].bv_offset;
+
+			instrument_copy_to_user(dst + off, src, bv[k].bv_len);
+			if (unsafe_copy_user_generic((__force void *)dst + off,
+						     src, bv[k].bv_len))
+				goto efault;
+		}
+	}
+	iov_iter_advance(i, len);
+	return true;
+
+efault:
+	return false;
+}
+#endif
+
+/*
+ * Copy the pages in @bv to @i one after the other, like copy_page_to_iter(),
+ * but all or nothing: after a short copy @i is reverted. For a plain user
+ * buffer the copies share one user access section where the architecture
+ * allows it.
+ */
+bool copy_bvecs_to_iter_full(const struct bio_vec *bv, unsigned int nr,
+			     struct iov_iter *i)
+{
+	size_t copied = 0, n;
+	unsigned int k;
+
+#ifdef unsafe_copy_user_generic
+	if (iter_is_ubuf(i))
+		return copy_bvecs_to_ubuf_full(bv, nr, i);
+#endif
+	for (k = 0; k < nr; k++) {
+		n = copy_page_to_iter(bv[k].bv_page, bv[k].bv_offset,
+				      bv[k].bv_len, i);
+		copied += n;
+		if (n != bv[k].bv_len) {
+			iov_iter_revert(i, copied);
+			return false;
+		}
+	}
+	return true;
+}
+
 size_t copy_page_to_iter_nofault(struct page *page, unsigned offset, size_t bytes,
 				 struct iov_iter *i)
 {

-- 
2.53.1-Meta
```
