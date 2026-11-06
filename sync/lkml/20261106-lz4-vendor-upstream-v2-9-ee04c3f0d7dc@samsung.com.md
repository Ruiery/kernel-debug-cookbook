---
title: [PATCH v2 09/15] arch: boot: put the LZ4 freestanding headers on the decompressor path
list: linux-block
message_id: 20261106-lz4-vendor-upstream-v2-9-ee04c3f0d7dc@samsung.com
link: https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-9-ee04c3f0d7dc@samsung.com/
---

# [PATCH v2 09/15] arch: boot: put the LZ4 freestanding headers on the decompressor path

来源：[https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-9-ee04c3f0d7dc@samsung.com/](https://lore.kernel.org/linux-block/20261106-lz4-vendor-upstream-v2-9-ee04c3f0d7dc@samsung.com/)

```
lib/decompress_unlz4.c pulls lib/lz4/lz4_decompress.c into the pre-boot
decompressor on these five arches. A later patch makes that file include
the vendored LZ4 sources, which include ISO C headers that -nostdinc does
not provide, so put lib/lz4/freestanding on the include path first.

Only the one object that includes decompress_unlz4.c gets it, so the
rest of each boot directory keeps -nostdinc's view.

Signed-off-by: Michal Wilczynski <m.wilczynski@samsung.com>
---
 arch/arm/boot/compressed/Makefile    | 3 +++
 arch/mips/boot/compressed/Makefile   | 4 ++++
 arch/parisc/boot/compressed/Makefile | 3 +++
 arch/s390/boot/Makefile              | 3 +++
 arch/x86/boot/compressed/Makefile    | 3 +++
 5 files changed, 16 insertions(+)

diff --git a/arch/arm/boot/compressed/Makefile b/arch/arm/boot/compressed/Makefile
index e3f550d6285786c8405b16768255af87b4dc8222..713225008aa71e614af8c9c6472fda180354569b 100644
--- a/arch/arm/boot/compressed/Makefile
+++ b/arch/arm/boot/compressed/Makefile
@@ -92,6 +92,9 @@ targets       := vmlinux vmlinux.lds piggy_data piggy.o \
 		 head.o $(OBJS)
 
 KBUILD_CFLAGS += -DDISABLE_BRANCH_PROFILING
+# decompress.c includes decompress_unlz4.c, which builds the vendored LZ4
+# sources; they include a few ISO C headers -nostdinc drops.
+CFLAGS_decompress.o += -I$(srctree)/lib/lz4/freestanding
 
 ccflags-y := -fpic $(call cc-option,-mno-single-pic-base,) -fno-builtin \
 	     -I$(srctree)/scripts/dtc/libfdt -fno-stack-protector \
diff --git a/arch/mips/boot/compressed/Makefile b/arch/mips/boot/compressed/Makefile
index e0b8ec9a9516281933b6cc5b175e82f4013c2f54..48f8a63c54a66826889634a54d3537d735f63512 100644
--- a/arch/mips/boot/compressed/Makefile
+++ b/arch/mips/boot/compressed/Makefile
@@ -30,6 +30,10 @@ endif
 KBUILD_CFLAGS := $(KBUILD_CFLAGS) -D__KERNEL__ -D__DISABLE_EXPORTS \
 	-DBOOT_HEAP_SIZE=$(BOOT_HEAP_SIZE) -D"VMLINUX_LOAD_ADDRESS_ULL=$(VMLINUX_LOAD_ADDRESS)ull"
 
+# decompress.c includes decompress_unlz4.c, which builds the vendored LZ4
+# sources; they include a few ISO C headers -nostdinc drops.
+CFLAGS_decompress.o += -I$(srctree)/lib/lz4/freestanding
+
 KBUILD_AFLAGS := $(KBUILD_AFLAGS) -D__ASSEMBLY__ \
 	-DBOOT_HEAP_SIZE=$(BOOT_HEAP_SIZE) \
 	-DKERNEL_ENTRY=$(VMLINUX_ENTRY_ADDRESS)
diff --git a/arch/parisc/boot/compressed/Makefile b/arch/parisc/boot/compressed/Makefile
index 14eefb5ed5d1d781a4ee0cb2ef61ab86c905cc56..9e82f9d1285f62b164073bdacc0d4a1828d4965c 100644
--- a/arch/parisc/boot/compressed/Makefile
+++ b/arch/parisc/boot/compressed/Makefile
@@ -12,6 +12,9 @@ targets += $(OBJECTS) sizes.h
 
 KBUILD_CFLAGS := -D__KERNEL__ -O2 -DBOOTLOADER
 KBUILD_CFLAGS += -DDISABLE_BRANCH_PROFILING
+# misc.c includes decompress_unlz4.c, which builds the vendored LZ4
+# sources; they include a few ISO C headers -nostdinc drops.
+CFLAGS_misc.o += -I$(srctree)/lib/lz4/freestanding
 KBUILD_CFLAGS += -fno-strict-aliasing
 KBUILD_CFLAGS += $(cflags-y) -fno-delete-null-pointer-checks -fno-builtin-printf
 KBUILD_CFLAGS += -fno-PIE -mno-space-regs -mdisable-fpregs -Os
diff --git a/arch/s390/boot/Makefile b/arch/s390/boot/Makefile
index 10b75e053a6f6bb9083548e8f82796f0aa9a9958..44355051a8c7f96b5c4dab5d110bc8aaf79c8f55 100644
--- a/arch/s390/boot/Makefile
+++ b/arch/s390/boot/Makefile
@@ -21,6 +21,9 @@ KBUILD_AFLAGS := $(filter-out $(CC_FLAGS_MARCH),$(KBUILD_AFLAGS_DECOMPRESSOR))
 KBUILD_CFLAGS := $(filter-out $(CC_FLAGS_MARCH),$(KBUILD_CFLAGS_DECOMPRESSOR))
 KBUILD_AFLAGS += $(CC_FLAGS_MARCH_MINIMUM) -D__DISABLE_EXPORTS
 KBUILD_CFLAGS += $(CC_FLAGS_MARCH_MINIMUM) -D__DISABLE_EXPORTS
+# decompressor.c includes decompress_unlz4.c, which builds the vendored LZ4
+# sources; they include a few ISO C headers -nostdinc drops.
+CFLAGS_decompressor.o += -I$(srctree)/lib/lz4/freestanding
 KBUILD_CFLAGS += $(call cc-option, -Wno-default-const-init-unsafe)
 
 CFLAGS_sclp_early_core.o += -I$(srctree)/drivers/s390/char
diff --git a/arch/x86/boot/compressed/Makefile b/arch/x86/boot/compressed/Makefile
index 06934f9691d6a9d6952532ae5f7d96f5858719dd..328eafcfc35bd14a16bc4ec5472f6c6dc72336a1 100644
--- a/arch/x86/boot/compressed/Makefile
+++ b/arch/x86/boot/compressed/Makefile
@@ -30,6 +30,9 @@ KBUILD_CFLAGS += -fno-strict-aliasing -fPIE
 KBUILD_CFLAGS += -fno-jump-tables
 KBUILD_CFLAGS += -Wundef
 KBUILD_CFLAGS += -DDISABLE_BRANCH_PROFILING
+# misc.c includes decompress_unlz4.c, which builds the vendored LZ4
+# sources; they include a few ISO C headers -nostdinc drops.
+CFLAGS_misc.o += -I$(srctree)/lib/lz4/freestanding
 cflags-$(CONFIG_X86_32) := -march=i386
 cflags-$(CONFIG_X86_64) := -mcmodel=small -mno-red-zone
 KBUILD_CFLAGS += $(cflags-y)

-- 
2.34.1
```
