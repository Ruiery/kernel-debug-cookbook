---
title: [PATCH blktests] block/046: skip with the new XFS read-bounce implementation
list: linux-block
message_id: CAKTh27_iPvKWV8_bLMwwhEZAD+XPXimBdpz4D8iuue8mSh2A=g@mail.gmail.com
link: https://lore.kernel.org/linux-block/CAKTh27_iPvKWV8_bLMwwhEZAD+XPXimBdpz4D8iuue8mSh2A=g@mail.gmail.com/
---

# [PATCH blktests] block/046: skip with the new XFS read-bounce implementation

来源：[https://lore.kernel.org/linux-block/CAKTh27_iPvKWV8_bLMwwhEZAD+XPXimBdpz4D8iuue8mSh2A=g@mail.gmail.com/](https://lore.kernel.org/linux-block/CAKTh27_iPvKWV8_bLMwwhEZAD+XPXimBdpz4D8iuue8mSh2A=g@mail.gmail.com/)

```
block/046 uses a deliberately misaligned one-byte iovec to exercise the
special bvec layout in bio_iov_iter_bounce_read().

The new XFS lazy read-bounce implementation no longer sets
IOMAP_DIO_BOUNCE before extracting the user pages.  The ordinary path now
rejects that iovec with EINVAL, and a later patch removes the legacy helper
entirely.

Detect the per-mount csum/read_bounce interface and mark the test not run
after cleaning up the XFS mount and null_blk device.  This retains the
regression coverage on older kernels without treating the expected EINVAL
as a successful result.

Reported-by: Shin'ichiro Kawasaki <shinichiro.kawasaki@wdc.com>
Link: https://lore.kernel.org/r/arDN1UdZIydNLUjz@shinmob
Link: https://lore.kernel.org/r/20260921082240.GA19833@lst.de
Signed-off-by: 0wnerD1ed <l7z@0b1t.tech>
---
 tests/block/046 | 19 +++++++++++++++++++
 1 file changed, 19 insertions(+)

diff --git a/tests/block/046 b/tests/block/046
index 5f874bc..e97f583 100755
--- a/tests/block/046
+++ b/tests/block/046
@@ -23,6 +23,7 @@ requires() {
 test() {
        local block_size
        local mount_dir="${TMPDIR}/mnt"
+       local read_bounce="/sys/fs/xfs/nullb1/csum/read_bounce"
        local test_file="${mount_dir}/target"

        echo "Running ${TEST_NAME}"
@@ -42,6 +43,24 @@ test() {
                _exit_null_blk
                return
        fi
+
+       # The lazy XFS read-bounce implementation replaced the legacy
block-layer
+       # path whose special bvec layout this test exercises.
+       if [[ -e "${read_bounce}" ]]; then
+               if ! umount "${mount_dir}" >>"${FULL}" 2>&1; then
+                       echo "failed to unmount XFS"
+                       _exit_null_blk
+                       return 1
+               fi
+               rm -rf "${mount_dir}"
+               if ! _exit_null_blk; then
+                       echo "failed to remove null_blk"
+                       return 1
+               fi
+               SKIP_REASONS+=("legacy read-bounce implementation is
not present")
+               return
+       fi
+
        dd if=/dev/zero of="${test_file}" bs=1M count=1 conv=fsync \
                status=none
        block_size=$(blockdev --getss /dev/nullb1)
--
2.54.0
```
