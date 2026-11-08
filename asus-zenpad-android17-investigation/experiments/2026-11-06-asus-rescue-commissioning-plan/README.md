# Parent rescue commissioning decisions

Question: how do the independently reviewed rescue limits change the next real
tablet test and full-install prerequisites?

Status: review findings adopted; physical qualification pending. No device
commands, arming approval or runtime readiness are supplied here. The reviewed
unarmed block-kind image and all original implementation files remain unchanged.

Read the independent report in `../2026-11-06-asus-rescue-independent-review/REPORT.md`.
Its context-kind verdict is accepted. These parent decisions supersede ambiguous
continuation wording in older handoffs:

1. A zero-record STATUS response establishes endpoint/idle state only. Positive
   descriptor tests require a separately reviewed STOCK-only two-role manifest.
   Static arming review precedes those tests; mutation qualification follows them.
2. Opcode6 has no recovery-pin argument. For commissioning, stream all 16 actual
   p10 chunks into a host SHA256 and compare with the final armed image's exact
   padded digest. Last chunk: 1,011,712 bytes. Keep this host comparison distinct
   from the daemon's self-hash and later pin-checked reconciliation.
3. Sample original p9 and p25 at first/middle/last chunks and compare actual bytes
   with trusted source tables. Then use fresh connections to reconcile original
   SYSTEM and BOOT, without activation. Reconciliation changes connection state;
   it is not an IDLE readback session. No synthetic corruption to prove writes.
4. Retain the existing per-chunk recovery content hash for initial commissioning.
   Production adds 241,111,289,856 recovery bytes for SYSTEM/DATA/BOOT chunk checks,
   and 241,362,395,136 including phase checks. These are byte arithmetic, not time
   or wear measurements. Measure bounded physical read/hash latency first. No
   guard cache, weaker content check or new target opcode is accepted here.
5. A lost host receipt remains UNKNOWN even if the daemon later reports IDLE.
   Never resend automatically or resume by offset. Require actual idle proof and
   explicit fresh reconciliation. Daemon memory and its tmpfs journal do not
   survive reboot. The proposed source-comment correction is in `patches/`.
6. Socket receive/send timeouts are inactivity limits, not absolute operation
   deadlines. Elapsed time does not authorize a reboot or another writer.
7. Original roles0/1 are a SYSTEM/BOOT inverse only. They do not restore p26 or
   p10. Any future five-role operation additionally requires a verified stock
   userdata recovery plan and all factory calibration preservation. p20 remains
   untouched. The clean Android17 ext4 image does not prove stock compatibility.

Next: finish the stock-data recovery study and a concrete STOCK-only armed
artifact/host readback plan. Actual commissioning requires nearby fallback and
fresh device checks. The first R3 RAM-only Linux4.9 trial is separate and does
not depend on full-OS rescue commissioning. No new permission question is needed
for offline preparation within the user's existing authorization.
