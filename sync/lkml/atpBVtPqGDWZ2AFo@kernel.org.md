---
title: [PATCH] block: let a stacking device inherit its members' DMA alignment
list: linux-block
message_id: atpBVtPqGDWZ2AFo@kernel.org
link: https://lore.kernel.org/linux-block/atpBVtPqGDWZ2AFo@kernel.org/
---

# [PATCH] block: let a stacking device inherit its members' DMA alignment

来源：[https://lore.kernel.org/linux-block/atpBVtPqGDWZ2AFo@kernel.org/](https://lore.kernel.org/linux-block/atpBVtPqGDWZ2AFo@kernel.org/)

```
On Thu, Jul 09, 2026 at 09:15:17AM -0700, Keith Busch wrote:
> From: Keith Busch <kbusch@kernel.org>
> 
> All device mappers that want to override the dma_alignment do so.
> However, because the default stacking limit is set to 511, a device
> mapper couldn't make it smaller even if it is capable of handling
> finer grained alignment.
> 
> Set the default dm stacking dma_alignment limit to 0 so that it can be
> stacked with any value a device mapper wants. If a mapper doesn't
> override the value, the initial 0 value will get changed to the original
> default 511 value when the limits are validated after the device
> stacking is complete.
> 
> Signed-off-by: Keith Busch <kbusch@kernel.org>
> ---
>  drivers/md/dm-table.c | 1 +
>  1 file changed, 1 insertion(+)
> 
> diff --git a/drivers/md/dm-table.c b/drivers/md/dm-table.c
> index dc2eff6b739df..80326f8096cb7 100644
> --- a/drivers/md/dm-table.c
> +++ b/drivers/md/dm-table.c
> @@ -591,6 +591,7 @@ static void dm_set_stacking_limits(struct queue_limits *limits)
>  {
>  	blk_set_stacking_limits(limits);
>  	limits->features |= BLK_FEAT_IO_STAT | BLK_FEAT_NOWAIT | BLK_FEAT_POLL;
> +	limits->dma_alignment = 0;
>  }
>  
>  /*
> -- 
> 2.52.0
> 

This isn't a DM-specific concern (just happens to be that you're
focused on dm-crypt in this patchset).  dm-crypt is still imposing a
too strict dma_alignment, and so that'll need fixing too (along with
other DM targets that aren't properly considering the underlying
devices' queue_limits provided dma_alignment).

But this is a proper fix that I needed to allow MD RAID0 to allow
O_DIRECT to NVMe devices beneath the MD device:

From: Mike Snitzer <snitzer@kernel.org>
Date: Fri, 9 Oct 2026 06:26:29 -0600
Subject: [PATCH] block: let a stacking device inherit its members' DMA alignment

blk_set_stacking_limits() initializes dma_alignment to SECTOR_SIZE - 1,
and blk_stack_limits() then takes the maximum of that and each member's
value.  As a result every MD array and device-mapper table requires
512-byte aligned memory regardless of what its members need: a raid0
of NVMe namespaces reports a dma_alignment of 511 while each member
reports 3.

Direct I/O from memory every member accepts is therefore rejected at
the stacking device, and callers that check the advertised alignment
(for instance through STATX_DIOALIGN) fall back to buffered I/O.

Leave dma_alignment at zero in blk_set_stacking_limits() so that the
stacked value is the strictest of the members'.  blk_validate_limits()
still applies the SECTOR_SIZE - 1 default when nothing was stacked,
such as for a table with no devices.  Targets that process the data
themselves and need logical-block-aligned memory already set
dma_alignment in their io_hints (dm-crypt, dm-integrity, dm-verity,
dm-log-writes), and NVMe multipath sets its own.

Assisted-by: LLM
Signed-off-by: Mike Snitzer <snitzer@kernel.org>
---
 block/blk-settings.c | 9 ++++++++-
 1 file changed, 8 insertions(+), 1 deletion(-)

diff --git a/block/blk-settings.c b/block/blk-settings.c
index 8274631290db..c4b0fba01c4b 100644
--- a/block/blk-settings.c
+++ b/block/blk-settings.c
@@ -41,7 +41,14 @@ void blk_set_stacking_limits(struct queue_limits *lim)
 	lim->physical_block_size = SECTOR_SIZE;
 	lim->io_min = SECTOR_SIZE;
 	lim->discard_granularity = SECTOR_SIZE;
-	lim->dma_alignment = SECTOR_SIZE - 1;
+	/*
+	 * No dma_alignment of its own: blk_stack_limits() keeps the strictest
+	 * of the devices stacked under it, and blk_validate_limits() gives the
+	 * sector-size default to a device left with none.  A driver that looks
+	 * at the data and needs it laid out by logical block says so in its
+	 * own limits, as dm-crypt, dm-integrity, dm-verity and dm-log-writes
+	 * do.
+	 */
 	lim->seg_boundary_mask = BLK_SEG_BOUNDARY_MASK;
 
 	/* Inherit limits from component devices */
-- 
2.52.0
```
