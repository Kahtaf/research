# Read-only rescue proof timing

Question: how long does one genuine fixed original-BOOT reconciliation take on the tablet?

Status: host-only measurement tool prepared; physically untested. No device operations, deployment, image writes or new target protocol. The exact rescue candidate remains unapproved for deployment. This tool does not establish that it can boot.

Independent review found no blocking standalone CLI defect. Parent fixed the owned-stream leak on invalid API deadlines and added real socket closure/EOF verification. Six local test methods pass after that fix. The reviewed snapshot and its findings remain preserved in the separate review spike.

`source/measure.py` sends exactly one existing RSC opcode2 request for original BOOT (index1), fixed manifest and full current recovery hash. It requires all16 chunk matches, discards the returned token, closes the stream, and never requests activation. STATUS and opcode6 cannot substitute for this check. The daemon also performs identity and original SYSTEM proofs and two complete recovery reads. Source-derived partition read volume is3,804,123,136bytes, plus identity/GPT overhead. That arithmetic is not a measurement.

Default: `python3 -B source/measure.py` only prints the plan. Actual execution needs a fresh parent-owned authenticated non-PTY rescue connection adapted to an inherited AF_UNIX stream FD, plus a new evidence filename. This spike supplies no device transport, deployment or execute command. Parent must first qualify the exact stock-kernel rescue boot and its labels/domain/identity/aliases/no-swap/mounts/holders and physical return route.

The CLI is subprocess-only; embedding `main()` in a long-lived process is unsupported. Preflight happens before it acquires the inherited socket; a rejected CLI process closes its inherited descriptors on termination. In-process users may call `measure()` directly with a fresh owned socket: it closes that socket on invalid arguments, success and failure. Such callers own input-pin and evidence checks themselves.

Accept a measurement only when the same CLI invocation exits0, its success JSON matches the exact pins, and its evidence ends with the same complete `OBSERVED_MATCH` record. A matching record anywhere in the file is insufficient: completion-fsync failure can leave an intermediate match followed by UNKNOWN, and an interrupted record or failed final/error fsync proves no completion. Lost invocation status stays UNKNOWN even if a visible file appears successful. Preserve all evidence without automatic retry. Evidence setup/hashing/fsync time is outside the measured request/reply interval.

The deadline bounds host observation; it cannot cancel an in-progress target read. Errors, timeout, malformed response or nonmatching chunks stop without any second request or automatic reconnect. A fresh explicit session is a separate parent decision. The target changes connection-local RAM state/token and may clear a stale RAM journal.new; opcode2 writes no partition. Do not describe it as entirely side-effect free.

Continuation: independently review this host tool, then use only after actual rescue commissioning. Record stable boot/run identity, exact source/image/manifest/current-p10 pins, battery/thermal readings before and after, elapsed time and justified repeat/margin policy. A single elapsed measurement cannot qualify double pair proofs, helper handoff/exec, RAM staging, eMMC writes/fsync/durability or the full stock rollback. Timing and execution flags in the rescue host remain unchanged and false. No physical GO is emitted.
