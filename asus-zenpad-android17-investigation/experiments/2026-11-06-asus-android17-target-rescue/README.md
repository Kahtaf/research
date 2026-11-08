# ASUS stock-kernel target rescue

Question: Can the real ARM64 rescue daemon/proxy be delivered in a reproducible stock-kernel recovery with fixed-partition safeguards and a non-authorizing manifest?

Status: **offline implementation and local delivery complete; target unavailable/unarmed pending parent qualifications.** Full OS flashing is not ready. The existing remote fixture `/srv/android/asus-target-rescue`, all retained failures and successful workloads are preserved. No physical device operation occurred.

Start with [REPORT.md](REPORT.md). Important outputs:

- [Write-disabled recovery image](artifacts/candidate-delivery/UNTESTED-target-rescue.img), [full p10-sized artifact](artifacts/candidate-delivery/UNTESTED-target-rescue.p10.raw), and [unapproved session contract](artifacts/candidate-delivery/session-contract.UNAPPROVED.json).
- [Exact artifact hashes](ARTIFACTS.json), [source pins](SOURCE_PINS.json), [checksum inventory](SHA256SUMS), [reproduction commands](BUILD.md).
- [Preferred local stock inverse sources](artifacts/local-stock-inverse.PLAN_ONLY.json), [pending parent review input](artifacts/parent-review.PENDING.json), and [retained cloud inverse inventory](artifacts/stock-inverse.PLAN_ONLY.json). SYSTEM is referenced in the parent's local rollback bundle; no extra 3.75 GB copy was created here.
- [24 passing adapter tests](evidence/adapter-tests-delivery.txt), [policy/context audit](evidence/policy-audit-delivery.json), [ARM64 block test](evidence/qemu-blocks-delivery/result.json), [stock-init integration](evidence/qemu-stock-init-delivery/result.json), [byte reproduction](evidence/reproduction-delivery.json).

Continuation: run `python3 -B scripts/verify_local.py` from this directory. Inspect actual remote job status before any new work; never restart because a conversation ended. Preserve p20 and the pristine userdata source. Private calibration remains local under parent ownership. Keep the new-kernel probe frozen and separate; do not edit other fixtures or active AOSP. Builds max-j2, QEMU1536 MiB/two CPUs. Parent alone qualifies physical transport/descriptors and authorizes any later arming, userdata operation or OS install.
