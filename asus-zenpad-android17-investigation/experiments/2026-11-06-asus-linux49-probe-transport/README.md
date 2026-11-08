# Exact P00A49PROBE recovery transport

**R2 INSTALL QUARANTINED.** Subsequent exact LK tracing proved its explicit
initrd token points 512 bytes into the relocated payload. The install CLI now
refuses this image. Historical tests and commands below describe the earlier
handoff; they are not current execution instructions. Corrected artifact and
evidence: `../2026-11-06-asus-linux49-probe-initrd-fix/README.md`.

Question: can the frozen combined Linux 4.9 RAM-only recovery probe r2 be staged,
written and fully verified over the fixed authenticated Wi-Fi transport, with a
bounded exact stock inverse and fresh USB run binding?

Status: implemented and tested offline. **32 test methods pass. No device contact,
flash, root-helper execution, physical boot, or hardware readiness is claimed.**
Parent review and nearby physical fallback remain required before the first 4.9
boot. The user's expected return time is not proof of their presence.

Important outputs:

- `source/probe_transport.py`: the only parent entry point for this profile;
  default PLAN_ONLY, exact frozen inputs, supervision gates, journal adapter.
- `source/recovery_control.py`: pinned stock transport, with only a distinct
  staging-directory constant changed. Its stock-kernel validator is unchanged.
- `profile.json`: exact component/provenance profile derived from the independent
  review. Its static provenance is not live approval.
- `COMMANDS.md`: concrete parent PLAN/verify/install/restore/readback/finalize
  sequence and the final code/profile hashes to review.
- `REPORT.md`: implementation evidence, scope and remaining physical gates.
- `evidence/base.diff`, `evidence/implementation.diff`,
  `evidence/source-receipts.json`, `evidence/source-preservation.json`,
  `evidence/code-receipt.json`, `evidence/verify-local.json`.
- `tests/test_transport.py`, `evidence/offline-tests.{txt,json}`: deterministic
  in-memory transport/root/block emulation with actual process creation forbidden.

Continuation: read REPORT.md and inspect the implementation diff; repeat the
commands below; review the exact command/profile/code inputs in COMMANDS.md.
Parent alone may subsequently execute, truthfully attesting current supervision
and physical fallback. Freeze these source files and the observer for the entire
run. Start the observer while stock Android is present, using the same fresh pin
and UUID. No command here enters recovery, reboots, changes boot mode, or writes
BCB/para. Parent retains responsibility for manual entry and physical return.

Run from this folder:

```sh
python3 -B tests/test_transport.py
python3 -B source/probe_transport.py verify-local
python3 -B source/probe_transport.py plan
python3 -B source/probe_transport.py install
python3 -B source/probe_transport.py restore
```

All five commands above are entirely offline. `--execute` is never implied.

The only writable partition is `/dev/block/mmcblk0p10` (16,740,352 bytes,
179:10, start 160184, 32696 sectors of 512 bytes). Image transfer uses only
`IP_REDACTED:5555`; DEVICE_SERIAL_REDACTED is independently checked as hardware serial.
Every privileged operation keeps the inherited alias/node/geometry guards and
pinned helper's Enforcing-before/after checks. USB preflight is read-only,
physical-topology pinned, and addressed by current transport ID. USB and Wi-Fi
must both remain healthy; there is no fallback, discovery, ADB-server restart,
endpoint reconnection, mode selection or Wi-Fi re-enablement in this tool.

Fresh per-run staging is under
`/data/local/tmp/asus-linux49-probe-transport/<uuid>-<action>`. Complete staged
bytes are pulled and compared before writing; complete p10 bytes are pulled
afterward. The existing recovery transports' advisory mutation lock is reused
unchanged. Parent must exclude any competing mutation that does not honor it.

One candidate attempt and at most one stock inverse are allowed per run. A known
failed install may perform that inverse only while stock health is confirmed.
An already-stock restore does no block write. Uncertain transport stops without
retry, cleanup or an inverse. Phase directories cannot be reused; failed,
interrupted or uncertain sessions require parent assessment, not a new retry
flag. No cleanup/recovery permission is inferred from a successful local plan.

`restore` can run after stock is regained even if diagnostics failed: restoring
stock does not require a successful diagnostic report. `readback` performs an
additional read-only capture when needed. Finalization requires a clean actual
post-return restore/readback journal, the installed run's original observer pin,
a valid report, observed stock return, and fresh current USB stock checks. It
accepts **no arbitrary readback-file argument**. A new filename, timestamp or
stock backup hash is insufficient. Local journals still are host evidence, not
a hardware signature or proof that a person is nearby.

Final outcomes remain separate: `report_collected`,
`diagnostic_requirements_passed`, `stock_returned`, and
`stock_recovery_readback_verified`. `hardware_ready` is always false. Optional
unavailable measurements and unverified directory listings retain the unchanged
observer's semantics. Full Android 17 installation is outside this transport.
