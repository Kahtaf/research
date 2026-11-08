# Cold devkmsg write boundary

Question: which admitted PID1 devkmsg entry/LOG/return boundaries are captured with the frozen final-only helper?

Status: **one candidate implemented and packaged; STOP**. One incremental kernel build, zero helper compiles, one isolated PLAN. Focused source/ELF, preservation and parser controls passed. No device/ADB/private target access, install, reboot or physical trial. Exact VM verified TERMINATED; owned SSH master closed.

Outputs: [handoff](output/HANDOFF.md), [candidate](artifacts/candidate.img), [fullp10](artifacts/candidate.p10.raw), [source diff](source/changes.patch), [source/ELF proof](evidence/scoped-proof.md), [pins and parent commands](evidence/handoff.json), [checks](evidence/focused-checks.json), [decoder](scripts/decode_boundary.py).

Candidate SHA256 `448f4a9c528608326cce8846968fa2971bd30bd0e9225f062ba378aefa4a51d1`. Fullp10 SHA256 `d07c38333018f7b9cde03ac87bec79928ee934bdbf29332fa55841f7d5157310`. Fresh kernel `e7acab50-e05a-4684-8e5a-c352f025564b`/format1; helper and control reused honestly. ENTIRE wrapped ramdisk/helper, config, DT, short bootargs and initrd bounds preserved.

Continuation: parent owns exact installed fullp10/new stock boot/complete-console binding and any separately authorized single trial. Report captured boundaries and calibration separately; missing records remain UNKNOWN. WRET is before C return, not userspace resumption. No CPU-hang/reporting-fault verdict, storage advance, automatic fix or next candidate.

Build note: compile succeeded; post-build cross-GDB inspection was unavailable. Original failure receipt preserved, read-only nm/objdump qualification passed, no rebuild. See evidence/kernel-build-outcome.json.
