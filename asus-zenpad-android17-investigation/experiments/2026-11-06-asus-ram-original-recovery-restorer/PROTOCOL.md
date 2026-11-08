# Fixed P10R1 terminal operation

This extends framing, not the ASUSR002 format. All packets use existing RSC1
magic and little-endian uint32 opcode/length, with a maximum 1 MiB payload.
No request carries a partition, path, source identifier, offset or hash.

| Request | Exact payload | Reply | Meaning |
| --- | --- | --- | --- |
| 0x30 | empty, original daemon IDLE only | 0xb0 empty | Terminal handoff to fixed helper |
| 0x31 | Next exact 1 MiB, final 1,011,712 bytes | 0xb1 empty | Staged in bounded anonymous RAM only |
| 0x32 | empty, after all 16 chunks | 0xb2: uint32 SKIP, 32-byte actual prior digest | Payload sealed/verified; full preimage read and admitted |
| 0x33 | empty, READY only | 0xb4: 32-byte full final readback digest | One whole-p10 attempt; reply only after fsync/close/reopen/full actual readback |
| 0x40 | empty, new terminal connection | 0xc0 text | Read-only terminal state; never resets state |
| 0x41 | empty, new terminal connection | 16 x 0xc1 byte chunks, then 0xc2 whole digest | Deliberate actual p10 observation; never reactivates writing |

When 0x32 finds exact original stock in the full actual preimage read, it sends
SKIP=1 and 0xb4 without opening p10 writable. The parent host checks the actual
prior digest against its generated final-image pin (or exact stock for SKIP)
before 0x33. The target independently checks the immutable core, canonical helper
archive, RAM helper identity, header ID, padding and fixed unit geometry.

There is no path from terminal service back to staging, from UNKNOWN to READY,
or back to ordinary RSC1 transactions. Existing opcodes 1–9 and per-chunk
recovery guards are unchanged. The same abstract lifetime writer lock and the
accepted/listening sockets survive the exec domain transition. The service
remains oneshot. No retry, fallback write, discard, reboot or automatic restart
exists. Fresh connection 0x33 is rejected, including after DONE.

The target's 15-second socket timeouts are inactivity limits. The host has an
additional 300-second operation deadline; expiration is UNKNOWN, not permission
to restart, reboot or send again. Block I/O can continue after a host disconnect.
A terminal DONE response or later stock readback cannot retroactively replace a
lost host transaction receipt.

`source/host.py` takes only an already authenticated parent-established stream
and a new host receipt directory. It performs no connection or device operation.
`restore()` refuses the delivered unarmed profile. `_exchange()` is the same
production exchange exercised by offline tests, not an alternative device route.
The parent must retain `attempt.json` (durable UNKNOWN before the first request)
and, if present, the atomically published, fsynced `receipt.json`. Ignore `.new`
files as incomplete publication. Receipt directory creation and authenticated
transport setup belong to the parent. Never reuse an attempt directory.
