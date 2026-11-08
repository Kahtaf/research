# Android 17 first-boot services

Question: can the SDK 37 / shipping API 23 ASUS product advance through real
keystore module-hash delivery, APEX activation and authenticated adbd without
modern hardware KeyMint or touching stock FDE data?

Status: staging complete; **25 offline source/config checks passed**. Actual
compilation and runtime are pending parent integration. No VM mutations/builds,
device operations or changes outside this spike occurred.

Outputs: [report.md](report.md) explains the real software Keymaster 4.0 path,
keystore's existing legacy version gate, first-activation metadata behavior,
integration order and runtime checks. `stagedsource/` selects the existing
platform service, declares HIDL/default, and selects supported post-data APEX
activation. `configsnippets/` includes parent integration additions and a
non-installable external ext4 scratch-data template. No stock-data mount or
format is introduced. `evidence/` contains source captures, hashes, current
builder variable excerpts and validation results.

Continue: read [report.md](report.md), then run `python3 -B scripts/validate.py`.
Parent owns integration, compilation, verified external-data identification,
recovery planning and physical testing. No TEE/hardware-attestation claim,
property spoof, wait bypass or no-op service is used. The final persistent
internal tablet data migration remains unresolved; scratch is a bring-up tool.
