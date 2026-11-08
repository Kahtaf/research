# Exact r7 continuation handoff

The kit is `/srv/android/asus-reviewed-build-kit/r7`; its candidate is `/srv/android/asus-product-integration-staging/r7`. The entry-point manifest SHA256 is **9287a07d243a9d70abefa0102de160d88af712a574c7fab6032ce9b36920f617** (101 pinned files). The parent owns source integration, launch and every device action. This kit contains no approval, implicit launch flag or attempted r7.

## Review these surfaces

1. `source/sensor-board-path.patch`, `inputs/sensor-delta.json`: exactly one assignment in `device/asus/p00a/sensors/BoardConfig.mk`, from `$(call my-dir)` to `device/asus/p00a/sensors`. Preimage `0e012287927a5b8ac3733f7fcc28d5cdc0eb1d8f06e82e0ff6ad211fe2f72f90`; postimage `9207c304761cf86afb423641534ed383e7f8dae613e64061e972d2f65832aa4d`. Policy and manifest bytes do not change.
2. `source/changes-from-r3.patch`, `scripts/continuation.py`, `scripts/verify_config_paths.py`: retained lifecycle supervisor and validators, exact continuation eligibility, sole source write, actual dumpvars path gate.
3. `inputs/prior-preservation-pins.json`, `inputs/r6-integration.json`, `inputs/r7-staging-manifest.json`, `evidence/final-readonly-state.json`: original r3 attempt, r5/r6 evidence, current exact sensor preimage and candidate lineage.
4. `evidence/linux-tests-and-source-audit.json`: actual Linux behavior tests and complete read-only source audit. `REPORT.md` states the limits.

The original r3 seal remains `a00ea8d7c944d45e3035296c81b31a369f13bde830f88a7165b0d7542960717c`. Its attempt is terminal: real native r6 exit **1** at **2026-11-06T22:28:00.150539+00:00**, with preserved FAILED.json. Log SHA256 is `ee061d878227210f7c2330bb36ca13f76a9daa37e354a178d733327695cfd4e0`. This was an actual source configuration failure; it is not a timeout. The r6 log has both the `/sepolicy` traversal panic and `/manifest.xml` diagnostic from the same empty BoardConfig path.

## Parent commands on the builder

Use the existing VM/session and original lock. Do not replay r3 integration, run the r6 launcher, remove anything, or launch a second supervisor. These commands do not wait for existing jobs: a live native job, held original lock, unknown source drift or consumed revision refuses immediately.

First verify the concrete kit and obtain a fresh terminal description under the original lifecycle lock:

```sh
set -euo pipefail
cd /srv/android/asus-reviewed-build-kit/r7
printf '%s  %s\n' 9287a07d243a9d70abefa0102de160d88af712a574c7fab6032ce9b36920f617 inputs/kit-pins.json | sha256sum --check
python3 -B - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from integrate import verify_pins
assert verify_pins(Path.cwd()) == '9287a07d243a9d70abefa0102de160d88af712a574c7fab6032ce9b36920f617'
PY
mkdir -p parent-review
set -o noclobber
python3 -B scripts/integrate.py --describe-prior > parent-review/r6-description.json
```

The parent must read that description and author **`/srv/android/asus-reviewed-build-kit/r7/parent-review/r6-failure.json`**. Use exactly `result.review_template` from the description as the starting JSON. Only the parent sets `reviewed_by_parent` to `true` and supplies its actual nonempty `reason`. Preserve the entire `prior` object, including all r3 attempt/r5/r6 file hashes and current image hashes. The only allowed top-level keys are `reviewed_by_parent`, `reason`, `prior`. No acceptance file has been created by this child.

After the parent has authored and reviewed that file, the read-only eligibility command is:

```sh
set -euo pipefail
cd /srv/android/asus-reviewed-build-kit/r7
r7_review_sha=$(sha256sum parent-review/r6-failure.json | cut -d ' ' -f 1)
python3 -B scripts/integrate.py \
  --prior-failure-review /srv/android/asus-reviewed-build-kit/r7/parent-review/r6-failure.json \
  --prior-failure-review-sha256 "$r7_review_sha"
```

That is PLAN_ONLY. It is not a reserved slot or proof of the changed product's dumpvars. If it passes, the exact one-shot foreground parent execute command is:

```sh
set -euo pipefail
cd /srv/android/asus-reviewed-build-kit/r7
printf '%s  %s\n' 9287a07d243a9d70abefa0102de160d88af712a574c7fab6032ce9b36920f617 inputs/kit-pins.json | sha256sum --check
r7_review_sha=$(sha256sum parent-review/r6-failure.json | cut -d ' ' -f 1)
python3 -B scripts/integrate.py --mode PARENT_EXECUTE \
  --prior-failure-review /srv/android/asus-reviewed-build-kit/r7/parent-review/r6-failure.json \
  --prior-failure-review-sha256 "$r7_review_sha"
```

The hash argument must identify the file the parent actually reviewed. Do not generate a new approval merely to satisfy a refusal. If reviewed evidence changes, stop and inspect it. Do not execute the local preparation/upload scripts again.

## What execute does

The retained supervisor nonblockingly acquires the existing `/srv/android/asus-device-product/logs/full-product-build.lock` without creating/truncating/replacing it. It refuses native jobs and any prior r7 marker/attempt, verifies the actual failed r6 and the parent's exact failure acceptance, then audits the already-integrated r3 source set and all pinned candidates.

Only after those gates does it exclusively create its own `attempt/`. It records the exact sensor preimage and r6 failure in `attempt/preservation.json`, copies prior logs into `attempt/before/logs`, preserves the old r3 attempt in place, and leaves existing images/cache in place. It rechecks sources, pins and terminal evidence, atomically replaces only the sensor BoardConfig with the reviewed postimage, verifies the full source state, and writes `attempt/postimages.json` and `attempt/integration.json`. The new receipt binds the r3 integration and seal, inherited kernel/config/source receipts, exact full product manifest, sole write, preservation receipt and source-postimage receipt.

The same original flock remains continuously held through apply, foreground build and validation. The build child independently proves the inherited FD inode, live held lock, recorded supervisor ancestry and one-shot consumption. It then runs real `lunch` and dumpvars. Before either native `m` command, all current policy-directory variables and manifest inputs must be canonical source-relative paths that exist, without duplicate entries or a duplicated effective vendor policy path. The exact sensor policy directory must occur once and sensor DEVICE_MANIFEST_FILE must occur once; their source bytes and new BoardConfig hash must match. `/sepolicy`, `/manifest.xml`, escaping/symlink paths, missing paths or changed sensor policy/manifest bytes fail as `CONFIG_PATH_ERROR` before native compilation. The current supported variables are read from pinned Make/Soong mechanisms; obsolete Kati variables are not queried.

The existing `m -j8` host/service phase and `m -j8 bootimage systemimage` remain unchanged, with actual verbose compiler/linker records retained. Full image/Google/ELF/source/compiler/linker/policy/neverallow/APEX/BOOT/SYSTEM/VINTF/BPF26/sensor-installation gates remain required. Fresh compiler/linker provenance requirements now refer to r7; no stale r6 output or fixture ELF is admitted. Final validation rechecks the dumpvars receipt and requires the r7 sensor postimage.

Any failure preserves the new attempt and terminal evidence. No retry, rollback, installclean or automatic relaunch exists. Records use `full-build-r7.*` and `r7/attempt/`; r3, r5, r6 and frozen probes remain intact. Do not remove attempt markers even if no native build reached completion.

## Scope and remaining gates

Real product dumpvars has **not** been run for the changed product. The passing Make fixture evaluates the exact include with unavailable `my-dir`; it is not a substitute for the required product dumpvars under the parent-held lifecycle lock. Native compilation, full image validation, service/runtime qualification and hardware behavior remain unrun by this child.

Kernel remains `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`; config remains `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`. Hardware charging remains inhibited. Authenticated ADB, userdebug root and normal Google remain selected and validated by the inherited gates. Audio PCM repair is excluded/unaccepted; frozen probes and separate firstboot/memory work retain their owners. Full images stay on the VM. No physical GO, flash readiness or device action is authorized here.
