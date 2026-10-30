---
title: [PATCH v1] rteval: Edited documentation for multistressor support
list: linux-rt-users
message_id: auSkiUhcFJAO2-_Y@fedora
link: https://lore.kernel.org/linux-rt-users/auSkiUhcFJAO2-_Y@fedora/
---

# [PATCH v1] rteval: Edited documentation for multistressor support

来源：[https://lore.kernel.org/linux-rt-users/auSkiUhcFJAO2-_Y@fedora/](https://lore.kernel.org/linux-rt-users/auSkiUhcFJAO2-_Y@fedora/)

```
Edited docs/rteval.8 to agree with recent code changes in stress-ng load
module. This is specfically focused on the multistressor support
changes.

Assisted-by: Claude Opus 4.8
Signed-off-by: Sana Sharma <sansshar@redhat.com>
---
 doc/rteval.8 | 35 +++++++++++++++++++++++++++++++----
 1 file changed, 31 insertions(+), 4 deletions(-)

diff --git a/doc/rteval.8 b/doc/rteval.8
index 370bad9..660a0d0 100644
--- a/doc/rteval.8
+++ b/doc/rteval.8
@@ -160,12 +160,21 @@ Source tar ball (default: linux-6.17.7.tar.xz).
 Number of working threads per core (default: 2).
 
 .SS Stress-ng Load Module Options
+The stress-ng load module only runs when at least one stressor is specified via
+\fB\-\-stressng\-stressor\fR or \fB\-\-stressng\-stressors\fR. When it runs, it
+takes over as the exclusive load module (other load modules are not run).
+Stressor names are validated against the output of \fBstress\-ng \-\-stressors\fR.
 .TP
-.B \-\-stressng\-option \fIOPTION\fR
-Stressor specific option.
+.B \-\-stressng\-stressor \fINAME\fR
+Stressor to run. Repeat the flag to run several stressors in parallel
+(e.g., \fB\-\-stressng\-stressor cpu \-\-stressng\-stressor vm\fR).
 .TP
-.B \-\-stressng\-arg \fIARG\fR
-Stressor specific arg.
+.B \-\-stressng\-stressors \fILIST\fR
+Comma-separated list of stressors to run in parallel (e.g., \fIcpu,vm,io\fR).
+.TP
+.B \-\-stressng\-workers \fIN\fR
+Number of workers to start per stressor (default: 0, which starts one worker per
+available CPU).
 .TP
 .B \-\-stressng\-timeout \fIT\fR
 Timeout after T seconds.
@@ -238,6 +247,24 @@ sudo rteval -d 1800 --measurement-module timerlat \\
 .RE
 .fi
 
+.SS Multiple Stress-ng Stressors
+Run several stress-ng stressors in parallel as the system load:
+.PP
+.nf
+.RS
+sudo rteval -d 3600 \\
+       --stressng-stressor cpu --stressng-stressor vm
+.RE
+.fi
+.PP
+The same set of stressors can be given as a comma-separated list:
+.PP
+.nf
+.RS
+sudo rteval -d 3600 --stressng-stressors cpu,vm,io
+.RE
+.fi
+
 .SS Analyze Existing Reports
 Summarize multiple existing XML reports:
 .PP
-- 
2.54.0


-- 
Sana Sharma <sansshar@redhat.com>
```
