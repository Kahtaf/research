# Final-only normal compute helper

Question: can the preserved normal-policy 2M compute and completion/afterIRQ path publish with the three intermediate writes deleted?

Status: **one final candidate packaged; STOP**. One helper compile, zero kernel builds, one isolated PLAN and focused checks passed. Exact VM verified TERMINATED; owned SSH master closed. No children, device/ADB/private target content access, install or trial.

Important outputs: [parent handoff](output/HANDOFF.md), [exact pins and commands](evidence/handoff.json), [source delta](source/changes.patch), [focused proof](evidence/scoped-proof.md), [focused checks](evidence/focused-checks.json), [packaging/preservation](evidence/packaging-receipt.json), [isolated PLAN limits](evidence/plan-isolation-receipt.json), [decoder](scripts/decode_compute.py).

Candidate: [candidate.img](artifacts/candidate.img), 7,991,296 bytes, SHA256 `f6bdb96f15a1cc23af1f0a2f5d4049cba98fba40472241f291ac1e10a473deaa`.

Full p10: [candidate.p10.raw](artifacts/candidate.p10.raw), 16,740,352 bytes, SHA256 `0bb68dc6cee1a2589906c5e2bcedee398c12a9cde1073b4cc9c8d706807e9df6`.

Fresh control: `342c9034-6b6f-4d95-aa67-9228b0904eb2`. Reused helper `ef56ad88-6904-4452-90a1-3744beaa3c78` and kernel `f53fadc2-5cd5-4c44-b5a3-7a65567c6935` prefixes and kernel profile sparse-fifo-v1 are unchanged and are not fresh proof. Exact clock.path value: `kernel-syscall:syscall(SYS_clock_gettime);vDSO-bypassed;control=342c9034-6b6f-4d95-aa67-9228b0904eb2;loop=pure-compute-normal-final-only`. Completion retains `control=342c9034-6b6f-4d95-aa67-9228b0904eb2 iterations=2000000 checksum=e4ca7075 reason=compute-cap`.

Payload 256,298 bytes ends at `0x4403e92a`, leaving 1,757 bytes under unchanged guard `0x4403f007`. Kernel gzip/raw/wrapper/config and hardware DT are byte-identical to the pinned normal baseline. Supplied current fullp10 `9a836b53aaf66366a93f2f715c73247ae49e889cb4bce4a369655939142c04ad` is appended to installer admissions; not freshly observed here.

Continuation instructions: parent only runs the exact dependency PLAN, execute and decoder commands in [HANDOFF.md](output/HANDOFF.md), obtains fresh physical readback/new stock boot/complete-console evidence and owns its one physical trial. No automatic next build, loop variant or rerun follows this candidate or its result.
