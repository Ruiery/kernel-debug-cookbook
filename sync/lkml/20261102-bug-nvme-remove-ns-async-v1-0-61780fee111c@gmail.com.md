---
title: [PATCH 0/2] nvme: delete controllers with many namespaces faster
list: linux-block
message_id: 20261102-bug-nvme-remove-ns-async-v1-0-61780fee111c@gmail.com
link: https://lore.kernel.org/linux-block/20261102-bug-nvme-remove-ns-async-v1-0-61780fee111c@gmail.com/
---

# [PATCH 0/2] nvme: delete controllers with many namespaces faster

来源：[https://lore.kernel.org/linux-block/20261102-bug-nvme-remove-ns-async-v1-0-61780fee111c@gmail.com/](https://lore.kernel.org/linux-block/20261102-bug-nvme-remove-ns-async-v1-0-61780fee111c@gmail.com/)

```
Deleting an nvme controller removes its namespaces one after another,
about 20 ms each, so disconnecting from a fabrics target with 64
namespaces takes over a second.

Patch 1 removes the namespaces in parallel, as scanning already adds
them. Patch 2 drops the write lock that del_gendisk() takes on the tag
set, which would otherwise serialize the parallel removals again.

Disconnecting from a tcp target on the same host with 64 namespaces
drops from 1201-1308 ms to 115-124 ms. Details are in each patch.

Signed-off-by: Qiliang Yuan <odys.yuan@gmail.com>
---
Qiliang Yuan (2):
      nvme: remove namespaces in parallel
      block: set QUEUE_FLAG_NO_ELV_SWITCH under the read lock in del_gendisk()

 block/genhd.c            | 17 +++++------------
 drivers/nvme/host/core.c | 13 ++++++++++++-
 2 files changed, 17 insertions(+), 13 deletions(-)
---
base-commit: 6628e7d4c6b25c8d18f1345e3a20d21829aae7e4
change-id: 20261102-bug-nvme-remove-ns-async-ceaaa1eda6a7

Best regards,
-- 
Qiliang Yuan <odys.yuan@gmail.com>
```
