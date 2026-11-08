# Fitted camera driver identification

Question: which camera drivers has stock Android actually selected on this ASUS?

Status: two guarded read-only cached metadata reads identify main ov5670mipiraw and sub ov2680mipiraw. No camera activation, frames, OTP or private calibration access. No new-kernel/HAL3 qualification.

Important outputs: evidence/identification.json, live-read.json, source-pins.json; inputs contain the exact public OEM kernel interfaces. REPORT.md explains the source and limits.

Continuation: qualify OEM metadata dispatch for these exact selected drivers; preserve ABI/kernel/graphics blockers and physical test gates. This is not an Android17 camera bring-up result.
