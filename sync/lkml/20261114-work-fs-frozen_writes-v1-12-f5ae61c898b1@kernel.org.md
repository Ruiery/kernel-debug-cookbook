---
title: [PATCH 12/12] nfsd: take freeze protection for the truncate on open
list: linux-block
message_id: 20261114-work-fs-frozen_writes-v1-12-f5ae61c898b1@kernel.org
link: https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-12-f5ae61c898b1@kernel.org/
---

# [PATCH 12/12] nfsd: take freeze protection for the truncate on open

来源：[https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-12-f5ae61c898b1@kernel.org/](https://lore.kernel.org/linux-block/20261114-work-fs-frozen_writes-v1-12-f5ae61c898b1@kernel.org/)

```
An OPEN that truncates an existing file ends up in nfsd4_truncate()
which calls nfsd_setattr() on the already verified file handle. For a
verified file handle nfsd_setattr() leaves fh_want_write() to the
caller but nfsd4_truncate() never takes it, and do_lookup_open() has
dropped its own write access by then. So a freeze of the exported
filesystem that lands in between lets the truncate modify a frozen
filesystem.

Take write access around nfsd_setattr() like nfsd4_setattr() does.

Fixes: 9f67f189939e ("nfsd: notify_change needs elevated write count")
Cc: stable@vger.kernel.org
Signed-off-by: Christian Brauner (Amutable) <brauner@kernel.org>
---
 fs/nfsd/nfs4state.c | 10 +++++++++-
 1 file changed, 9 insertions(+), 1 deletion(-)

diff --git a/fs/nfsd/nfs4state.c b/fs/nfsd/nfs4state.c
index 1de6c6d757c3e..e561903b9180f 100644
--- a/fs/nfsd/nfs4state.c
+++ b/fs/nfsd/nfs4state.c
@@ -6681,11 +6681,19 @@ nfsd4_truncate(struct svc_rqst *rqstp, struct svc_fh *fh,
 	struct nfsd_attrs attrs = {
 		.na_iattr	= &iattr,
 	};
+	__be32 status;
+	int err;
+
 	if (!open->op_truncate)
 		return 0;
 	if (!(open->op_share_access & NFS4_SHARE_ACCESS_WRITE))
 		return nfserr_inval;
-	return nfsd_setattr(rqstp, fh, &attrs, NULL);
+	err = fh_want_write(fh);
+	if (err)
+		return nfserrno(err);
+	status = nfsd_setattr(rqstp, fh, &attrs, NULL);
+	fh_drop_write(fh);
+	return status;
 }
 
 static __be32 nfs4_get_vfs_file(struct svc_rqst *rqstp, struct nfs4_file *fp,

-- 
2.53.0
```
