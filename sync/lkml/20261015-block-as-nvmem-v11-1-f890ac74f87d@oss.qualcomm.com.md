---
title: [PATCH v11 1/7] dt-bindings: bluetooth: qcom: Add NVMEM BD address cell
list: linux-block
message_id: 20261015-block-as-nvmem-v11-1-f890ac74f87d@oss.qualcomm.com
link: https://lore.kernel.org/linux-block/20261015-block-as-nvmem-v11-1-f890ac74f87d@oss.qualcomm.com/
---

# [PATCH v11 1/7] dt-bindings: bluetooth: qcom: Add NVMEM BD address cell

来源：[https://lore.kernel.org/linux-block/20261015-block-as-nvmem-v11-1-f890ac74f87d@oss.qualcomm.com/](https://lore.kernel.org/linux-block/20261015-block-as-nvmem-v11-1-f890ac74f87d@oss.qualcomm.com/)

```
Add support for an NVMEM cell provider for "local-bd-address",
allowing the Bluetooth stack to retrieve controller's BD address
from non-volatile storage such as an EEPROM or an eMMC partition.

Reviewed-by: Rob Herring (Arm) <robh@kernel.org>
Reviewed-by: Bartosz Golaszewski <bartosz.golaszewski@oss.qualcomm.com>
Signed-off-by: Loic Poulain <loic.poulain@oss.qualcomm.com>
---
 .../devicetree/bindings/net/bluetooth/qcom,bluetooth-common.yaml | 9 +++++++++
 1 file changed, 9 insertions(+)

diff --git a/Documentation/devicetree/bindings/net/bluetooth/qcom,bluetooth-common.yaml b/Documentation/devicetree/bindings/net/bluetooth/qcom,bluetooth-common.yaml
index c8e9c55c1afb4c8e05ba2dae41ce2db4194b4a0f..7cb28f30c9af032082f23311f2fc89a32f266f17 100644
--- a/Documentation/devicetree/bindings/net/bluetooth/qcom,bluetooth-common.yaml
+++ b/Documentation/devicetree/bindings/net/bluetooth/qcom,bluetooth-common.yaml
@@ -22,4 +22,13 @@ properties:
     description:
       boot firmware is incorrectly passing the address in big-endian order
 
+  nvmem-cells:
+    maxItems: 1
+    description:
+      Nvmem data cell that contains a 6 byte BD address with the most
+      significant byte first (big-endian).
+
+  nvmem-cell-names:
+    const: local-bd-address
+
 additionalProperties: true

-- 
2.34.1
```
