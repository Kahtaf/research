# ASUS Android 17 clean internal data validation

Question: Does the exact full-size internal p26 ext4 image pass construction checks and actual matching Linux 4.9 mount, durable metadata, direct I/O, APEX backing and reboot persistence?

**Status: PASS for the bounded host and QEMU qualification.** Both guest boots, 136 real APEX material hashes, persistence/direct I/O, clean unmount and post-boot read-only e2fsck passed. Physical flashing and full Android service/policy startup remain parent-owned gates.

Read [REPORT.md](REPORT.md) for commands, scope, rollback evidence and continuation. Important outputs:

- Remote pristine image: `/srv/android/asus-internal-data-validation/artifacts/A17DATA-pristine.raw` — **11,331,268,096 bytes**.
- SHA-256: `1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1`.
- [32 MiB chunk manifest](evidence/image-manifest.json), [1 MiB reference-rescue fragment](evidence/fresh_userdata.reference-1MiB.json), [integration gates](evidence/integration-gates.json).
- [Two-boot result](evidence/runtime-r2/result.json), [boot 1](evidence/runtime-r2/result-1.json), [boot 2](evidence/runtime-r2/result-2.json), [local validation](evidence/local-validation.json).
- [Fixed builder/inspector](source/image.py), [runtime runner](source/run_runtime.py), [guest fixture](source/guest_init.c), [negative tests](source/test_image.py).
- [Correct 4.9 fstab line](source/fstab.internal-data.4.9.in), [comment-only integration patch](source/fstab-comment-update.patch). No active AOSP edits.

All large raw images remain remote. The pristine image is mode 0400 and was never guest-writable; r2/data-qa.raw contains disposable test data and must not be used for provisioning. Every logical raw byte, including sparse zeros and the final 3584 bytes, must be materialized and read back by the parent's qualified rescue. Leave p20 unchanged for the Android17 trial.

Continuation: parent integrates the manifest into its actual qualified rescue protocol, keeps the final 4.9 alias and real late-mount sequence, and owns all target operations. The earlier four-byte stock-footer proposal is not a user-imposed restriction: normal OEM reset affects the whole metadata partition plus data/cache/bookkeeping, and actual stock re-encryption remains a separate unverified runtime step.

For local evidence validation: `python3 -B source/validate_evidence.py`. To repeat QEMU, choose a new unused revision under the new remote fixture (`source/run_runtime.py r3`); it creates another clone. Do not rerun fixed setup/build over completed artifacts or reuse the old prerequisite fixture's original r6 path.

No ADB, USB, tablet/root operations, cloud lifecycle changes, private calibration/device-data reads or uploads, or changes to previous spikes/build trees were performed.
