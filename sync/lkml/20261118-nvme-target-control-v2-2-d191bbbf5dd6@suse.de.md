---
title: [PATCH blktests v2 2/9] contrib/nvme-target-control: pick a free service ID for new nvmet ports
list: linux-block
message_id: 20261118-nvme-target-control-v2-2-d191bbbf5dd6@suse.de
link: https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-2-d191bbbf5dd6@suse.de/
---

# [PATCH blktests v2 2/9] contrib/nvme-target-control: pick a free service ID for new nvmet ports

来源：[https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-2-d191bbbf5dd6@suse.de/](https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-2-d191bbbf5dd6@suse.de/)

```
The nvmet target derives the service ID from the port ID. On a target
that already has ports this clashes with existing ports, and nvme/003
connects to a service ID nothing listens on. Use the lowest free
service ID starting at trsvid instead.

Fixes: 79c32fb31b7b ("contrib: make nvme-target-control a standalone project")
Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 contrib/nvme-target-control/README.md                       | 13 +++++++------
 .../nvme_target_control/targets/nvmet.sh                    |  7 ++++++-
 2 files changed, 13 insertions(+), 7 deletions(-)

diff --git a/contrib/nvme-target-control/README.md b/contrib/nvme-target-control/README.md
index dc421b00b788..9abd7f30932d 100644
--- a/contrib/nvme-target-control/README.md
+++ b/contrib/nvme-target-control/README.md
@@ -61,12 +61,13 @@ is set, the namespace is a loop device on an image file in
 subsystem, the ports which don't export another subsystem, the hosts no
 other subsystem allows, and the loop device and image file.
 
-A new port gets the lowest free nvmet port ID N, starting at 1, and listens
-on `traddr` at service ID `trsvid` + N - 1. The first port of a target
-without other ports listens on `trsvid`. The nvmet target implements all
-port commands: `add-ports`, `add-port`, `remove-port`, `list-ports`,
-`show-port` and `set-ana`, and `set-host`, which changes the DH-CHAP keys,
-hash and DH group of the host.
+A new port gets the lowest free nvmet port ID, starting at 1, and the
+lowest service ID from `trsvid` up which no other port uses: the first
+port listens on `traddr` at `trsvid` unless another port of the target
+does. The nvmet target implements all port commands: `add-ports`,
+`add-port`, `remove-port`, `list-ports`, `show-port` and `set-ana`, and
+`set-host`, which changes the DH-CHAP keys, hash and DH group of the
+host.
 
 | Option | Meaning |
 | --- | --- |
diff --git a/contrib/nvme-target-control/nvme_target_control/targets/nvmet.sh b/contrib/nvme-target-control/nvme_target_control/targets/nvmet.sh
index 33f383eb17f0..7d6e9cd40da0 100644
--- a/contrib/nvme-target-control/nvme_target_control/targets/nvmet.sh
+++ b/contrib/nvme-target-control/nvme_target_control/targets/nvmet.sh
@@ -59,6 +59,11 @@ add_port() {
 	while [ -e "${cfs}/ports/${port}" ]; do
 		port=$((port + 1))
 	done
+	# The target may have other ports, take the first free service ID.
+	while cat "${cfs}"/ports/*/addr_trsvcid 2> /dev/null |
+			grep -qx "${trsvcid}"; do
+		trsvcid=$((trsvcid + 1))
+	done
 	case "${traddr}" in
 	*:*)	adrfam=ipv6 ;;
 	*)	adrfam=ipv4 ;;
@@ -68,7 +73,7 @@ add_port() {
 	echo "${trtype}" > "${cfs}/ports/${port}/addr_trtype"
 	echo "${adrfam}" > "${cfs}/ports/${port}/addr_adrfam"
 	echo "${traddr}" > "${cfs}/ports/${port}/addr_traddr"
-	echo $((trsvcid + port - 1)) > "${cfs}/ports/${port}/addr_trsvcid"
+	echo "${trsvcid}" > "${cfs}/ports/${port}/addr_trsvcid"
 	case "${tls}" in
 	none)
 		;;

-- 
2.56.1
```
