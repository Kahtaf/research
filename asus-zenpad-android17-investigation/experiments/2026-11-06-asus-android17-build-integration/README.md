# Android 17 full build integration

Question: can the measured/checked main battery kernel and Health integration build with the full SDK 37 ASUS P00A product, graphics and signed Google payload?

Status: integration in progress. Owner of active VM kernel/platform/product and main builds; no physical device, cloud lifecycle or goal operations.

Outputs: scripts, scoped compilation fixes, and compact evidence collected here. Large images remain on the builder. Existing kernel and graphics checkpoints remain preserved.

Continue: read REPORT.md when present and evidence logs. Builder /srv/android/lineage24; kernel /srv/android/asus-android17/kernel-bpf-fd; remote build integration /srv/android/asus-build-integration. Use unique attempt revisions, no overlapping main builds, freeze sources while compiling. Parent now plans clean internal /data after image/rescue verification; no personal-data migration or microSD requirement. Children must not format/mount old FDE. Default fstab remains gated and has no autoformat. Packaging and physical tests prohibit claiming flash readiness.
