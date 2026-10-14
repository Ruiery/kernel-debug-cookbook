---
title: [PATCH 3/5] nvme-fabrics: reset io_queues before computing the queue mapping
list: linux-block
message_id: 20261014-nvme-fabrics-isolcpu-v1-3-355156be27b2@kernel.org
link: https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-3-355156be27b2@kernel.org/
---

# [PATCH 3/5] nvme-fabrics: reset io_queues before computing the queue mapping

来源：[https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-3-355156be27b2@kernel.org/](https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-3-355156be27b2@kernel.org/)

```
From: Daniel Wagner <wagi@kernel.org>

nvmf_set_io_queues only sets the io_queues entries of the queue types it
hands out, but the array is reused on every reconnect.  When the
controller grants fewer queues on a reconnect, stale entries survive and
nvmf_map_queues maps CPUs to hardware contexts that don't exist anymore,
which crashes blk_mq_map_swqueue with a NULL pointer dereference.  E.g.
with nr_io_queues=8, nr_write_queues=8 and nr_poll_queues=8, 24 queues
are mapped 8/8/8 (default/read/poll).  If the controller grants only 16
queues on the reconnect, the poll map still starts at hardware context
16.

Clear the array before computing the new mapping.

Fixes: 6486199378a5 ("nvme-tcp: fix queue mapping when queue count is limited")
Fixes: 5651cd3c4336 ("nvme-rdma: fix queue mapping when queue count is limited")
Signed-off-by: Daniel Wagner <wagi@kernel.org>
---
 drivers/nvme/host/fabrics.c | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/drivers/nvme/host/fabrics.c b/drivers/nvme/host/fabrics.c
index 59f823dfbbcc..571de549fbaf 100644
--- a/drivers/nvme/host/fabrics.c
+++ b/drivers/nvme/host/fabrics.c
@@ -1125,6 +1125,8 @@ static int nvmf_parse_options(struct nvmf_ctrl_options *opts,
 void nvmf_set_io_queues(struct nvmf_ctrl_options *opts, u32 nr_io_queues,
 			u32 io_queues[HCTX_MAX_TYPES])
 {
+	memset(io_queues, 0, sizeof(*io_queues) * HCTX_MAX_TYPES);
+
 	if (opts->nr_write_queues && opts->nr_io_queues < nr_io_queues) {
 		/*
 		 * separate read/write queues

-- 
2.56.0
```
