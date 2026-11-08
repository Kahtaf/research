# Exact LK to Linux 4.9 handoff

Question: what does this tablet's exact LK do to the reviewed kernel, appended
DT, compressed ramdisk and final AArch64 entry registers before Linux starts?

Status: initial offline reference capture only. Existing static packaging checks
prove the host image's bytes, but do not yet prove the final bootloader handoff.
No device or bootloader change, runtime claim, or flash authorization.

The exact public LK is SHA-256
`c5b5017ee3efdf018d9b6be7db978f29365c30e60a3fb9173660fda699f7b765`,
matching saved device evidence. Its mapped base is 0x41e00000 after the 512-byte
wrapper. Supporting source: boot-access-audit and custom-boot-path spikes;
reviewed fixed probe: build-continuation/artifacts/probe-r2. Do not substitute
product r3 or change the frozen diagnostic.

Important outputs: `scripts/find_handoff_references.py` and
`evidence/string-reference-candidates.json`. Reference candidates use linear
Thumb decoding and require control-flow verification; strings or candidate
calls alone prove no branch executes.

Continuation: trace the actual recovery loader to common handoff, decompression
and DT selection, initrd wrapper adjustment/properties, cmdline edits and final
kernel address/DT argument. Record exact addresses and assumptions; bound any
emulation with explicit stubs. Distinguish source/static inference from hardware
proof. No ADB, root, device, cloud build or security changes are needed.
