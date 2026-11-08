# Parent command sheet — no device actions executed

All commands below run from this spike. The delivered state is PLAN_ONLY, with no technical approval or physical-presence attestation. No execute command with affirmative supervision or fallback flags is supplied.

Offline verification (local public source/image/stock-recovery reads only):

```sh
python3 -B source/adapter.py verify-local
python3 -B source/adapter.py plan
python3 -B source/adapter.py install
python3 -B source/adapter.py restore
python3 -B tests/run_tests.py
```

Expected refusal without supervision, fallback, contract and pin:

```sh
python3 -B source/adapter.py install --execute
```

Unapproved contract template, printed only to stdout. The UUID below is illustrative; parent chooses a new canonical UUID for an actual authorized run. Output belongs inside this spike if saved. No current times, approval, presence, or fallback are asserted:

```sh
python3 -B source/adapter.py template --run-id 9b95c5c6-cae1-44c9-bf02-1f6159a3dce7 --phase pin-install
python3 -B source/adapter.py template --run-id 9b95c5c6-cae1-44c9-bf02-1f6159a3dce7 --phase install
python3 -B source/adapter.py template --run-id 9b95c5c6-cae1-44c9-bf02-1f6159a3dce7 --phase pin-restore
python3 -B source/adapter.py template --run-id 9b95c5c6-cae1-44c9-bf02-1f6159a3dce7 --phase restore
```

Concrete future parameter shapes, intentionally still PLAN_ONLY:

```sh
python3 -B source/adapter.py pin-install --run-id 9b95c5c6-cae1-44c9-bf02-1f6159a3dce7 --contract evidence/parent-pin-install-contract.json
python3 -B source/adapter.py install --run-id 9b95c5c6-cae1-44c9-bf02-1f6159a3dce7 --contract evidence/parent-install-contract.json
python3 -B source/adapter.py pin-restore --run-id 9b95c5c6-cae1-44c9-bf02-1f6159a3dce7 --contract evidence/parent-pin-restore-contract.json
python3 -B source/adapter.py restore --run-id 9b95c5c6-cae1-44c9-bf02-1f6159a3dce7 --contract evidence/parent-restore-contract.json
```

The parent may only construct actual execution commands after independently reviewing the source/profile hashes and filling the matching phase contract with a review reference and a fresh numeric UTC-epoch validity interval of at most 600 seconds. The execute parser also requires truthful supervision and nearby-Power-fallback attestations at invocation. These gates are deliberately absent from every future parameter shape above. No file in this delivery approves execution.

Fixed parameters cannot be overridden: serial DEVICE_SERIAL_REDACTED, stock fingerprint/SDK24/boot completion/secure ADB/Enforcing, stock product/model/device, already-connected authenticated Wi-Fi IP_REDACTED:5555, recovery node and alias, 179:10/start160184/32696 sectors/512-byte geometry, exact candidate and all zero padding, exact wrapped stock kernel/header layout, two original recovery backups, pinned root helper and root binary. The shared mutation lock must already exist at the established writer path; the adapter never creates a substitute lock.

Each pin phase records actual USB inventory and healthy-stock properties, boot UUID and stopped stock recovery autorepair. Install reads its own `evidence/runs/UUID/pin-install/pin.json`; restore reads the corresponding `pin-restore` result. Pin maximum age is 180 seconds. All phase directories are exclusive. During a phase, changed identity/topology/transport ID stops commands. Between install and restore, a changed transport ID is allowed only with identical physical topology and identity and a fresh full stock snapshot. If manual entry occurred, parent first owns and observes manual return; this tool does not enter recovery, observe rescue, certify return, or re-enable/reconnect Wi-Fi.

Install requires a guarded actual entire-p10 stock capture, then one candidate dispatch and entire-p10 candidate verification. A known completed candidate failure permits at most one fixed-original inverse under the same still-valid guards. Uncertain transport/helper completion, Unicode decoding failure, deadline expiry or invalid identity stops all commands, including inverse and cleanup. Later restore requires the receipt nonce from the successful live install output, a clean linked install, both actual prerequisite/final captures and their command evidence, and admits only the exact installed candidate or already-original recovery. Unexpected other recovery bytes are refused. An uncertain/failed install, consumed restore, altered source or missing capture is not eligible.

The local stock backup copies are staging inputs. They never count as physical capture or restoration evidence. Actual installed bytes, parent manual entry, rescue commissioning, parent-observed stock return, verified restoration, and hardware readiness remain separate statuses. No rescue protocol, BCB/p20/p26/SYSTEM/BOOT write, reboot, mode selection, automatic retry, TCP re-enable, or reconnect command is exposed.

A successful live install output contains `install_completion_token`. Only its SHA256 is stored in the install journal. Parent retains the actual returned nonce and supplies it in the `install_completion_token` field of both later removal contracts. Missing, wrong, or journal-derived values are refused before transport. If publication/fsync or the live result is lost, the visible token digest cannot reconstruct acceptance. This is a completion receipt, not physical commissioning or permission to boot the candidate.
