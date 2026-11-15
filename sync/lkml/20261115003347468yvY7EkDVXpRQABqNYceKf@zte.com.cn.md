---
title: [PATCH] partitions: sun: calculate partition starts in sector_t
list: linux-block
message_id: 20261115003347468yvY7EkDVXpRQABqNYceKf@zte.com.cn
link: https://lore.kernel.org/linux-block/20261115003347468yvY7EkDVXpRQABqNYceKf@zte.com.cn/
---

# [PATCH] partitions: sun: calculate partition starts in sector_t

来源：[https://lore.kernel.org/linux-block/20261115003347468yvY7EkDVXpRQABqNYceKf@zte.com.cn/](https://lore.kernel.org/linux-block/20261115003347468yvY7EkDVXpRQABqNYceKf@zte.com.cn/)

```
From: Shao Mingyin <shao.mingyin@zte.com.cn>

The Sun label parser calculates sectors per cylinder and partition
starts in unsigned long. On 32-bit systems a start above UINT_MAX
sectors wraps before put_partition() receives it, potentially exposing
a partition at the wrong location. The same label is parsed differently
on a 64-bit system.

Keep both values in sector_t and promote the first geometry operand
before multiplication. This also prevents the two 16-bit geometry
fields from being multiplied as signed int when their product exceeds
INT_MAX.

Cc: stable@vger.kernel.org
Signed-off-by: Shao Mingyin <shao.mingyin@zte.com.cn>
---
Testing:
Built with W=1 for i386 and m68k. Ran the complete parser against five
checksummed labels in freestanding i386 and x86_64 test programs with
substitutes for disk reads and partition registration. The base parser
miscalculates two starts on each ABI; the fixed parser matches the
independently calculated starts for all five labels on each ABI.

Also tested a checksummed Sun label in x86_64 QEMU/KVM with both geometry
fields set to 65535. The base kernel discards its partition because of
the miscalculated start; the fixed kernel reports start sector
4294836225 and length 128. The backing disk is a sparse image.

The arithmetic is already present in the initial Linux git snapshot;
its original introducing commit has not been identified.

base-commit: 84abb955b1015477aa11a96e2f3ac1b938b77f48

 block/partitions/sun.c | 6 +++---
 1 file changed, 3 insertions(+), 3 deletions(-)

diff --git a/block/partitions/sun.c b/block/partitions/sun.c
index 92c645fcd2e09bfd82a51fdfa81e4ee61f42051d..02ddc967846b884d2e03e3858c0ecfdf5be888b2 100644
--- a/block/partitions/sun.c
+++ b/block/partitions/sun.c
@@ -64,7 +64,7 @@ int sun_partition(struct parsed_partitions *state)
 		__be16 csum;       /* Label xor'd checksum */
 	} * label;
 	struct sun_partition *p;
-	unsigned long spc;
+	sector_t spc;
 	int use_vtoc;
 	int nparts;
 
@@ -102,9 +102,9 @@ int sun_partition(struct parsed_partitions *state)
 	 */
 	use_vtoc = use_vtoc || !(label->vtoc.sanity ||
 				 label->vtoc.version || label->vtoc.nparts);
-	spc = be16_to_cpu(label->ntrks) * be16_to_cpu(label->nsect);
+	spc = (sector_t)be16_to_cpu(label->ntrks) * be16_to_cpu(label->nsect);
 	for (i = 0; i < nparts; i++, p++) {
-		unsigned long st_sector;
+		sector_t st_sector;
 		unsigned int num_sectors;
 
 		st_sector = be32_to_cpu(p->start_cylinder) * spc;
-- 
2.43.0
```
