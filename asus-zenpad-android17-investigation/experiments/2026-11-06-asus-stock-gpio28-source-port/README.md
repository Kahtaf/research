# UNQUALIFIED P00A GPIO28 stock software-contract source port

Question: restore the public stock GPIO28 gate contract in a future Linux4.9 source candidate while preserving the internal PMIC speaker and excluding generic GPIO24 AW pulses.

Status: **staged and host-verified; UNQUALIFIED, not integrated or built for target**. Checked managed initial-low request, explicit gate On/Off, fault-aware mixer state, shutdown/release and conservative suspend behavior are implemented in owned copies. Parent-owned stock GPIO ownership metadata is pinned. Fitted component identity and active physical routes remain unproven.

Important outputs:

- [Complete handoff, API semantics and remaining gates](report/HANDOFF.md).
- [Kernel source patch](patches/kernel-source.patch) and [future .config patch](patches/resolved-config.patch).
- [Exact pre/post pins](evidence/pre-post-pins.json), [public source/API pins](evidence/input-pins.json), and [patch replay](evidence/patch-replay.json).
- [38 host cases / 984 assertions](evidence/host-results.txt), [API/production extraction](evidence/host-production-extraction.json), [config deltas](evidence/config-deltas.json), [DT/ownership checks](evidence/dt-and-ownership-checks.json), and [Darwin limits](evidence/host-constraints.json).

Continuation: review the handoff and patch against exact preimages. `python3 scripts/run_host.py` verifies the staged copies. Real Kconfig/dtc, ARM64 whole-object/full-kernel builds, board/electrical evidence, active stock-route observations, integration and physical commissioning remain separate gates. HAL routes remain false. No build/image/physical/flash GO or hardware enable approval.

This distinct spike owns all new files. Existing research, source and active/frozen kernels are unchanged. No children, network/cloud/VM, device/ADB/root/USB/mixer/PCM/GPIO/charging/radio action, private calibration/keys, target/full-kernel build, existing source/out changes or excluded PCM patch work occurred.
