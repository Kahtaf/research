# ASUS SD media-flag probe

Question: does correcting the MMC block media flag precondition allow the pinned Linux 4.9 PID1 probe to produce a fresh PROBE.TXT?

Status: offline candidate built; three focused mock groups, unchanged package/layout checks and local PLAN_ONLY passed. No physical boot or readiness claim. The previous physical trial returned healthy stock Android without PROBE.TXT, which does not establish whether Linux booted.

The pinned kernel leaves GENHD_FL_REMOVABLE unset, so the exact precondition is now removable=0. All other card identity, marker, RO-to-RW, O_EXCL, bounded I/O and 60-second reboot behavior is preserved. Run UUID and PROBE.ID bytes remain dbbb6afb-dd70-4c35-961e-9c977d7164a8 followed by LF. Parent alone establishes report absence before its next physical trial; no card rewrite is required for the marker.

Outputs: SOURCE.diff, source/init.c, source/install.py, artifacts/candidate.img, evidence/manifest.json, evidence/build-log.json and evidence/install-plan.json. Padded p10 stays in /srv/android/asus-sd-media-flag-probe-20261107/artifacts/candidate.p10.raw.

Continuation: owner alone handles physical preparation, flashing and trial. scripts/local_driver.py uses the existing fixed SSH helper with this new owned prefix. Do not rebuild the kernel or Android. Installer defaults to PLAN_ONLY; its --execute command is for the parent only after their hardware checks.

Candidate: 8044544 bytes, SHA-256 `999a575cc3dcb20b92f45a8281de19d1d452ad304836b5dded93422aca9d2510`. Full padded p10: 16740352 bytes, SHA-256 `7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09`.
