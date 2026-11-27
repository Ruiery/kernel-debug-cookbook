---
title: [PATCH] cpu/hotplug: Rename cpuhp_remove_multi_state to be symmetric with setup
list: linux-block
message_id: 20261127-fix-rename_cpuhp_remove_multi_state-v1-1-097db4564cbd@csail.mit.edu
link: https://lore.kernel.org/linux-block/20261127-fix-rename_cpuhp_remove_multi_state-v1-1-097db4564cbd@csail.mit.edu/
---

# [PATCH] cpu/hotplug: Rename cpuhp_remove_multi_state to be symmetric with setup

来源：[https://lore.kernel.org/linux-block/20261127-fix-rename_cpuhp_remove_multi_state-v1-1-097db4564cbd@csail.mit.edu/](https://lore.kernel.org/linux-block/20261127-fix-rename_cpuhp_remove_multi_state-v1-1-097db4564cbd@csail.mit.edu/)

```
The multi-instance CPU hotplug state setup API is named as
cpuhp_setup_state_multi(), whereas the corresponding remove API is
currently named as cpuhp_remove_multi_state(). Rename the latter as
cpuhp_remove_state_multi() to fix the asymmetry. This also helps
maintain consistency in the API names by letting them share a common
prefix, i.e., cpuhp_setup/remove_state_*() across all the variants
[none|nocalls|nocalls_cpuslocked].

Signed-off-by: Srivatsa S. Bhat (Microsoft) <srivatsa@csail.mit.edu>
---
Performing the API rename in
Documentation/translations/zh_CN/core-api/cpu_hotplug.rst is left as a
to-do, as I don't know how to edit that file correctly, and didn't want
to mess up the translation in the process. If someone can help do the
rename in that file safely, that would be much appreciated!
---
 Documentation/core-api/cpu_hotplug.rst       | 6 +++---
 drivers/block/zram/zram_drv.c                | 6 +++---
 drivers/devfreq/event/rockchip-dfi.c         | 2 +-
 drivers/fpga/dfl-fme-perf.c                  | 4 ++--
 drivers/hwtracing/coresight/coresight-trbe.c | 4 ++--
 drivers/hwtracing/ptt/hisi_ptt.c             | 4 ++--
 drivers/iommu/iova.c                         | 2 +-
 drivers/md/raid5.c                           | 4 ++--
 drivers/net/ethernet/ibm/ibmvnic.c           | 8 ++++----
 drivers/net/ethernet/marvell/mvneta.c        | 8 ++++----
 drivers/net/virtio_net.c                     | 8 ++++----
 drivers/nvdimm/nd_perf.c                     | 6 +++---
 drivers/perf/alibaba_uncore_drw_pmu.c        | 4 ++--
 drivers/perf/arm-ccn.c                       | 4 ++--
 drivers/perf/arm-cmn.c                       | 4 ++--
 drivers/perf/arm-ni.c                        | 4 ++--
 drivers/perf/arm_cspmu/arm_cspmu.c           | 2 +-
 drivers/perf/arm_dmc620_pmu.c                | 4 ++--
 drivers/perf/arm_dsu_pmu.c                   | 4 ++--
 drivers/perf/arm_smmuv3_pmu.c                | 4 ++--
 drivers/perf/arm_spe_pmu.c                   | 4 ++--
 drivers/perf/cxl_pmu.c                       | 4 ++--
 drivers/perf/dwc_pcie_pmu.c                  | 4 ++--
 drivers/perf/fsl_imx8_ddr_perf.c             | 4 ++--
 drivers/perf/fsl_imx9_ddr_perf.c             | 4 ++--
 drivers/perf/fujitsu_uncore_pmu.c            | 4 ++--
 drivers/perf/hisilicon/hisi_pcie_pmu.c       | 4 ++--
 drivers/perf/hisilicon/hisi_uncore_l3c_pmu.c | 4 ++--
 drivers/perf/hisilicon/hisi_uncore_pmu.c     | 2 +-
 drivers/perf/hisilicon/hns3_pmu.c            | 4 ++--
 drivers/perf/marvell_cn10k_ddr_pmu.c         | 4 ++--
 drivers/perf/marvell_cn10k_tad_pmu.c         | 4 ++--
 drivers/perf/marvell_pem_pmu.c               | 4 ++--
 drivers/perf/nvidia_t410_c2c_pmu.c           | 2 +-
 drivers/perf/nvidia_t410_cmem_latency_pmu.c  | 2 +-
 drivers/perf/thunderx2_pmu.c                 | 4 ++--
 drivers/scsi/lpfc/lpfc_init.c                | 4 ++--
 include/linux/cpuhotplug.h                   | 4 ++--
 kernel/padata.c                              | 2 +-
 kernel/trace/trace.c                         | 2 +-
 mm/zswap.c                                   | 2 +-
 41 files changed, 82 insertions(+), 82 deletions(-)

diff --git a/Documentation/core-api/cpu_hotplug.rst b/Documentation/core-api/cpu_hotplug.rst
index f8b3f59a3d5f..a387ccb08eef 100644
--- a/Documentation/core-api/cpu_hotplug.rst
+++ b/Documentation/core-api/cpu_hotplug.rst
@@ -471,7 +471,7 @@ To remove a previously set up state, the following functions are provided:
 * cpuhp_remove_state(state)
 * cpuhp_remove_state_nocalls(state)
 * cpuhp_remove_state_nocalls_cpuslocked(state)
-* cpuhp_remove_multi_state(state)
+* cpuhp_remove_state_multi(state)
 
 The @state argument is either a statically allocated state or the state
 number which was allocated in the dynamic range by cpuhp_setup_state*(). If
@@ -481,7 +481,7 @@ available for dynamic allocation again.
 The functions differ in the way how the installed callbacks are treated:
 
   * cpuhp_remove_state_nocalls(), cpuhp_remove_state_nocalls_cpuslocked()
-    and cpuhp_remove_multi_state() only remove the callbacks.
+    and cpuhp_remove_state_multi() only remove the callbacks.
 
   * cpuhp_remove_state() removes the callbacks and invokes the teardown
     callback (if not NULL) for all online CPUs which have currently a state
@@ -611,7 +611,7 @@ ONLINE section for notifications on online and offline operation::
    ....
    cpuhp_state_remove_instance(state, &inst2->node);
    ....
-   cpuhp_remove_multi_state(state);
+   cpuhp_remove_state_multi(state);
 
 
 Testing of hotplug states
diff --git a/drivers/block/zram/zram_drv.c b/drivers/block/zram/zram_drv.c
index ab064c84b092..d152c356bd6a 100644
--- a/drivers/block/zram/zram_drv.c
+++ b/drivers/block/zram/zram_drv.c
@@ -3270,7 +3270,7 @@ static void destroy_devices(void)
 	zram_debugfs_destroy();
 	idr_destroy(&zram_index_idr);
 	unregister_blkdev(zram_major, "zram");
-	cpuhp_remove_multi_state(CPUHP_ZCOMP_PREPARE);
+	cpuhp_remove_state_multi(CPUHP_ZCOMP_PREPARE);
 }
 
 static int __init zram_init(void)
@@ -3288,7 +3288,7 @@ static int __init zram_init(void)
 	ret = class_register(&zram_control_class);
 	if (ret) {
 		pr_err("Unable to register zram-control class\n");
-		cpuhp_remove_multi_state(CPUHP_ZCOMP_PREPARE);
+		cpuhp_remove_state_multi(CPUHP_ZCOMP_PREPARE);
 		return ret;
 	}
 
@@ -3297,7 +3297,7 @@ static int __init zram_init(void)
 	if (zram_major <= 0) {
 		pr_err("Unable to get major number\n");
 		class_unregister(&zram_control_class);
-		cpuhp_remove_multi_state(CPUHP_ZCOMP_PREPARE);
+		cpuhp_remove_state_multi(CPUHP_ZCOMP_PREPARE);
 		return -EBUSY;
 	}
 
diff --git a/drivers/devfreq/event/rockchip-dfi.c b/drivers/devfreq/event/rockchip-dfi.c
index 16b25779d2f8..137adb1b7d27 100644
--- a/drivers/devfreq/event/rockchip-dfi.c
+++ b/drivers/devfreq/event/rockchip-dfi.c
@@ -614,7 +614,7 @@ static void rockchip_ddr_cpuhp_remove_state(void *data)
 {
 	struct rockchip_dfi *dfi = data;
 
-	cpuhp_remove_multi_state(dfi->cpuhp_state);
+	cpuhp_remove_state_multi(dfi->cpuhp_state);
 
 	rockchip_dfi_disable(dfi);
 }
diff --git a/drivers/fpga/dfl-fme-perf.c b/drivers/fpga/dfl-fme-perf.c
index a0e3abc64c9e..9cd5327ceab4 100644
--- a/drivers/fpga/dfl-fme-perf.c
+++ b/drivers/fpga/dfl-fme-perf.c
@@ -998,7 +998,7 @@ static int fme_perf_init(struct platform_device *pdev,
 pmu_register_err:
 	cpuhp_state_remove_instance_nocalls(priv->cpuhp_state, &priv->node);
 cpuhp_instance_err:
-	cpuhp_remove_multi_state(priv->cpuhp_state);
+	cpuhp_remove_state_multi(priv->cpuhp_state);
 	return ret;
 }
 
@@ -1009,7 +1009,7 @@ static void fme_perf_uinit(struct platform_device *pdev,
 
 	fme_perf_pmu_unregister(priv);
 	cpuhp_state_remove_instance_nocalls(priv->cpuhp_state, &priv->node);
-	cpuhp_remove_multi_state(priv->cpuhp_state);
+	cpuhp_remove_state_multi(priv->cpuhp_state);
 }
 
 const struct dfl_feature_id fme_perf_id_table[] = {
diff --git a/drivers/hwtracing/coresight/coresight-trbe.c b/drivers/hwtracing/coresight/coresight-trbe.c
index 3fa663c7f026..06d2c5b93f63 100644
--- a/drivers/hwtracing/coresight/coresight-trbe.c
+++ b/drivers/hwtracing/coresight/coresight-trbe.c
@@ -1524,7 +1524,7 @@ static int arm_trbe_probe_cpuhp(struct trbe_drvdata *drvdata)
 
 	ret = cpuhp_state_add_instance(trbe_online, &drvdata->hotplug_node);
 	if (ret) {
-		cpuhp_remove_multi_state(trbe_online);
+		cpuhp_remove_state_multi(trbe_online);
 		return ret;
 	}
 	drvdata->trbe_online = trbe_online;
@@ -1534,7 +1534,7 @@ static int arm_trbe_probe_cpuhp(struct trbe_drvdata *drvdata)
 static void arm_trbe_remove_cpuhp(struct trbe_drvdata *drvdata)
 {
 	cpuhp_state_remove_instance(drvdata->trbe_online, &drvdata->hotplug_node);
-	cpuhp_remove_multi_state(drvdata->trbe_online);
+	cpuhp_remove_state_multi(drvdata->trbe_online);
 }
 
 static int arm_trbe_probe_irq(struct platform_device *pdev,
diff --git a/drivers/hwtracing/ptt/hisi_ptt.c b/drivers/hwtracing/ptt/hisi_ptt.c
index 6ed65b44a4af..7d7dbc0916c1 100644
--- a/drivers/hwtracing/ptt/hisi_ptt.c
+++ b/drivers/hwtracing/ptt/hi
```
