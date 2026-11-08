# Exact stock P00A speaker software topology

Question: does the combined Linux4.9 AW8737S GPIO24/mode4 path preserve the stock ASUS P00A/MT8163 speaker path?

Status: **software discrepancy resolved; fitted-topology implementation blocked**. The actual public stock kernel and DT use the internal PMIC speaker plus an ASUS **GPIO28 gate outside CONFIG_MTK_SPEAKER**. The combined binary contains a generic GPIO24 pulse sequence and omits that GPIO28 path. Its exact appended DT also lacks the required AW delay property, making codec init return -EINVAL before registration. No source/config delta is staged, since AW-off alone would not restore stock topology and the fitted component remains unidentified.

Important outputs:

- [Bounded implementation handoff and missing evidence](report/HANDOFF.md).
- [Verified input paths and SHA256 pins](evidence/input-pins.json), [stock boot match](evidence/stock-boot-match.json), and [GPIO ownership](evidence/gpio-ownership.json).
- [Stock actual-byte disassembly](evidence/stock-public-disassembly.txt), [combined actual-byte disassembly](evidence/bmc-disassembly.txt), and [address mapping controls](evidence/address-mapping-controls.json).
- [Five host fragment checks](evidence/host-checks.json), [exact unchanged pre/post config accounting](evidence/config-accounting.json), and [final verification](evidence/final-verification.json).
- [Darwin resource limitations](evidence/darwin-constraints.json) and [why no patch is staged](proposal/NO-DELTA.md).

Continuation: read the handoff first. Supply board-revision/component/wiring evidence and separately authorized active-stock transition evidence before selecting a fitted-topology implementation. Reproduction commands are in the handoff; run sequentially with the existing local public artifacts. Host mocks establish code behavior only. No route qualification, amplitude/calibration/default, integration, physical test or flash GO is provided.

Everything new lives here. Existing artifacts are preserved. No subagents, network/cloud/VM/device/ADB/root/USB/mixer/PCM/GPIO/playback/capture/charging action, private calibration/keys, target/full-kernel build, active source/out mutation or excluded PCM patch work was performed. Darwin cannot enforce Linux CPU affinity or the requested RLIMIT_AS; serial finite work and measured host footprints are documented without a hard-enforcement claim.
