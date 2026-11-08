# Parent handoff

Offline build completed. No card/device access or physical readiness claim. The kernel was reused unchanged; exactly one serial ARM64 init compile ran. Existing three mock groups and package/layout checks passed, and local installer PLAN_ONLY completed with device_contacted=false.

Production patch: source/init.c changes the exact mmcblk1/removable precondition from 1 LF to 0 LF. Every other init byte is unchanged. SOURCE.diff includes the small mock fixture update; INSTALL.diff shows the installer specialization. execute() and Transport are byte-identical to the working installer; source/adb and legacy_adb.py are byte-identical copies, including the adb shim's existing absolute legacy adapter path. The previous full780053 preimage is explicitly allowed alongside the existing fixed allowlist. No writer or policy was replaced.

Run UUID: dbbb6afb-dd70-4c35-961e-9c977d7164a8. PROBE.ID remains exactly that ASCII UUID followed by LF (37 bytes). Parent establishes PROBE.TXT absence immediately before its next trial. A fresh matching PID1 uname report is physical evidence; absent report remains inconclusive about Linux boot. The old physical trial returned healthy stock Android without a report before or after, and did not prove a Linux boot.

Candidate: `/OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-sd-media-flag-probe/artifacts/candidate.img`

Image bytes: 8044544

Image SHA-256: `999a575cc3dcb20b92f45a8281de19d1d452ad304836b5dded93422aca9d2510`

Full p10 bytes: 16740352

Full p10 SHA-256: `7161898f7858c5eb2887a4589fce5a62d4b2d556e1413e36e4e53c3cd8431b09`

VM padded p10: `/srv/android/asus-sd-media-flag-probe-20261107/artifacts/candidate.p10.raw`

Exact parent install command (not run by this implementation agent; installer itself does not reboot):

```sh
/opt/homebrew/opt/python@3.13/bin/python3.13 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-sd-media-flag-probe/source/install.py --execute
```

PLAN command (already run successfully):

```sh
/opt/homebrew/opt/python@3.13/bin/python3.13 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-sd-media-flag-probe/source/install.py
```
