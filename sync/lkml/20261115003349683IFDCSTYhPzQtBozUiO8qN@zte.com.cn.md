---
title: [PATCH] ublk: validate all parameters for zoned devices
list: linux-block
message_id: 20261115003349683IFDCSTYhPzQtBozUiO8qN@zte.com.cn
link: https://lore.kernel.org/linux-block/20261115003349683IFDCSTYhPzQtBozUiO8qN@zte.com.cn/
---

# [PATCH] ublk: validate all parameters for zoned devices

来源：[https://lore.kernel.org/linux-block/20261115003349683IFDCSTYhPzQtBozUiO8qN@zte.com.cn/](https://lore.kernel.org/linux-block/20261115003349683IFDCSTYhPzQtBozUiO8qN@zte.com.cn/)

```
From: Shao Mingyin <shao.mingyin@zte.com.cn>

ublk_validate_params() returns as soon as zoned parameters are valid,
skipping the subsequent DMA alignment, segment and integrity checks.
SET_PARAMS therefore accepts combinations that it rejects for a
non-zoned device, including integrity parameters without UBLK_F_INTEGRITY.
Invalid parameters may reach disk creation or advertise an integrity
format that the server cannot access.

Continue checking the remaining parameter types after successful zoned
validation. Preserve the zoned validator's errors and the requirement
for zoned devices to supply zoned parameters.

Fixes: e84025d2a9cb ("ublk: add DMA alignment limit")
Signed-off-by: Shao Mingyin <shao.mingyin@zte.com.cn>
---
Tested on next-20261105 in an x86_64 QEMU/KVM guest (4 vCPUs, 4 GiB,
4 KiB pages), with CONFIG_BLK_DEV_UBLK, CONFIG_BLK_DEV_ZONED and
CONFIG_BLK_DEV_INTEGRITY enabled. The same userspace program submits
ADD_DEV, SET_PARAMS and DEL_DEV through io_uring to both kernels.

Independently invalid DMA alignment, segment boundary and integrity
parameters without UBLK_F_INTEGRITY are accepted by the original kernel
and rejected with -EINVAL by the fix. The integrity test uses valid DMA
and segment parameters; enabling UBLK_F_INTEGRITY makes the same parameters
valid on both kernels. Valid optional parameters are also accepted by
both. All five checks pass on three independent boots per kernel.

Separate userspace function tests cover 4 KiB and 64 KiB page-size
boundaries. The QEMU tests exercise SET_PARAMS only, without START_DEV
or block I/O.

 drivers/block/ublk_drv.c | 10 +++++++---
 1 file changed, 7 insertions(+), 3 deletions(-)

diff --git a/drivers/block/ublk_drv.c b/drivers/block/ublk_drv.c
index 3d322fa1bc83160f51fbd97fb89b17ee94bc1213..ce1c192e3590cb8ddfeb495629540a653658513a 100644
--- a/drivers/block/ublk_drv.c
+++ b/drivers/block/ublk_drv.c
@@ -1011,10 +1011,14 @@ static int ublk_validate_params(const struct ublk_device *ub)
 	if (ub->params.types & UBLK_PARAM_TYPE_DEVT)
 		return -EINVAL;
 
-	if (ub->params.types & UBLK_PARAM_TYPE_ZONED)
-		return ublk_dev_param_zoned_validate(ub);
-	else if (ublk_dev_is_zoned(ub))
+	if (ub->params.types & UBLK_PARAM_TYPE_ZONED) {
+		int ret = ublk_dev_param_zoned_validate(ub);
+
+		if (ret)
+			return ret;
+	} else if (ublk_dev_is_zoned(ub)) {
 		return -EINVAL;
+	}
 
 	if (ub->params.types & UBLK_PARAM_TYPE_DMA_ALIGN) {
 		const struct ublk_param_dma_align *p = &ub->params.dma;
-- 
2.43.0
```
