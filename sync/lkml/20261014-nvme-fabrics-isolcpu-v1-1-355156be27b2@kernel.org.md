---
title: [PATCH 1/5] nvme-tcp: initialize pf_cache_lock when allocating the controller
list: linux-block
message_id: 20261014-nvme-fabrics-isolcpu-v1-1-355156be27b2@kernel.org
link: https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-1-355156be27b2@kernel.org/
---

# [PATCH 1/5] nvme-tcp: initialize pf_cache_lock when allocating the controller

来源：[https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-1-355156be27b2@kernel.org/](https://lore.kernel.org/linux-block/20261014-nvme-fabrics-isolcpu-v1-1-355156be27b2@kernel.org/)

```
From: Daniel Wagner <wagi@kernel.org>

Since commit 61b0ed3be81b ("nvme-tcp: parallelize I/O queue allocation
and startup") the I/O tag set is allocated before the I/O queues.
blk_mq_alloc_tag_set calls nvme_tcp_init_request for every request,
which takes pf_cache_lock of the request's queue, but nvme_tcp_alloc_queue
initializes that mutex only later.  With CONFIG_DEBUG_MUTEXES the first
connect triggers DEBUG_LOCKS_WARN_ON(lock->magic != lock) in
__mutex_lock and lock debugging is disabled.

Initialize pf_cache_lock for all queues when allocating the controller
and keep it for the lifetime of the controller.

Fixes: 61b0ed3be81b ("nvme-tcp: parallelize I/O queue allocation and startup")
Signed-off-by: Daniel Wagner <wagi@kernel.org>
---
 drivers/nvme/host/tcp.c | 13 +++++++++----
 1 file changed, 9 insertions(+), 4 deletions(-)

diff --git a/drivers/nvme/host/tcp.c b/drivers/nvme/host/tcp.c
index ec678ed07af8..f876375dffd2 100644
--- a/drivers/nvme/host/tcp.c
+++ b/drivers/nvme/host/tcp.c
@@ -1531,7 +1531,6 @@ static void nvme_tcp_free_queue(struct nvme_ctrl *nctrl, int qid)
 	kfree(queue->pdu);
 	mutex_destroy(&queue->send_mutex);
 	mutex_destroy(&queue->queue_lock);
-	mutex_destroy(&queue->pf_cache_lock);
 
 #ifdef CONFIG_DEBUG_LOCK_ALLOC
 	lockdep_unregister_key(&queue->nvme_tcp_sk_key);
@@ -1861,7 +1860,6 @@ static int nvme_tcp_alloc_queue(struct nvme_ctrl *nctrl, int qid,
 	INIT_LIST_HEAD(&queue->send_list);
 	mutex_init(&queue->send_mutex);
 	INIT_WORK(&queue->io_work, nvme_tcp_io_work);
-	mutex_init(&queue->pf_cache_lock);
 
 	if (qid > 0)
 		queue->cmnd_capsule_len = nctrl->ioccsz * 16;
@@ -2002,7 +2000,6 @@ static int nvme_tcp_alloc_queue(struct nvme_ctrl *nctrl, int qid,
 err_destroy_mutex:
 	mutex_destroy(&queue->send_mutex);
 	mutex_destroy(&queue->queue_lock);
-	mutex_destroy(&queue->pf_cache_lock);
 	return ret;
 }
 
@@ -3028,7 +3025,7 @@ static struct nvme_tcp_ctrl *nvme_tcp_alloc_ctrl(struct device *dev,
 		struct nvmf_ctrl_options *opts)
 {
 	struct nvme_tcp_ctrl *ctrl;
-	int ret;
+	int ret, i;
 
 	ctrl = kzalloc_obj(*ctrl);
 	if (!ctrl)
@@ -3098,6 +3095,14 @@ static struct nvme_tcp_ctrl *nvme_tcp_alloc_ctrl(struct device *dev,
 		goto out_free_ctrl;
 	}
 
+	/*
+	 * The I/O tag set is allocated before the I/O queues, and initializing
+	 * its requests already allocates the PDUs from the page frag caches of
+	 * the queues, so initialize their locks here.
+	 */
+	for (i = 0; i < ctrl->ctrl.queue_count; i++)
+		mutex_init(&ctrl->queues[i].pf_cache_lock);
+
 	ctrl->net = get_net(current->nsproxy->net_ns);
 
 	ret = nvme_init_ctrl(&ctrl->ctrl, dev, &nvme_tcp_ctrl_ops, 0);

-- 
2.56.0
```
