# Offline reproduction and verification

The finished implementation is owned remotely by `/srv/android/asus-target-rescue`; this local handoff mirrors source, tests and compact artifacts. Do not recreate the fixture or restart completed jobs. All commands below are offline and perform no device operations. Inspect actual processes/exit files before starting a new revision. Existing output directories are deliberately refused.

## Verify on the laptop

From this directory:

```sh
python3 -B scripts/verify_local.py
```

This checks the local package and source inventory, exact stock-kernel preservation, ARM64 static binaries, ramdisk contents, non-authorizing identity manifest, and checksums. It does not reread the parent's multi-gigabyte rollback payload or contact a device.

`artifacts/local-stock-inverse.PLAN_ONLY.json` is the preferred inverse source map. `inputs/parent/local-stock-rollback.READY.json` and the actual-capture manifest preserve the independent parent verification. File paths point at the parent's local rollback directory; do not duplicate SYSTEM into this handoff. `artifacts/parent-review.PENDING.json` deliberately fails the manifest approval gate.

## Build on the existing Linux builder

Dependencies used: Python3.12, GNU make/ar/gcc and aarch64-linux-gnu-gcc 13.3.0-6ubuntu2~24.04.1, plus QEMU only for the virtual tests. Exact compiler commands/stdout/stderr and return codes are in `artifacts/tools-delivery/commands.json`. Vendored source archives are pinned by SHA-256 in `SOURCE_PINS.json` and asserted by `source/build.py`; there are no floating downloads. The historical assembler provenance also lists six remote AppleDouble `._` metadata files; those are not compiler inputs, are omitted from this local handoff, and are excluded from local source verification. Every actual source and test file is pinned in `SOURCE_PINS.json`.

Use a fresh suffix instead of reusing delivery outputs:

```sh
cd /srv/android/asus-target-rescue
python3 -B source/build.py --out artifacts/tools-NEW
python3 -B source/assemble.py \
  --stock inputs/initial/recovery.bin \
  --stock-verify inputs/verify/recovery.bin \
  --public-key artifacts/inputs/adbkey.pub \
  --tools artifacts/tools-NEW \
  --identity-plan artifacts/stock-inverse.PLAN_ONLY.json \
  --out artifacts/candidate-NEW
```

`build.py` uses `make -j2`, sequential compiler invocations, `LC_ALL=C`, `SOURCE_DATE_EPOCH=1793923200`, static ARM64 binaries and no linker build ID. Assembly has deterministic newc ordering/metadata and gzip time zero. The existing accepted stock inventory is reused; no completed full-size workload needs repeating. The two saved original recovery inputs must match each other and the hard-coded original hash before assembly.

Exact changed-daemon reproduction performed:

```sh
aarch64-linux-gnu-gcc -static -O2 -Wall -Wextra -Werror \
  -Wno-unused-function -Wno-misleading-indentation -Wl,--build-id=none \
  source/rescue.c -o artifacts/daemon-delivery-reproduction/os-rescue
```

The command was run in a newly created reproduction directory. `scripts/record_reproduction.py` compares those bytes and both separately assembled image/policy/context/manifest sets. Do not rerun it until the referenced outputs exist.

## Focused validation commands used

The final host adapter was compiled with:

```sh
gcc -O2 -Wall -Wextra -Wno-unused-function -Wno-misleading-indentation \
  tests/test_server.c -o artifacts/tools-delivery/test_server
RESCUE_TEST_SERVER=/srv/android/asus-target-rescue/artifacts/tools-delivery/test_server \
RESCUE_DAEMON=/srv/android/asus-target-rescue/artifacts/tools-delivery/os-rescue \
  python3 -B tests/test_adapters.py
python3 -B tests/policy_audit.py artifacts/tools-delivery \
  artifacts/candidate-delivery evidence/policy-audit-delivery.json
```

For the guest helpers, each was compiled separately with:

```sh
aarch64-linux-gnu-gcc -static -O2 -Wall -Wextra -Wno-unused-function \
  -Wno-misleading-indentation -Wl,--build-id=none \
  tests/guest_init.c -o artifacts/tools-delivery/guest-init
aarch64-linux-gnu-gcc -static -O2 -Wall -Wextra -Wno-unused-function \
  -Wno-misleading-indentation -Wl,--build-id=none \
  tests/target_probe.c -o artifacts/tools-delivery/target-probe
```

Completed runtime invocations, using the already existing kernels:

```sh
python3 -B tests/run_guest.py qemu-blocks-delivery \
  artifacts/candidate-delivery artifacts/tools-delivery
python3 -B tests/run_stock_init.py qemu-stock-init-delivery \
  artifacts/candidate-delivery build/compat-out/arch/arm64/boot/Image \
  artifacts/tools-delivery/guest-init
```

These names already exist and must not be reused. Each QEMU command is preserved in its evidence directory; two CPUs, 1536 MiB, no network or USB passthrough. Do not run `tests/build_compat_fixture.sh` against the existing fixture: it is the historical one-time construction recipe and deliberately refuses an existing source directory. Do not rerun the successful full-size SYSTEM or pristine userdata workloads for routine delivery checks.

## Input preparation provenance

`source/prepare_inverse.py --out artifacts/stock-inverse.PLAN_ONLY.json` was run once remotely to hash the actual accepted cloud SYSTEM into 1 MiB chunks and match both saved BOOT/recovery copies. It produced inventory only, no armed manifest. Its output and parent receipts are delivered; it need not be repeated to rebuild the unarmed recovery. Parent's later local rollback provider is preferred for future inverse payload delivery and has its own independent receipts.

The daemon requires `ASUSR002`; raw-CID version1 manifests are incompatible by design. The binary header contains CID SHA-256, both GPT pins and image count zero. Supplying `--manifest` to assembly is a separate future arming operation, not part of these reproduction commands. No such operation was performed for the delivered recovery.
