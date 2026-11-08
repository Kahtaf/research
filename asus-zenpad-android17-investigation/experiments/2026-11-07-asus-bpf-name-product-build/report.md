# Integrated BPF program-name SYSTEM build

Status: completed. One ordinary native `m -j8 systemimage` exited 0 at 2026-11-07T16:12:42.950190+00:00, wrapper exit 0, timeout false. Lunch was the prior successful `lineage_p00a-trunk_staging-userdebug`. Soft/hard RLIMIT_AS were both unlimited. The original exclusive nonblocking flock inode 15018964 was held continuously from exact source application through native execution and final artifact capture. Total elapsed through final capture: 484.746 seconds. No native retry occurred.

Only active source change: `/srv/android/lineage24/system/bpf/loader/Loader.cpp`. The exact patch SHA256 `e442a96373a2a9a7ec16d59f13315997487935bd074c29f5369a216e15d6993f` was applied once from preimage `4795e5bb1d46187f1aa858ba0703185ff9309dcd6d4fa97f2860b12b357f93b7` to postimage `bb8288818619d492a79fe997c902dc9b64fa67f1f04bff4afb2b047b4511dccf`, rechecked before final capture. The change only guards the diagnostic program name with measured `kernelVer >= KVER(4, 15, 0)`.

Actual native output logged compilation of Loader.cpp, library link/strip/copy/install, dependent bpfloader rebuild and SYSTEM image packaging. The installed native library and raw-image library bytes are identical:

- Installed: `/srv/android/lineage24/out/target/product/p00a/system/lib64/libbpf_android.so`
- Compiled: `/srv/android/lineage24/out/soong/.intermediates/system/bpf/loader/libbpf_android/android_arm64_armv8-a_shared/libbpf_android.so`
- Bytes: 56960
- SHA256: `380d0d96572c25d82a45eda9c7305fa5866ec722803a33396804c97223cc1e44`

The previous installed library was `b40bd6f4d6677484a8a83d9ceeecdc59724d3c80ee8d2772678060c618050183`. This ordinary product build's library hash differs from the isolated runtime-qualified candidate `682ed7fd0c69bcf0567d81c4d0d43314fce1c0205172f6a1dd9c263a97c7389e`. No binary-equivalence investigation or additional runtime claim was made; exact source integration and actual native/installed identities are recorded.

## Artifacts retained on VM

- Sole raw SYSTEM: `/srv/android/asus-bpf-name-product-build-20261107/system-partition.raw`, 3753902080 bytes, mode 0444, SHA256 `fa41395749229849344b216a8fa55de3c0a9fd029bc90f05543f6ba0cc8550f5`.
- Native sparse SYSTEM: `/srv/android/lineage24/out/target/product/p00a/system.img`, 2583089972 bytes, SHA256 `36881e46852cb73a6e1954425294e4d76705456b12dfbc3b0bba2b3762278ee6`. Expanded size is exactly 3753902080 bytes.
- Public chunk table: `/srv/android/asus-bpf-name-product-build-20261107/evidence/system-1MiB-chunks.tsv`, 316470 bytes, SHA256 `363d0679786262278ed573ab472810919e26abdb0a606ccebdfa07450dc7c5c6`. Columns: index, byte offset, bytes, SHA256. 3580 chunks at 1 MiB, final chunk may be shorter. Mac copy: `evidence/system-1MiB-chunks.tsv` with transfer hash verified.
- Full build log: `/srv/android/asus-bpf-name-product-build-20261107/logs/native.log`, SHA256 `0e92be418ea98c8c61f93f26b9db5226e52f3cb8d1127a4553c5995fb0bac9e7`.
- Machine-readable result: `/srv/android/asus-bpf-name-product-build-20261107/evidence/final-report.json`, also copied locally.

One raw was fully materialized directly from native sparse SYSTEM; all zero ranges were written. Whole-image and chunk hashes were computed in that same output pass. No expanded temporary image, duplicate raw copy, old raw rehash, or historical cache attestation was performed.

Minimal checks passed: exact source postimage; changed compiled/installed/final-image libbpf_android identity; `ro.secure=1`, `ro.debuggable=1`, `ro.adb.secure=1` in actual property files matched into raw SYSTEM; ext4 916480 blocks × 4096 bytes equals the expected 3753902080-byte partition. GMS APEX, Phonesky and GoogleServicesFramework containers match the earlier public artifact hashes in staging and final ext4. This is a three-container retention check; the broad Google suite was not rerun. Existing read-only image/installed-byte helpers were reused directly; the full historical host validator was not invoked or weakened.

Prior readonly SYSTEM `/srv/android/asus-radio-trigger-build-r4/system-partition.raw` (published SHA256 `fff09d5ab4e0ca301786830d133106152c4c0aca15a2c49166c28827aa5e3f79`), prior packaged BOOT `/srv/android/asus-radio-trigger-build-r4/checks/r3/UNTESTED-combined-MTKBOOT.img` (9242624 bytes, published SHA256 `784d4dc565e7742ea607683d2a67d1fdb066764bddfa369895cbaaf6f048b435`), and native `boot.img` retained identical device/inode/size/mode/mtime/ctime metadata across this locked build. They were not rebuilt, rewritten, copied or rehashed.

No new tests, Android startup, HWC investigation, kernel build, subagents, device/card/ADB/root-helper work, private factory/calibration/DATA/manifest access, other-owner process inspection/signals, or cloud lifecycle changes occurred. Ordinary build-generated outputs changed through the requested native command. Existing prior artifacts and failure receipts were preserved. Hardware kernel combination remains pending with the independent reset worker; no complete-framework or hardware acceptance is established.

Continuation: parent consumes this SYSTEM identity and public chunk table, joins its independently qualified physical kernel reset result, and owns any subsequent incremental card update. Do not automatically rerun native build or materialize another raw. Large artifacts remain on the VM.
