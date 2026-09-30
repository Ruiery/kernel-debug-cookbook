---
title: [PATCH] mm: oom_kill: add trace logs in process_mrelease() system call
list: linux-mm
message_id: 1629106756-20874-1-git-send-email-charante@codeaurora.org
link: https://lore.kernel.org/linux-mm/1629106756-20874-1-git-send-email-charante@codeaurora.org/
---

# [PATCH] mm: oom_kill: add trace logs in process_mrelease() system call

来源：[https://lore.kernel.org/linux-mm/1629106756-20874-1-git-send-email-charante@codeaurora.org/](https://lore.kernel.org/linux-mm/1629106756-20874-1-git-send-email-charante@codeaurora.org/)

```
The process_mrelease() system call[1] is used to release the memory of
a dying process from the context of the caller, which is similar to and
uses the functions of the oom reaper logic. There exists trace logs for
a process when reaped by the oom reaper. Just extend the same to when
done by the process_mrelease() system call.

[1] https://lore.kernel.org/linux-mm/20210809185259.405936-1-surenb@google.com/

Signed-off-by: Charan Teja Reddy <charante@codeaurora.org>
---
 mm/oom_kill.c | 14 +++++++++++++-
 1 file changed, 13 insertions(+), 1 deletion(-)

diff --git a/mm/oom_kill.c b/mm/oom_kill.c
index 431d38c..8f4020a 100644
--- a/mm/oom_kill.c
+++ b/mm/oom_kill.c
@@ -941,7 +941,6 @@ static void __oom_kill_process(struct task_struct *victim, const char *message)
 	mmdrop(mm);
 	put_task_struct(victim);
 }
-#undef K
 
 /*
  * Kill provided task unless it's secured by setting
@@ -1199,8 +1198,18 @@ SYSCALL_DEFINE2(process_mrelease, int, pidfd, unsigned int, flags)
 		ret = -EINTR;
 		goto drop_mm;
 	}
+	trace_start_task_reaping(task->pid);
 	if (!__oom_reap_task_mm(mm))
 		ret = -EAGAIN;
+	if (!ret) {
+		pr_info("process_mrelease: reaped process %d (%s), now anon-rss:%lukB, file-rss:%lukB, shmem-rss:%lukB oom_score_adj:%d\n",
+			task_pid_nr(task), task->comm,
+			K(get_mm_counter(mm, MM_ANONPAGES)),
+			K(get_mm_counter(mm, MM_FILEPAGES)),
+			K(get_mm_counter(mm, MM_SHMEMPAGES)),
+			task->signal->oom_score_adj);
+	}
+	trace_finish_task_reaping(task->pid);
 	mmap_read_unlock(mm);
 
 drop_mm:
@@ -1208,9 +1217,12 @@ SYSCALL_DEFINE2(process_mrelease, int, pidfd, unsigned int, flags)
 put_task:
 	put_task_struct(task);
 put_pid:
+	if (ret && ret != -EAGAIN)
+		trace_skip_task_reaping(pid_vnr(pid));
 	put_pid(pid);
 	return ret;
 #else
 	return -ENOSYS;
 #endif /* CONFIG_MMU */
 }
+#undef K
-- 
QUALCOMM INDIA, on behalf of Qualcomm Innovation Center, Inc. is a
member of the Code Aurora Forum, hosted by The Linux Foundation
```
