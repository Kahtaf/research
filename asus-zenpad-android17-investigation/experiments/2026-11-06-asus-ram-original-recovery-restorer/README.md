# Fixed RAM original recovery restorer

Question: restore exact original p10 after SYSTEM/BOOT inverse without relying
on functioning Android userdata?

Status: real implementation, ARM64 build and offline verification complete.
The candidate is **unarmed, unexecuted and not physically commissioned**.
No device access, arming approval or physical GO occurred.

Start with [REPORT.md](REPORT.md), [HANDOFF.json](HANDOFF.json) and
[PROTOCOL.md](PROTOCOL.md). Exact source/payload/policy/image pins are in
[SOURCE_PINS.json](SOURCE_PINS.json), [ARTIFACTS.json](ARTIFACTS.json) and
[the unapproved contract](artifacts/candidate/session-contract.UNAPPROVED.json).

Outputs include the fixed production core and isolated SELinux helper,
durable host exchange, verified original recovery payload, static AArch64
binaries, compiled policy/contexts and `artifacts/candidate/UNARMED.img` plus
its complete zero-padded p10 file. Tests cover 24 core cases, 16 protocol/host
cases, 5 receipt/source cases and 24 existing RSC1 regressions. Policy/context,
independent layout, actual ARM64 archive extraction and full byte reproduction
checks also pass. None proves physical rescue boot or eMMC durability.

Continuation: parent reviews the source and explicit external full-image trust
boundary, then separately decides whether to produce a newly bound STOCK-only
operational image. The delivered zero-record artifact and host refuse use.
Future full-OS profiles remain refused until separately bound. All live device,
USB/ADB/root/reboot/flashing/reset and commissioning decisions belong to the
parent. See [BUILD.md](BUILD.md) for offline reproduction and verification.
