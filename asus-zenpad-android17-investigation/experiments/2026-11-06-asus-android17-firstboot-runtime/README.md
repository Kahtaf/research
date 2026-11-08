# ASUS SDK37 first-boot runtime

Question: Can the genuine product SELinux/init, software Keymaster/keystore,
APEX activation and authenticated adbd chain run on the matching Linux 4.9
virtual kernel before physical flashing?

Status: In progress. Runtime qualification, not physical hardware proof.

Outputs: `source/` reproducible fixture scripts, `evidence/` immutable input
manifests and runtime logs, `stagedpatches/` fixes for later parent integration.
Remote ownership: `/srv/android/asus-firstboot-runtime` only. Inputs are read-only
copies; active AOSP and other experiments must remain untouched.

Continuation: Read `report.md` and latest run evidence before continuing. Use
new numbered run directories. QEMU is bounded to one CPU and at most 2 GiB;
any isolated compile is serial. No physical device/ADB/USB, cloud lifecycle,
calibration, personal userdata or existing private ADB keys are in scope.
Fresh disposable legacy ext4 models clean internal data, shipping API 23.
