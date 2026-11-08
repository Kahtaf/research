# ASUS P00A_2 main battery measurement port

Question: can Android 17 Health consume truthful main-tablet battery data from
the pinned 4.9 hardware kernel without enabling charging?

Status: bounded measurement patch staged; host and source checks pass. No remote changes, builds, device
operations or charging enablement. This is the permitted bounded measurement
alternative, not a claim of a complete state-of-charge estimator.

The original ASUS source identifies UG31xx as the optional cover (`pack_bat`),
not the main battery. Main battery sensing is MT6323 AUXADC with the in-kernel
MediaTek software gauge and BQ25896 charging. There is no demonstrated main-pad
proprietary fuel-gauge-daemon dependency.

Important outputs:

- `patches/0001-asus-p00a-measured-battery.patch`: pinned 4.9 source patch.
- `staged/`: exact changed source files, including checked PMIC conversion,
  original battery NTC conversion, hardware status and Health property dispatch.
- `scripts/`: source collection, patch generation and host verification.
- `evidence/base/`: selected public source read by SSH at kernel commit
  `717bb3c9e13ce573cfdd2dda856debd27a0fa17f` (not a complete build tree).
- `evidence/remote-source.json`: revision, read-only SSH options, source hashes.
- `REPORT.md`: findings, implemented/compiled/runtime boundaries and exact remaining work.
- `integration/`: apply/build instructions, Health handoff and startup-gate snippet.

Continuation: only the graphics/build owner may apply/build on the VM. Review
this spike's completed report and apply instructions first. Preserve the absent
`asus,allow-battery-charging` DT property. Capacity/current/charge counters remain
unavailable, with explicit errors, until the software estimator is reconciled.
Do not make a full kernel build from this case-insensitive host source snapshot.

Verification: 9,713 host assertions (ASan/UBSan) and 67 source/guard/patch-replay
checks pass. No ARM64 kernel build or hardware test was performed. Actual
Android 17 default aggregate HealthInfo turns unavailable SOC into zero, so
read `integration/HEALTH-HANDOFF.md` before integration. This is diagnostic
measurement support, not a closed full-SOC/Android-Health gate.
