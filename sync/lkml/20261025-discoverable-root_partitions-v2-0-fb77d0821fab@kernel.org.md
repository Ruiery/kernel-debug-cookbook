---
title: [PATCH v2 0/7] init: discoverable root partitions
list: linux-block
message_id: 20261025-discoverable-root_partitions-v2-0-fb77d0821fab@kernel.org
link: https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-0-fb77d0821fab@kernel.org/
---

# [PATCH v2 0/7] init: discoverable root partitions

来源：[https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-0-fb77d0821fab@kernel.org/](https://lore.kernel.org/linux-block/20261025-discoverable-root_partitions-v2-0-fb77d0821fab@kernel.org/)

```
DPS [1] defines GPT partition type UUIDs for OS partitions and
attributes that control whether such partitions should be
automatically discovered. The specification states that:

  The OS can discover and mount the necessary file systems with a
  non-existent or incomplete /etc/fstab file and without the root=
  kernel command line option.

DPS is already implemented in systemd-gpt-auto-generator [2], which,
when embedded in an initrd, indeed allows automatic detection of the
root filesystem through its partition type UUID.

This series adds root discovery directly into the kernel so that people
who are not using an initrd can still benefit from it.

The scope is deliberately limited to block devices that the kernel can
already mount through the root= parameter. Other DPS features, such as
setting up LUKS-encrypted partitions, mounting partitions other than
root or container setup, remain userspace responsibilities, with no
future plan to implement them in the kernel. The intended usage is
thus a hybrid approach in which the kernel DPS only mounts the root
partition and leaves the remaining setup to userspace (either with DPS
or with a classic fstab), just as it does today when root= specifies
the root device.

The benefit is being able to boot a kernel with no accompanying
bootloader configuration: no root= parameter and no initramfs. The root
partition is identified from the existing on-disk metadata instead.

This is useful for booting a kernel manually, for example from the edk2
file browser, or recovering from a lost or corrupted bootloader
configuration without having to supply the correct root= argument or
load an initrd from the grub shell. Finally, it allows systems that
otherwise need no initrd to discover their root partition through DPS
without introducing an early userspace environment solely for that
lookup.

The implementation follows these rules:

  - GPT partition type UUIDs are used for automatic discovery policy
    only. No root=PARTTYPEUUID=xxx cmdline option or similar syntax is
    added.

  - An initramfs providing an early userspace init, a root= command-line
    option, or a root device supplied by the boot loader takes
    precedence. Existing working boot configurations therefore retain
    their current behaviour. Automatic discovery triggers only when
    booting without any of these, where the kernel would otherwise panic
    because no root device was specified.

  - As required by DPS, discovery is restricted to the disk containing
    the active EFI System Partition, identified through the
    LoaderDevicePartUUID EFI variable. This avoids selecting a root
    partition on another disk, such as a potentially malicious USB thumb
    drive.

  - If several eligible partitions have the selected type, the first
    match in block-device enumeration order is used.

  - The native architecture's root partition type takes precedence.
    Where the kernel supports compatible 32-bit userspace, its root
    partition type is accepted as a fallback.

  - Partitions carrying the DPS no-auto attribute are excluded.

  - The DPS read-only attribute is intentionally not enforced. The
    kernel already mounts the root filesystem read-only by default and
    if the command line requests rw, it takes precedence over the DPS
    attribute. User space remains responsible for deciding whether a
    discovered root should later be remounted read-write based on DPS
    metadata and local policy.

Patch 1 retains GPT partition type UUIDs in partition metadata for early
block lookup.

Patch 2 defines the architecture-specific DPS root partition type UUIDs
and the derived DPS_ROOT_AUTO_DISCOVERY symbol in Kconfig.

Patch 3 factors out lookup_root_device() so initial root lookup and
rootwait retries share the same lookup policy.

Patch 4 implements DPS root discovery through early_lookup_dps_root()
and integrates it into the root mount path.

Patch 5 excludes partitions marked no-auto.

Patch 6 adds the compatible 32-bit root partition type UUID as a
fallback when no partition with the native type UUID can be found.

Finally, patch 7 documents automatic root discovery.

Tested with the Linux EFI stub [3] and with GRUB [4], which both expose
the LoaderDevicePartUUID EFI variable.

[1] The Discoverable Partitions Specification (DPS)
Link: https://uapi-group.org/specifications/specs/discoverable_partitions_specification/

[2] systemd-gpt-auto-generator
Link: https://www.freedesktop.org/software/systemd/man/latest/systemd-gpt-auto-generator.html

[3] commit 0f7d63d9a725 ("efi/libstub: add initial Boot Loader Interface
    support")
Link: https://git.kernel.org/torvalds/c/0f7d63d9a725

[4] GRUB -- §16.20 bli
Link: https://www.gnu.org/software/grub/manual/grub/html_node/bli_005fmodule.html

Signed-off-by: Vincent Mailhol <mailhol@kernel.org>
---
Changes in v2:

  - Remove all architectures which do not have CONFIG_EFI.

  - Replace the per-architecture UUID headers with Kconfig definitions.

  - Move most of the DPS lookup logic to block/early-lookup.c.

  - Bail out if ROOT_DEV already exists.

  - Hold the disk's open_mutex during lookup so partition scanning
    finishes before reporting -ENODEV. This is a prerequisite for the
    next two changes.

  - Do an early abort when early_lookup_dps_root() returns -ENODEV.

  - Add the secondary partition type UUID as a fallback.

  - Small tweaks in log messages.

  - Documentation is updated accordingly.

Link to v1: https://lore.kernel.org/r/20260615-discoverable-root_partitions-v1-0-39c78fac42e2@kernel.org

---
Vincent Mailhol (7):
      block: store GPT partition type UUID
      init: add DPS root partition type UUID definitions
      init: factor out root device lookup into lookup_root_device()
      init: discover root by DPS partition type UUID
      block: skip partitions with DPS no-auto GPT attribute
      init: add secondary DPS root partition type UUID
      docs: document discoverable root partitions

 Documentation/admin-guide/discoverable-root.rst |  40 ++++++++
 Documentation/admin-guide/index.rst             |   1 +
 Documentation/admin-guide/kernel-parameters.txt |   5 +
 block/early-lookup.c                            | 119 +++++++++++++++++++++++-
 block/partitions/efi.c                          |   2 +
 include/linux/blkdev.h                          |  15 +++
 init/Kconfig                                    |  21 +++++
 init/do_mounts.c                                |  44 +++++++--
 8 files changed, 234 insertions(+), 13 deletions(-)
---
base-commit: 21a7f44fd0765fcc5194130b28767786eba1d1e7
change-id: 20260611-discoverable-root_partitions-bdacbada570d

Best regards,
--  
Vincent Mailhol <mailhol@kernel.org>
```
