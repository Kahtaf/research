# Local stock OS rollback payloads

Question: can the exact saved stock BOOT/SYSTEM/recovery bytes be available on the
Mac independently of the build VM and without executing ASUS's complete updater?

Status: completed local bundle at `artifacts/stock-rollback/`; 7 offline test
methods pass. The 3,753,902,080-byte SYSTEM was independently reread and matched
all 112 captured-backup chunks and the complete captured SHA-256. BOOT and
recovery match both saved original copies. No device, cloud, bootloader or partition
operations. The selected OEM SYSTEM reconstruction is permitted only because its
whole image already equals the captured, independently verified tablet backup.
The output is a local payload source, not an authorization or mechanism to flash.

`source/prepare.py` defaults to PLAN_ONLY. `--execute` reconstructs SYSTEM with
bounded memory, checks every chunk against the pinned actual-backup manifest,
and rereads the entire output. BOOT/recovery must match both saved original
backups. Outputs are published read-only only after all checks pass. The ZIP's
preloader, LK, TEE, updater, and all other payloads are never extracted or run.

Run offline tests with `python3 -B -m unittest discover -s tests -v`. Build the
local bundle using `python3 -B source/prepare.py --execute`. Existing completed
or pending output is never overwritten or resumed implicitly. Retain failed
pending output for inspection. A separate qualified rescue service, fixed
partition geometry, writer, and physical acceptance are still required.

Important outputs:

- `artifacts/stock-rollback/system.img` — SHA-256
  `4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49`
- `artifacts/stock-rollback/boot.img` — 16,740,352 bytes, SHA-256
  `7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`
- `artifacts/stock-rollback/recovery.img` — 16,740,352 bytes, SHA-256
  `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`
- `artifacts/stock-rollback/READY.json` — input pins, construction boundary and
  output hashes. `ready_to_flash` remains false.

SYSTEM/BOOT contain only the publicly distributed stock OS; this bundle does
not contain personal data or factory calibration. The existing private local
calibration backups must remain separate. Recovery came from both actual device
backups. Preserve this local bundle and the remote captured backup until a
working replacement OS and rollback path have been physically accepted.

Continuation: use these exact byte sources for the independent rescue's inverse
manifest/provider, rechecking hashes before any use. Do not run the full OEM
updater. Do not reconstruct another full copy unnecessarily; the Mac retains
only several GiB free after this bundle.
