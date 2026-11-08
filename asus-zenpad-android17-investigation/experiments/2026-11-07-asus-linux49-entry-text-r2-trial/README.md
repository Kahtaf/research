# Experiment 2: physical Linux4.9 entry text test

Question: does the structurally guarded pre-MMU checkpoint execute and survive the recovery attempt?

Status: preparing one recovery-only trial. Candidate fullp10 f547c8fd3819b01efef6a232197aa5670dcbe332a83edcbc20529b2a07a08e42; fresh tag run95c88f32-9471-4354-9a36-e44e98901a0f. BOOT/SYSTEM/DATA remain intact. Parent has fresh nearby Power fallback confirmation. Continue with exactly one verified installation, one Recovery entry and complete retained-log collection after normal Android returns. Absent tag remains UNKNOWN.


## Physical result

One verified install and one ACKNOWLEDGED recovery entry completed. Android returned automatically to f53fef38-8c1e-40f2-aa9a-1b149cda93a9. No PID1 USB descriptor was observed. Full retained log 523015 bytes SHA256 4ed7b1f37c718d5a9c30519c63206b4ab0a90c964328004e7a348d7c5ba9042a contains neither the fresh UUID nor exact tag. Outcome UNKNOWN_NO_FRESH_ENTRY_TAG. This does not prove nonexecution, guard success or failure. Experiment3 is not admitted. No speculative driver changes follow. Next bounded discriminator: calibrate the same early writer using the known-working stock kernel, with a kernel-origin bounded readback before its stock ring reset, preserving normal reset and RAMUSB fallback.
