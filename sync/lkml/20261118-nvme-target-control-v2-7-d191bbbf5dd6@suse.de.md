---
title: [PATCH blktests v2 7/9] common/nvme: support the ports of a remote target
list: linux-block
message_id: 20261118-nvme-target-control-v2-7-d191bbbf5dd6@suse.de
link: https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-7-d191bbbf5dd6@suse.de/
---

# [PATCH blktests v2 7/9] common/nvme: support the ports of a remote target

来源：[https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-7-d191bbbf5dd6@suse.de/](https://lore.kernel.org/linux-block/20261118-nvme-target-control-v2-7-d191bbbf5dd6@suse.de/)

```
The port helpers always use the local nvmet configfs, so tests that use
more than one port don't work with a remote target. Use the port
commands of the target control script instead and document them.

Signed-off-by: Daniel Wagner <dwagner@suse.de>
---
 Documentation/running-tests.md | 29 +++++++++++++++++
 common/nvme                    | 70 +++++++++++++++++++++++++++++++++++-------
 2 files changed, 88 insertions(+), 11 deletions(-)

diff --git a/Documentation/running-tests.md b/Documentation/running-tests.md
index d556f1d3b7cc..8300d9aa4842 100644
--- a/Documentation/running-tests.md
+++ b/Documentation/running-tests.md
@@ -256,6 +256,8 @@ The blktests expects that the script interface implements following
   --hostnqn HOSTNQN
   --ctrlkey CTRLKEY
   --hostkey HOSTKEY
+  --ports NR_PORTS
+  --tls | --force-tls
 
 cleanup:
   --subsysnqn SUBSYSNQN
@@ -267,6 +269,33 @@ the target can set up TLS. blktests skips the tests which need a feature
 the list lacks: the authentication tests without dhchap-sha256, and
 nvme/042 and nvme/043 only the steps for the other missing algorithms.
 
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
index 6fba3890b6ce..2590b6343a27 100644
--- a/common/nvme
+++ b/common/nvme
@@ -906,20 +906,21 @@ _nvme_connect_subsys() {
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
@@ -1097,6 +1098,20 @@ _fc_host_traddr() {
 	printf "nn-%s:pn-%s" "$(_host_wwnn $port)" "$(_host_wwpn $port)"
 }
 
+# Add the nvme-target-control option for the TLS mode of a port to an array.
+_nvme_target_control_tls() {
+	local -n tls_args="$2"
+
+	case "$1" in
+	not-required)
+		tls_args+=(--tls)
+		;;
+	required)
+		tls_args+=(--force-tls)
+		;;
+	esac
+}
+
 _create_nvmet_port() {
 	local tls="${1:-none}"
 	local host_port="${2:-0}"
@@ -1106,6 +1121,14 @@ _create_nvmet_port() {
 	local trsvcid="${def_trsvcid}"
 	local portcfs
 
+	if [[ -n "${nvme_target_control}" ]]; then
+		local -a ARGS
+
+		_nvme_target_control_tls "${tls}" ARGS
+		"${nvme_target_control}" add-port "${ARGS[@]}"
+		return
+	fi
+
 	local port
 	for ((port = 0; ; port++)); do
 		if [[ ! -e "${NVMET_CFS}/ports/${port}" ]]; then
@@ -1175,6 +1198,12 @@ _setup_nvmet_port_ana() {
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
@@ -1191,6 +1220,11 @@ _remove_nvmet_port() {
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
@@ -1464,6 +1498,13 @@ _get_nvmet_ports() {
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
@@ -1491,7 +1532,12 @@ _get_nvmet_port_params() {
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
@@ -1638,11 +1684,13 @@ _nvmet_target_setup() {
 		if [[ -n "${ctrlkey}" ]]; then
 			ARGS+=(--ctrlkey "${ctrlkey}")
 		fi
+		_nvme_target_control_tls "${tls}" ARGS
 
 		"${nvme_target_control}" setup \
 					 --subsysnqn "${subsysnqn}" \
 					 --subsys-uuid "${subsys_uuid:-$def_subsys_uuid}" \
 					 --hostnqn "${def_hostnqn}" \
+					 --ports "${num_ports}" \
 					 "${ARGS[@]}" &> /dev/null
 		p=0
 		while (( p < num_ports )); do
@@ -1736,20 +1784,20 @@ _nvmet_target_add_ports() {
 		if [[ -n "${ctrlkey}" ]]; then
 			ARGS+=(--ctrlkey "${ctrlkey}")
 		fi
+		_nvme_target_control_tls "${tls}" ARGS
 
 		"${nvme_target_control}" add-ports \
 					 --ports "${num_ports}" \
 					 --subsysnqn "${subsysnqn}" \
 					 --subsys-uuid "${subsys_uuid:-$def_subsys_uuid}" \
 					 --hostnqn "${def_hostnqn}" \
-					 "${ARGS[@]}" &> /dev/null
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
2.56.1
```
