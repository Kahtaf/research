# Exact incremental r8 handoff

The parent-owned launch kit is `/srv/android/asus-reviewed-build-kit/r8`; its candidate is `/srv/android/asus-product-integration-staging/r8`. SHA256 of `inputs/kit-pins.json` is **f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4** (134 pinned files). No production r8 attempt, approval, integration, native build or device action was created by this worker.

Read REPORT.md and these compact review surfaces before launch:

1. `source/wpa-include-boundary.patch`, `source/zram-context.patch`, `inputs/r8-delta.json`: the entire future source scope is two files. WPA changes only the upstream include diagnostic boundary. The context file gains only `/dev/block/zram0    u:object_r:swap_block_device:s0`.
2. `scripts/continuation.py`, `scripts/integrate.py`, `source/scripts-from-r7.patch`: exact already-integrated r7 preimage; preserved ancestors; two exclusive source writes; original supervisor/flock/FD/ancestry/one-shot protections.
3. `scripts/build.sh`, `scripts/capture_build_evidence.py`, `scripts/compiler_channel.py`, `scripts/verify_product_r3.py`: compressed native command channel, successful phase/current Ninja joins, unchanged strict r8 freshness gates. **No `showcommands` argument.** It is rejected in actual `build/soong/cmd/soong_ui/main.go`, despite config.go parsing it.
4. `inputs/qualification/`: genuine SDK37 WPA original/candidate/strict-warning negative, identical 155 shared dependencies, real policy/type/selected-context checks, and authentic r7 command disposition. `inputs/r7-preservation.json` binds all 21 actual r7 attempt files, original r7 logs and the owned immutable compressed verbose copy. Original r3/r5/r6 evidence remains checked through the unchanged r7 ancestor guards.
5. `inputs/lmkd-functional/REPORT.md`, `HANDOFF.md`, `qualification.json`: parent must review the complete memory evidence before launch. Four native pressure/recovery cycles pass; protected incompressible overload fails. Full Android17 + Google + root usability remains unproved.

## Evidence decision

Terminal r7 is actual exit 1 at `2026-11-06T23:02:58.864381+00:00`, with original FAILED.json preserved. Its kit seal is `9287a07d243a9d70abefa0102de160d88af712a574c7fab6032ce9b36920f617`; UI log SHA256 is `e18314db5121a830f0f000f8c40616e2377312a804e22e477ae20030472bdc61`.

The genuine compressed r7 log is frozen at `r8/evidence/r7-native/verbose.log.gz`, SHA256 `ac3b3a99e80ab47feef181073397fbc83837d6edcd035b30041913b5b01a77ee`. It contains 1,227 completed-action lines and **zero completed commands for the validator's selected bpfloader/vold/sensor/BPF outputs**. Its source-specific command lines are pending-work diagnostics, not successful executions. No mandatory prior r7 execution is admitted. R8 must genuinely execute every output for which the inherited validator requires freshness. There is no timestamp relaxation, source touching, cache cleaning, rebuild forcing or fixture substitution.

Each future `m -j8` phase freezes its genuine `verbose.log.gz`, `.ninja_log` and available native diagnostics into `attempt/native-evidence/<phase>/` before the next m invocation can rotate them. Failed phases are preserved too. Only completed `[n/total]` action records, excluding failed records, can supply commands. Commands must produce the exact full output path with `-o`; linker dependency mentions and `verbose: ninja:` pending diagnostics cannot qualify. A command must join the same successful Ninja entry in its frozen phase and the current Ninja log. Source/graph/toolchain/installed ELF/build ID/SYSTEM/APEX/BPF26 checks and strict r8 output/record timestamps remain mandatory.

## Parent sequence

Wait for the separately owned runtime-prerequisite build's actual terminal receipt. This worker does not poll or manage it. A live native job or held original lock is a coordination refusal, not a source blocker. Do not bypass it or launch a second supervisor.

On the existing builder, verify the kit and obtain the unapproved r7 failure description under the original nonblocking lifecycle lock:

```sh
set -euo pipefail
cd /srv/android/asus-reviewed-build-kit/r8
printf '%s  %s\n' f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4 inputs/kit-pins.json | sha256sum --check
python3 -B - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from integrate import verify_pins
assert verify_pins(Path.cwd()) == 'f55aedf8ac9d2a513e3663230db0b9d802e72b5df512fc0db6b3714331a7efa4'
PY
mkdir -p parent-review
set -o noclobber
python3 -B scripts/integrate.py --describe-prior > parent-review/r7-description.json
```

Only the parent authors `/srv/android/asus-reviewed-build-kit/r8/parent-review/r7-failure.json`, using exactly `result.review_template` from that description. Set `reviewed_by_parent` to true only after actual review and provide a nonempty reason. Keep `prior` intact; permitted top-level keys are exactly `reviewed_by_parent`, `reason`, `prior`. This worker supplied no acceptance file.

The exact read-only eligibility command defaults to PLAN_ONLY:

```sh
set -euo pipefail
cd /srv/android/asus-reviewed-build-kit/r8
r8_review_sha=$(sha256sum parent-review/r7-failure.json | cut -d ' ' -f 1)
python3 -B scripts/integrate.py \
  --prior-failure-review /srv/android/asus-reviewed-build-kit/r8/parent-review/r7-failure.json \
  --prior-failure-review-sha256 "$r8_review_sha"
```

A passing plan is only eligibility at that instant. After parent review of the kit, memory evidence and exact failure acceptance, the parent may use the same command with `--mode PARENT_EXECUTE` added. That is the only integration/build entry point; do not invoke build.sh directly. No affirmative command has been executed by this worker. Do not rerun preparation/upload scripts.

Execute nonblockingly acquires the original `/srv/android/asus-device-product/logs/full-product-build.lock` without creating, replacing or truncating it, refuses live native work or any prior r8 marker/attempt, rechecks pins/preimages and the exact parent acceptance, exclusively claims r8/attempt, backs up both source preimages and prior r7 logs, and applies only the two reviewed files. It holds the same inherited flock continuously through foreground incremental build and host validation. The build child independently proves FD inode, held lock, supervisor ancestry and one-shot consumption. Failures preserve attempt and terminal receipts permanently; no retry, rollback, installclean, baseline replay or automatic relaunch exists.

Real lunch/dumpvars, full product variables and exact policy/manifest paths are required **before native compilation**. Full actual Soong, Google32, authenticated userdebug ADB/root, compiler/linker/ELF, BOOT/SYSTEM, BPF26, APEX, init, VINTF, policy/context/neverallow validators remain required. Final zRAM validation independently links installed CIL without disabling neverallows, validates merged contexts against that policy, uses genuine libselinux to select the block-device context, and binds installed vendor contexts to actual SYSTEM bytes. Real device activation remains a later parent gate.

Kernel `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1` and config `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2` remain frozen. Charging stays inhibited; audio PCM is excluded; frozen probes are untouched. Post-delta actual dumpvars/full build/full image qualification and physical Android/Google/root/hardware usability remain unproved. No flash readiness or physical GO is granted.
