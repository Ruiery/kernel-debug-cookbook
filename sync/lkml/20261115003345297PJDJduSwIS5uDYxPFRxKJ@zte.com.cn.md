---
title: [PATCH] partitions: aix: validate the physical partition size exponent
list: linux-block
message_id: 20261115003345297PJDJduSwIS5uDYxPFRxKJ@zte.com.cn
link: https://lore.kernel.org/linux-block/20261115003345297PJDJduSwIS5uDYxPFRxKJ@zte.com.cn/
---

# [PATCH] partitions: aix: validate the physical partition size exponent

来源：[https://lore.kernel.org/linux-block/20261115003345297PJDJduSwIS5uDYxPFRxKJ@zte.com.cn/](https://lore.kernel.org/linux-block/20261115003345297PJDJduSwIS5uDYxPFRxKJ@zte.com.cn/)

```
From: Shao Mingyin <shao.mingyin@zte.com.cn>

The physical partition size exponent is read as an unvalidated 16-bit
value from the LVM record and used as the shift count of an int. Values
of 32 or more cause an out-of-range shift and can produce an unrelated
partition size. Exponents below SECTOR_SHIFT produce a zero sector count.

Reject sizes that cannot be represented by the parser's u32 byte count
or do not cover a whole sector before doing the shift. Use an unsigned
operand to express the representable byte count directly.

Fixes: 6ceea22bbbc84 ("partitions: add aix lvm partition support files")
Cc: stable@vger.kernel.org
Signed-off-by: Shao Mingyin <shao.mingyin@zte.com.cn>
---
Testing:
Tested on x86_64 Linux next-20261113 in QEMU/KVM with UBSAN_SHIFT.
Disk images containing exponents 32, 33 and 65535 trigger shift-out-of-
bounds diagnostics in the base kernel. The fixed kernel rejects all
three without a diagnostic. Valid exponents 9, 20 and 31 retain the same
partition start and size in both kernels, including normal end-of-disk
truncation for the largest size. Also built with W=1 for m68k and i386;
existing AIX kernel-doc warnings are identical to the base build.

base-commit: 84abb955b1015477aa11a96e2f3ac1b938b77f48

 block/partitions/aix.c | 6 +++++-
 1 file changed, 5 insertions(+), 1 deletion(-)

diff --git a/block/partitions/aix.c b/block/partitions/aix.c
index 689837deba279b1817f69edd2ce4246604e13564..b01b2c62162ddc0c724a681892f07d9d6f4a5275 100644
--- a/block/partitions/aix.c
+++ b/block/partitions/aix.c
@@ -177,7 +177,11 @@ int aix_partition(struct parsed_partitions *state)
 		if (lvm_version == 1) {
 			int pp_size_log2 = be16_to_cpu(p->pp_size);
 
-			pp_bytes_size = 1 << pp_size_log2;
+			if (pp_size_log2 < SECTOR_SHIFT || pp_size_log2 >= 32) {
+				put_dev_sector(sect);
+				return 0;
+			}
+			pp_bytes_size = 1U << pp_size_log2;
 			pp_blocks_size = pp_bytes_size / 512;
 			seq_buf_printf(&state->pp_buf,
 				       " AIX LVM header version %u found\n",
-- 
2.43.0
```
