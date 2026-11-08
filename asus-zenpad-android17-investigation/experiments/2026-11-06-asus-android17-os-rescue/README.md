# Android 17 OS rescue

Question: repair the proven stock-kernel diagnostic report and retain independent
BOOT/SYSTEM recovery before replacing normal Android, using clean internal data.

Status: **offline handoff complete; parent review required.** The new diagnostic
is compiled and byte-reproduced. The OS rescue is a tested offline prototype;
the Linux adapter/proxy/new SELinux policy are not integrated. Its ARM64 unarmed
binary exits78 and must not be treated as a functioning recovery. No device,
root, VM/cloud, goal, upload or physical formatting operations occurred.

Start with [report/REPORT.md](report/REPORT.md), especially the ordered parent
runtime gates and the OEM metadata-wide wipe finding. User's latest choice is
internal storage with nothing to preserve: no microSD, full old-userdata backup
or legacy FDE decryption prerequisite. No format has been executed or approved
by this handoff.

Important outputs:

- [New diagnostic candidate](artifacts/candidate-final/UNTESTED-stock-control.img),
  SHA256 `7d74dfcaf4b2793453906799d721bfd95a401c564f6698b1c646e18bee918ea5`.
- [Unapproved diagnostic transport contract](artifacts/candidate-final/transport.UNAPPROVED.json).
- [Report/policy/DAC verification](evidence/diagnostic-final.json) and
  [byte-identical reproduction](artifacts/reproduction-final/reproduction.json).
- [Rescue controller](source/rescue.py), [native bounds gate](source/rescue_gate.c),
  [stream framing](source/protocol.py), [unapproved contract](artifacts/rescue-v1/manifest.UNAPPROVED.json).
- [27 passing offline tests](evidence/offline-tests-final.txt),
  [exact binary audit](evidence/binary-audit-v1.json),
  [real host ext4 fixture evidence](evidence/ext4-fixture-final.json).
- [Fixed p26 data recipe](source/data_plan.py), [staged init/policy/fstab](source/staged-rescue),
  [corrected observer](source/observer.py).

To continue offline, run `python3 -B source/reproduce.py --out artifacts/NEW-name`
from this spike. Existing outputs are refused. The report documents dependencies
and additional commands. Parent supplies real SYSTEM backup receipt from the
separate stock-system-stream-backup spike; this spike does not duplicate that tool.
Existing diagnostics, transport, approved manifests and original backups stay
unchanged. Do not infer target recoverability from host tests or restore stock via
OEM wipe_data without reviewing its whole-metadata wipe behavior.
