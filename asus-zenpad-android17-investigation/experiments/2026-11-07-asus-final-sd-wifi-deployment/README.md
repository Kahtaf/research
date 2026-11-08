# Final SD-rescue Wi-Fi recovery deployment

Question: can the existing reviewed p10-only Wi-Fi writer deploy the parent's
actual final offline stock-fallback assembly without changing its write sequence?

Status: implemented, with focused offline checks passed. Host-only; no device
contact or deployment. The real final assembly is absent. No candidate, manifest,
arm, SYSTEM/BOOT identity or physical GO was manufactured.

Outputs: `source/install.py`, `source/admission.py`, focused offline evidence and
exact source pins under `evidence/`. Existing tools/core/helper/shim stay unchanged.

The adapter admits only the exact fixed `final_package.py` contract. It reads the
assembly receipt before stock-image inputs, binds both candidate files to their
actual lengths/digests, checks the full 16740352-byte p10 and all zero padding,
and parses the manifest/arm from the actual operational ramdisk. It checks the
genuine original-pair prefix, five fixed roles/geometry/chunk counts/CID/GPT and
the admitted final DATA whole identity. It reads no raw role images or external
parent-private manifest/table.

Using the existing pinned parsers/packager, admission reconstructs the byte join
in memory from the delivered common core, actual embedded authorities and the
fixed public physical e9 kernel artifact. Complete equality proves the compiled
Image/config, restricted DT changes, memory reservations, 92-byte LK header,
stock header addresses, MTK wrappers, Android SHA1, canonical binding capsule and
padding. It compares the complete packaging/behavior receipt and every emitted
control file. This does not compile anything or write a candidate. The receipt
is parent input and explicitly remains `physical_GO=false`.

`execute()` and the `Transport` class are byte-for-byte preserved from the actual
working SD-probe installer. The explicit-execute main tail differs only in using
the frozen shim's original directory in PATH. The original helper, engine, Wi-Fi
transport and legacy nonce/remote-exit shim remain untouched. Identity, stock boot
continuity, Enforcing, geometry, source checks, 600-second expiry, shared existing
mutation lock, journal, full stage/preimage/readbacks, bounded fixed-stock inverse,
terminal uncertainty, cleanup and no-reboot behavior are retained.

Only `/dev/block/mmcblk0p10` is writable by this host adapter. Allowed install
preimages are exactly original
`902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`
and the installed SD probe
`78005304291706fe2ad2affa185467c89464dc2f3216f97d572a29a1e058afa9`.
An already exact final candidate uses the preserved no-write idempotence path;
unknown bytes refuse. The host adapter does not invoke the recovery's later
normal/stock SD programs. It never writes BOOT/SYSTEM/DATA/p20/GPT/BCB or reboots.

Run from `/OWNER_HOME/Documents/workspace/ideas`, after the parent has produced
the actual final assembly with the existing final packager:

```sh
python3 -B 2026-11-07-asus-final-sd-wifi-deployment/source/install.py \
  --assembly-dir 2026-11-07-asus-offline-stock-fallback/artifacts/final
```

This defaults to PLAN_ONLY. It performs local admission only and never contacts
ADB. The current absent directory returns exit 2, `mode=PLAN_ONLY`,
`outcome=refused`, `device_contacted=false` before stock-image inputs. With the
real assembly it prints its actual image/full-p10/manifest/binding identities.

After the parent has reviewed that actual assembly and the physical SD probe
result, the precise deployment command is:

```sh
python3 -B 2026-11-07-asus-final-sd-wifi-deployment/source/install.py \
  --assembly-dir 2026-11-07-asus-offline-stock-fallback/artifacts/final \
  --execute
```

There are no worker approval flags, new approval files, USB requirement or user
reconfirmation. Execute reuses authenticated `IP_REDACTED:5555`, serial
`DEVICE_SERIAL_REDACTED`, the existing server on 5037, the fixed helper and shared lock.
It strips ADB/ANDROID_ADB/ANDROID_SERIAL environment overrides and neither starts
nor kills a server. Each actual run's existing full evidence semantics use this
new spike's `private/<uuid>` and `evidence/<uuid>.json` directories. An uncertain
run stops without a retry or further commands.

Focused results are in `evidence/focused-offline.json`: byte-preserved execution
and transport, preserved execute tail, exact narrowed preimages, pinned parser
loading, duplicate/nonassembly receipt refusal, missing five-role authority
refusal, source-drift refusal, and actual default missing-directory refusal with
network/process/helper/stock-input callbacks blocked. No writer was invoked.
`source/check_offline.py` records these checks without generating a fake complete
candidate/receipt/manifest. It is for this absent-assembly handoff only; once the
real assembly exists, use the PLAN command instead of rerunning that check.

Exact pre/post upstream hashes are in `evidence/upstream-{before,after}.json`;
the final-core source pins are in `evidence/core-source-pins.json`; new delivery
hashes are in `evidence/DELIVERY_PINS.json`. The minimal old/new installer diff is
`evidence/install.patch`.

Boundary: no positive full-assembly admission, physical deployment, kernel boot,
SD hardware, runtime stock restore or reset proof is claimed. Genuine final
artifacts and physical SD-probe evidence remain parent inputs. No device/root/
ADB/USB/network/SSH/VM/cloud operation, build, other-process inspection, private
payload read, or old source/artifact mutation was performed in this spike.
