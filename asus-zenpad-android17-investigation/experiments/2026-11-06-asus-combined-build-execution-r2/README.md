# Combined build execution r2: unlimited native address space

Question: can the ordinary combined build complete after removal of the unrequested native address-space cap?

Status: parent explicitly authorized actual new execution. Exact reviewed launcher patch b1f2a7010d38c60a75f5a9459676fb5518c2e08db2e7c744b67e9272ee2bfa5c applied to a fresh owned driver. VM prefix /srv/android/asus-combined-build-execution-r2. Fresh SSH soft/hard native RLIMIT_AS must both be unlimited and are read back once before launch. No native AS/cgroup memory cap is set. Existing host-only small-check limit is separate.

Sources already integrated and only checked: health71566, namespacee2aa/test00b8, device10/rootMK9eef. No patch reapplication/restoration. Ordinary actual lunch lineage_p00a-trunk_staging-userdebug then m -j4 systemimage bootimage once; original nonblocking lock inode15018964; 45-minute finite supervisor; normal cache, no clean/touch/kernel rebuild/historical sweeps/repeated tests. Failed r1 logs and receipts remain immutable. Preserve old readonly images and stock rollback; at most one new raw after native success. Full images stay on VM.

Continuation: this execution runs to a real terminal result. Native physical/cgroup/kernel OOM is a failure to preserve/report, never grounds for an automatic native retry/source workaround. Reuse the previously scoped minimum critical image/kernel/layout/root/Google/APEX/filter/netd-byte checks; actual VINTF errors remain visible and peripheral completeness is not silently converted to a pass. No device/network-device/private-calibration/cloud lifecycle actions, and no full OS flash GO based only on compilation.

Actual launch: 2026-11-07 05:00:12 UTC, fresh SSH receipt reads soft=-1/hard=-1/unlimited=-1, no driver native limit mutation. Source writes=[]; all already integrated postimages retained. Live owned local exec session35521 awaits terminal status. Never relaunch this consumed r2 attempt. Native job4, original lock15018964, absolute45min bound. See evidence/actual-native-limits-and-launch.json.

Terminal result: SUPERVISOR_DEADLINE_NATIVE_INCOMPLETE after 2681.461 seconds. The driver exited 1; m did not return a normal native exit before the owned group was killed by its finite supervisor. Fresh SSH native AS limits were both unlimited. Soong generation succeeded (17m32.37s); the last Ninja record was 2326/214073. No OOM appeared in this attempt's native log. No native retry, source change, clean, touch, or cache deletion was performed.

Postbuild checks, actual VINTF, raw materialization and MTKBOOT packaging were not reached. No new validated image paths/hashes exist. Failed r1 log/receipt hashes remain exact; both old raw images retain their original readonly inode/size/mtime/mode without a body rehash. Original R9 and all previous failure receipts remain historical failures. No physical/runtime/full-OS flash acceptance.

Outputs: evidence/final-report.json, evidence/final-report-pin.json, evidence/terminal-readback.json, evidence/terminal-supplement.json, evidence/execution-return.json. VM native log: /srv/android/asus-combined-build-execution-r2/logs/native.log; failed receipt: attempt/FAILED.json. This consumed attempt must never be relaunched. Any later execution requires its own explicit instruction and fresh prefix; retain cached out.
