# Parent review and later commands

No target command has been run by this worker. Candidate package and exact profile are complete, the VM is TERMINATED, and the same experiment's first physical trial is still pending. No affirmative physical GO is asserted here.

Review pins and preservation receipts first. The installer is [source/install.py](source/install.py), based on the current battery-uevent installer. Common execute(), Transport, Guard, inherited stock/root/identity/uncertainty/readback readers and adapters remain unchanged. The added exact minimal-profile admission is outside the common mutation path; inspect [install.diff](source/install.diff). Only the owner-supplied current full-p10 preimage was appended.

Parent's real PLAN command, after reviewing the package:

```sh
python3 -B 2026-11-08-asus-minimal-platform-build-r3/source/install.py
```

The worker ran one isolated main() PLAN with a pinned public original-image header template and fixed public code readers substituted only in memory. This did not validate private stock backup/root dependency chains or a fresh device identity/preimage. The delivered command above retains those real readers. A failure is a stop, not permission to bypass them.

Only when the parent separately owns and authorizes the physical installation phase, the existing installer entry point is:

```sh
python3 -B 2026-11-08-asus-minimal-platform-build-r3/source/install.py --execute
```

It performs the inherited guarded recovery-only operation; it does not reboot. Parent owns all subsequent recovery-entry, evidence collection and independently verified normal-stock return. No BOOT/SYSTEM/DATA action is admitted. Current physical full p10 was supplied as `d78e6ddd7f4a555201515df3aef6d8d7f15203c20e3b8d201ea7eb2f4c5df081`, not newly read by this worker.

The one unchanged helper's contract:

1. RAM initramfs contains only static /init plus /dev and /proc. PID1 creates /dev/kmsg and mounts proc only. No udev, sysfs, USB reporter, block write or storage mount.
2. Actual uname; SCHED_OTHER policy 0, priority 0, nice 0; proc mounted before the one-online-CPU check. No scheduler setters/FIFO.
3. Exactly 2,000,000 volatile unsigned iterations and checksum, with no logging or clock read inside compute. Expected state `0x2093acf8`, checksum `4296231513146560`.
4. Five one-shot nominal-one-second alarms, actual flag-only SIGALRM handler and sigsuspend returns. Per-cycle messages before/after include strictly parsed/summed unique CPU0 GIC PPI29/30 counts and two direct SYS_clock_gettime observations. Each IRQ total and monotonic observation must grow; no walltime or counter-rate calibration.
5. Success or clear error reports then requests normal reboot. Stalls or failed timer delivery have no guaranteed alarm bound; eventual owner manual Power fallback remains accepted.

Preserve the original complete raw bytes of stock `/proc/last_kmsg`. This decoder recognizes exactly its known `ram console header, hw_status: N, fiq step N.\n` framing; it does not trim arbitrary transport output or accept last_kmsg2/raw-corruption framing. It reads the file without rewriting it.

After fresh raw and separate stock-return evidence exist:

```sh
python3 -B 2026-11-08-asus-minimal-platform-build-r3/scripts/decode.py \
  /absolute/path/to/original-complete-last_kmsg.bin \
  --parent-attestation /absolute/path/to/completed-parent-attestation.json
```

Copy [the attestation template](source/parent-attestation.template.json) and fill it from actual evidence. Bind the exact new full-p10 pin and SHA of the unmodified raw capture; supply the capture/completeness reference and actual retained geometry (log_start 0, exact console payload log_size and capacity with size strictly below capacity). Do not guess capacity from a truncated capture. Supply canonical different pre-trial/post-trial stock boot IDs and a separate reference proving fresh normal-stock return. These are explicitly parent attestations, not things the offline decoder can independently verify.

Acceptance requires one exact fresh entry tag, matching helper UUID and actual compiled uname, normal scheduler, the helper's successful one-CPU gate, true expected compute result, all five ordered before/return pairs with IRQ/monotonic growth, and success/normal-reboot request plus separately attested fresh stock return. Missing stages, mixed/stale identity, malformed framing, saturation, truncation, wrong checksum, incomplete raw/freshness or unproved stock return is UNKNOWN. The helper's one-CPU evidence is its successful bound sysconf gate and strict CPU0 IRQ parser; it does not emit a separate invented CPU-count record.

Synthetic controls under evidence/ are marked SYNTHETIC. They are not target data, physical retention proof, calibrated timing or protection qualification. No actual raw target content was read here.

A successful trial supports functional RAM compute/timer liveness in this exact retained-closure configuration. It does not qualify hardware protection, storage/fullOS readiness, or uniquely identify the previous stall's cause. Negative/ambiguous ends this attempt for parent reassessment, with no automatic runtime/config/build/trial variant.
