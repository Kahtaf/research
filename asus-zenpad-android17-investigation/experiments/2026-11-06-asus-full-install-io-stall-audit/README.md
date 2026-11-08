# Full-install transport stall audit

Question: does the existing full-install host adapter bound a stalled or partial USB message, and are recovery-only pin limits incorrectly imposed on full images?

Finding: the inspected full-install client does not inherit the recovery-deployment180secondpin/600secondcontract. Those are distinct tools. It instead calls blocking os.read/os.write with no built-in message deadlines. Two actual copied-client pipe trials (partial8byteACK and full-pipe1MiBsend) remained blocked until the separate0.3second supervisor terminated its own child. No target, source network, ADB or device was contacted. This demonstrates the need for a finite-I/O wrapper before eventual live full-install use, not a measured hardware timeout.

Outputs: evidence/actual-client-pipe-stalls.json. The existing remote source reader also uses blocking SOURCE1 pipes; keep its preflight and per-chunk reads within explicit caller budgets. Future implementation must preserve protocol bytes, fixed profiles, source-before-target preflight, terminal uncertainty/no retry and full source/target validation. Budget values need later physical qualification; large full-data/whole-hash phases must not inherit small recovery-deployment timing.

Status: source audit and bounded local reproduction complete. No production source, target artifact, execution approval or physical readiness changed.
