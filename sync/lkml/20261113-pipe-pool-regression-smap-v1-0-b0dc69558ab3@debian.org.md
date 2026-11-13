---
title: [PATCH RFC 0/3] fs/pipe: copy a run of pipe buffers in one user access section
list: linux-block
message_id: 20261113-pipe-pool-regression-smap-v1-0-b0dc69558ab3@debian.org
link: https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-0-b0dc69558ab3@debian.org/
---

# [PATCH RFC 0/3] fs/pipe: copy a run of pipe buffers in one user access section

来源：[https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-0-b0dc69558ab3@debian.org/](https://lore.kernel.org/linux-block/20261113-pipe-pool-regression-smap-v1-0-b0dc69558ab3@debian.org/)

```
anon_pipe_read() opens and closes a user access section for every pipe
buffer it copies, which on x86 is a STAC/CLAC pair per page. Mateusz
suggested [1] doing the copies under one section instead.

Patch 1 splits the STAC/CLAC out of copy_user_generic(), so that its
rep movs body can run inside a caller's user access section.

Patch 2 adds copy_bvecs_to_iter_full(), which copies an array of pages
to an iov_iter, all or nothing, in one section when the destination is
a plain user buffer.

Patch 3 uses it in anon_pipe_read() for up to 16 anonymous buffers that
the read consumes whole.

This is an RFC. A single patch PoC [2] behaved as Mateusz expected but
was "on the uglier side" [3], so the user access part moved out of
fs/pipe.c into lib/iov_iter.c. The main question is whether that helper
is welcome there, or, make the party a bit uglier.

Benchmark wise, see the numbers on the last patch.

[1] https://lore.kernel.org/all/CAGudoHF3de_55YvdztPs7QiYs25u6nPEV=uMOzfr=bWmwof69g@mail.gmail.com/
[2] https://lore.kernel.org/all/avMQxhpHhIPM_6HP@gmail.com/
[3] https://lore.kernel.org/all/CAGudoHFe8XgtKZohfn0Q=EH0EeXozTZq+UPJKN0BEmLnEG2s=Q@mail.gmail.com/

Signed-off-by: Breno Leitao <leitao@debian.org>
---
Breno Leitao (3):
      x86/uaccess: Split the STAC/CLAC out of copy_user_generic()
      iov_iter: add copy_bvecs_to_iter_full()
      fs/pipe: copy a run of anonymous buffers in one user access section

 arch/x86/include/asm/uaccess_64.h | 20 +++++++++++--
 fs/pipe.c                         | 44 +++++++++++++++++++++++++++-
 include/linux/uio.h               |  2 ++
 lib/iov_iter.c                    | 61 +++++++++++++++++++++++++++++++++++++++
 4 files changed, 124 insertions(+), 3 deletions(-)
---
base-commit: 6d582d78fad9d828e575ca0cdcff8ea47a77220b
base-tree: git://git.kernel.org/pub/scm/linux/kernel/git/next/linux-next.git master
change-id: 20261106-pipe-pool-regression-smap-13cc7cd3b482

Best regards,
--  
Breno Leitao <leitao@debian.org>
```
