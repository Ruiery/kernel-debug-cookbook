---
title: [PATCH v11 6/7] Bluetooth: qca: Set NVMEM BD address quirks when address is invalid
list: linux-block
message_id: 20261015-block-as-nvmem-v11-6-f890ac74f87d@oss.qualcomm.com
link: https://lore.kernel.org/linux-block/20261015-block-as-nvmem-v11-6-f890ac74f87d@oss.qualcomm.com/
---

# [PATCH v11 6/7] Bluetooth: qca: Set NVMEM BD address quirks when address is invalid

来源：[https://lore.kernel.org/linux-block/20261015-block-as-nvmem-v11-6-f890ac74f87d@oss.qualcomm.com/](https://lore.kernel.org/linux-block/20261015-block-as-nvmem-v11-6-f890ac74f87d@oss.qualcomm.com/)

```
When the controller BD address is invalid (zero or default),
set the NVMEM quirks to allow retrieving the address from a
'local-bd-address' NVMEM cell. The BD address is often stored
alongside the WiFi MAC address in big-endian format, so also
set the big-endian quirk.

Reviewed-by: Bartosz Golaszewski <bartosz.golaszewski@oss.qualcomm.com>
Signed-off-by: Loic Poulain <loic.poulain@oss.qualcomm.com>
---
 drivers/bluetooth/btqca.c | 5 ++++-
 1 file changed, 4 insertions(+), 1 deletion(-)

diff --git a/drivers/bluetooth/btqca.c b/drivers/bluetooth/btqca.c
index 22b08ab05b829bef2452cacad9c25eb8a63cda19..08600b0fc041cb09c175bf456cefcb6493171aa1 100644
--- a/drivers/bluetooth/btqca.c
+++ b/drivers/bluetooth/btqca.c
@@ -704,8 +704,11 @@ static int qca_check_bdaddr(struct hci_dev *hdev, const struct qca_fw_config *co
 	}
 
 	bda = (struct hci_rp_read_bd_addr *)skb->data;
-	if (!bacmp(&bda->bdaddr, &config->bdaddr))
+	if (!bacmp(&bda->bdaddr, &config->bdaddr)) {
 		hci_set_quirk(hdev, HCI_QUIRK_USE_BDADDR_PROPERTY);
+		hci_set_quirk(hdev, HCI_QUIRK_USE_BDADDR_NVMEM);
+		hci_set_quirk(hdev, HCI_QUIRK_BDADDR_NVMEM_BE);
+	}
 
 	kfree_skb(skb);
 

-- 
2.34.1
```
