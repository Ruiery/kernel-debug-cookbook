---
title: [PATCH blktests 07/10] common/nvme: support the ports of a remote target
list: linux-block
message_id: 20261104-nvme-target-control-v1-7-b31b40537bb4@suse.de
link: https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-7-b31b40537bb4@suse.de/
---

# [PATCH blktests 07/10] common/nvme: support the ports of a remote target

来源：[https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-7-b31b40537bb4@suse.de/](https://lore.kernel.org/linux-block/20261104-nvme-target-control-v1-7-b31b40537bb4@suse.de/)

```
With NVME_TARGET_CONTROL the port helpers still use the local nvmet
configfs. _create_nvmet_port, _remove_nvmet_port and
_setup_nvmet_port_ana write to it. _get_nvmet_ports and
_get_nvmet_port_params read from it. The ports of a remote subsystem
are not there. _nvmet_target_setup doesn't pass the number of ports to
the script, and _nvmet_target_add_ports only reports that add-ports is a
stub. The tests which use more than one port don't work with a remote
target, e.g. nvme/057 finds no port and connects to none.

Use the port commands of the script instead: setup --ports, add-ports,
add-port, remove-port, list-ports, show-port and set-ana, with --tls or
--force-tls for the TLS mode. _nvme_connect_subsys finds the port of the
subsystem with list-ports, as it does with the local target. If the
script lists no port, e.g. for a target which is configured already, it
connects to the address config shows, as before.

Document the port commands in running-tests.md.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 Documentation/running-tests.md | 29 ++++++++++++++++++
 common/nvme                    | 69 +++++++++++++++++++++++++++++++++++-------
 2 files changed, 87 insertions(+), 11 deletions(-)

diff --git a/Documentation/running-tests.md b/Documentation/running-tests.md
index 095d6aa4e18e..9ca01e6893ec 100644
--- a/Documentation/running-tests.md
+++ b/Documentation/running-tests.md
@@ -255,10 +255,39 @@ The blktests expects that the script interface implements following
   --hostnqn HOSTNQN
   --ctrlkey CTRLKEY
   --hostkey HOSTKEY
+  --ports NR_PORTS
+  --tls | --force-tls
 
 cleanup:
   --subsysnqn SUBSYSNQN
 
+The tests which use more than one port, or add and remove ports, also need
+the port commands. A port is named by an ID the script picks:
+
+add-ports: export the subsystem on NR_PORTS more ports, print their IDs
+  --subsysnqn SUBSYSNQN
+  --ports NR_PORTS
+  --tls | --force-tls
+
+add-port: create a port which exports no subsystem, print its ID
+  --tls | --force-tls
+
+remove-port:
+  --port PORT
+
+list-ports: print the IDs of the ports which export the subsystem
+  --subsysnqn SUBSYSNQN
+
+show-port: print the transport type, address and service ID of the port
+  --port PORT
+
+set-ana: set the state of an ANA group on the port
+  --port PORT
+  --grpid GRPID
+  --state STATE
+
+If list-ports prints nothing, blktests connects to the address config shows.
+
 contrib/nvme-target-control implements this interface. It configures a Linux
 nvmet target over ssh and can be extended for other targets, see
 contrib/nvme-target-control/README.md.
diff --git a/common/nvme b/common/nvme
index dfe85b6e281f..698d6bf780ef 100644
--- a/common/nvme
+++ b/common/nvme
@@ -888,20 +888,21 @@ _nvme_connect_subsys() {
 		esac
 	done
 
+	if [[ -z "${port}" ]]; then
+		local ports
+
+		_get_nvmet_ports "${subsysnqn}" ports
+		port="${ports[0]##*/}"
+	fi
 	if [[ -n "${nvme_target_control}" && -z "${port}" ]]; then
+		# The target doesn't list ports, e.g. it is configured already.
 		ARGS+=(--transport "$(${nvme_target_control} config --show-trtype)")
 		ARGS+=(--traddr "${def_traddr}")
 		ARGS+=(--trsvcid "${def_trsvcid}")
 	else
 		if [[ -z "${port}" ]]; then
-			local ports
-
-			_get_nvmet_ports "${subsysnqn}" ports
-			port="${ports[0]##*/}"
-			if [[ -z "${port}" ]]; then
-				echo "WARNING: no port found"
-				return 1
-			fi
+			echo "WARNING: no port found"
+			return 1
 		fi
 		_get_nvmet_port_params "${port}" ARGS
 	fi
@@ -1079,6 +1080,18 @@ _fc_host_traddr() {
 	printf "nn-%s:pn-%s" "$(_host_wwnn $port)" "$(_host_wwpn $port)"
 }
 
+# Print the nvme-target-control option for the TLS mode of a port.
+_nvme_target_control_tls() {
+	case "$1" in
+	not-required)
+		echo "--tls"
+		;;
+	required)
+		echo "--force-tls"
+		;;
+	esac
+}
+
 _create_nvmet_port() {
 	local tls="${1:-none}"
 	local host_port="${2:-0}"
@@ -1088,6 +1101,13 @@ _create_nvmet_port() {
 	local trsvcid="${def_trsvcid}"
 	local portcfs
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		# shellcheck disable=SC2046
+		"${nvme_target_control}" add-port \
+			$(_nvme_target_control_tls "${tls}")
+		return
+	fi
+
 	local port
 	for ((port = 0; ; port++)); do
 		if [[ ! -e "${NVMET_CFS}/ports/${port}" ]]; then
@@ -1157,6 +1177,12 @@ _setup_nvmet_port_ana() {
 	local cfsport="${NVMET_CFS}/ports/${port}"
 	local anaport="${cfsport}/ana_groups/${anagrpid}"
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		"${nvme_target_control}" set-ana --port "${port}" \
+			--grpid "${anagrpid}" --state "${anastate}"
+		return
+	fi
+
 	if [[ ! -d "${anaport}" ]] ; then
 		if [[ "${anagrpid}" -eq 1 ]]; then
 			echo "FAIL target setup failed, ANA not supported"
@@ -1173,6 +1199,11 @@ _remove_nvmet_port() {
 	local cfsport="${NVMET_CFS}/ports/${port}"
 	local a
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		"${nvme_target_control}" remove-port --port "${port}"
+		return
+	fi
+
 	if [[ "${nvme_trtype}" == "fc" ]]; then
 		_nvme_fcloop_del_tport "$(_remote_wwnn "$port")" \
 				       "$(_remote_wwpn "$port")"
@@ -1446,6 +1477,13 @@ _get_nvmet_ports() {
 	local -n nvmet_ports="$2"
 	local cfs_path="${NVMET_CFS}/ports"
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		mapfile -t -O "${#nvmet_ports[@]}" nvmet_ports < <(
+			"${nvme_target_control}" list-ports \
+				--subsysnqn "${nvmet_subsysnqn}")
+		return
+	fi
+
 	for port in "${cfs_path}/"*; do
 		if [[ -e "${port}/subsystems/${nvmet_subsysnqn}" ]]; then
 			nvmet_ports+=("${port##*/}")
@@ -1473,7 +1511,12 @@ _get_nvmet_port_params() {
 	local trsvcid="${def_trsvcid}"
 
 	# When port is specified, get port dependent parameter values
-	if [[ $port != none ]]; then
+	if [[ $port != none && -n "${nvme_target_control}" ]]; then
+		read -r trtype traddr trsvcid < <(
+			"${nvme_target_control}" show-port --port "${port}")
+		[[ -n "${trsvcid}" ]] || exit 1
+		args+=(--traddr "${traddr}")
+	elif [[ $port != none ]]; then
 		[[ -d "${cfs_path}" ]] || exit 1
 		trtype=$(cat "${cfs_path}/addr_trtype")
 		traddr=$(cat "${cfs_path}/addr_traddr")
@@ -1621,10 +1664,13 @@ _nvmet_target_setup() {
 			ARGS+=(--ctrlkey "${ctrlkey}")
 		fi
 
+		# shellcheck disable=SC2046
 		"${nvme_target_control}" setup \
 					 --subsysnqn "${subsysnqn}" \
 					 --subsys-uuid "${subsys_uuid:-$def_subsys_uuid}" \
 					 --hostnqn "${def_hostnqn}" \
+					 --ports "${num_ports}" \
+					 $(_nvme_target_control_tls "${tls}") \
 					 "${ARGS[@]}" &> /dev/null
 		p=0
 		while (( p < num_ports )); do
@@ -1719,19 +1765,20 @@ _nvmet_target_add_ports() {
 			ARGS+=(--ctrlkey "${ctrlkey}")
 		fi
 
+		# shellcheck disable=SC2046
 		"${nvme_target_control}" add-ports \
 					 --ports "${num_ports}" \
 					 --subsysnqn "${subsysnqn}" \
 					 --subsys-uuid "${subsys_uuid:-$def_subsys_uuid}" \
 					 --hostnqn "${def_hostnqn}" \
-					 "${ARGS[@]}" &> /dev/null
+					 $(_nvme_target_control_tls "${tls}") \
+					 "${ARGS[@]}" > /dev/null
 		p=0
 		while (( p < num_ports )); do
 			# Set ports_to_hosts so that _get_fc_host_port() can return the correct host port
 			ports_to_hosts+=("${host_port}")
 			p=$(( p + 1 ))
 		done
-		echo "'${nvme_target_control} add-ports' is a stub"
 		return
 	fi
 

-- 
2.56.0
```
