---
title: [PATCH 0/6] rteval: multi-stressor support plus stressng and test fixes
list: linux-rt-users
message_id: cover.1795478784.git.jkacur@redhat.com
link: https://lore.kernel.org/linux-rt-users/cover.1795478784.git.jkacur@redhat.com/
---

# [PATCH 0/6] rteval: multi-stressor support plus stressng and test fixes

来源：[https://lore.kernel.org/linux-rt-users/cover.1795478784.git.jkacur@redhat.com/](https://lore.kernel.org/linux-rt-users/cover.1795478784.git.jkacur@redhat.com/)

```
Applied to the rteval tree: Sana's multi-stressor support (v6), class-level
tests for the stressng opt-out and arg building, a docstring fix, and three test
robustness fixes -- making the core-sharing tests reproducible on hosts without
SMT, and making the cpuset tests select usable CPUs from cpuset.cpus.effective
instead of hardcoding CPUs that another isolated partition (e.g. intel_lpmd's)
may hold. Posting the series for the archive.

John Kacur (5):
  rteval: Test stressng opt-out and arg building
  rteval: Fix validate_stressors() docstring Raises claim
  rteval: Make core-sharing tests independent of host SMT topology
  rteval: Skip cpuset partition tests when CPUs are not cgroup-usable
  rteval: Pick cpuset integration-test CPUs from cpuset.cpus.effective

Sana Sharma (1):
  rteval: Add multi stressor support

 rteval/modules/__init__.py            |   4 +-
 rteval/modules/loads/stressng.py      |  81 ++++++++++++----
 tests/cpusets/test-cpusets.sh         |  65 +++++++++----
 tests/test_core_sharing_validation.py |  24 +++++
 tests/test_cpusetmanager.py           |  39 ++++++++
 tests/test_stressng.py                | 132 +++++++++++++++++++++++++-
 6 files changed, 309 insertions(+), 36 deletions(-)

-- 
2.56.1
```
