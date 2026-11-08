# Parent host overlay after independent review

This is an offline host-source revision. It does not change the reviewed target
helper, policy, image, fixed payload, protocol opcodes, either original-pair
proof, any p10 transition scan, or the no-retry behavior. The old delivery and
review remain immutable. No device was contacted.

## R1: publication and replay contract

The schema-2 `attempt.json` is durably UNKNOWN before the first request.
`receipt.json` always retains `outcome=UNKNOWN` and
`publication_accepted=false`. Its separate `device_outcome` may record verified
DONE or SKIPPED. This file describes observation, even after a successful
rename; it never certifies that its own final directory fsync succeeded.

Only a successful live return from `_exchange` yields `outcome=DONE/SKIPPED`
and `publication_accepted=true`, after the file publication returned successfully.
A parent supervisor must act only on that successful invocation result. It
must catch `UnknownOutcome` as terminal UNKNOWN. Inspecting a receipt file,
finding a target DONE, or later observing stock bytes cannot override a known
failed or lost invocation outcome. A process crash between publication and
return remains UNKNOWN. There is deliberately no replay-to-success function.

For interrupted or conflicting records, preserve all files and refuse retry,
reboot or reset based on their presence. Separately authorized read-only target
observation can establish current bytes without retroactively accepting the
lost operation. No additional marker on the same failing storage can guarantee
otherwise. Other parent prerequisites still apply even after a successful live
return; this return does not itself authorize reboot or reset.

The regression injects failure after the successful rename at the fourth fsync,
then makes storage unavailable for the UNKNOWN rewrite. Visible receipt and
durable attempt both remain UNKNOWN, while `device_outcome=DONE` is retained as
evidence. The call raises `UnknownOutcome`, closes the stream and sends no retry.

## R2: phase deadline implementation, physical timing still open

Host deadlines now cover entire phases, including fragmented header/body
receives, rather than restarting a 15-second inactivity interval on each read.
Each phase is bounded by the same hard 600-second operation deadline:

| Phase | Provisional ceiling | Scope |
| --- | ---: | --- |
| handoff | 180 s | Request through first acknowledgement, including both original-pair proofs |
| stage | 15 s per chunk | One RAM chunk send and acknowledgement |
| prepare | 60 s | Sealing and complete preimage proof |
| restore | 120 s | Activation, writes, fsyncs, all transition scans, final reopened readback |

These ceilings are engineering placeholders, not measurements or an asserted
adequate margin. `TIMING_QUALIFIED=False` blocks the public `restore()` entry
before payload access, receipt creation or protocol requests, even if a future
binding sets ARMED. The current copied binding is also still unarmed.

Separately authorized read-only stock commissioning must retain actual elapsed
times, operation/source pins, byte counts, thermal/battery state and sufficient
repeat observations to justify proof-phase limits and margin. The write phase
requires a justified budget followed by explicit physical commissioning; its
first actual write is not already proven. Bind the accepted evidence and exact
phase constants in a later reviewed source/build revision. Do not merely toggle
the qualification flag or treat the modeled delayed response as a benchmark.

The 16-second valid initial response now passes the exact production Python
exchange in a protocol/clock model. Over-limit responses in all four phases and
fragment activity remain UNKNOWN. Phase changes cannot extend the operation
deadline. A timeout cannot stop target block I/O, consume-and-retry a handoff,
or authorize reconnection; all uncertainty handling remains terminal.

## Integration and continuation

Use this host-source overlay only in a separately bound STOCK-only operational
build after the original review's remaining gates. Regenerate whole-image and
external helper pins if any target bytes change. This task does not produce an
operational candidate, physical acceptance, or Android17/full-OS flash approval.

`tests/contract_tests.py` covers publication/deadline regressions locally.
`scripts/replay_remote.py` creates an exclusive Linux fixture once and replays
the revised host against the existing real C session/core test binary and exact
unarmed image/payload. Its immutable source and artifact hashes are recorded.
Native tests use memory storage and local socket pairs, never block devices.
The script refuses an existing fixture; inspect retained evidence rather than
blindly rerunning its creation recipe. No full SYSTEM/data copy is made.
