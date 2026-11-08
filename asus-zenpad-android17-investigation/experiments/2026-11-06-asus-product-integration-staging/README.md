# Product integration staging

Question: can the qualified combined kernel, radio product and exact-LK full
BOOT packaging be assembled without changing the running Android build?

Status: isolated staging completed and checked. This is a separate staging candidate, not an
active deployment or a flashable product. Firstboot parity, the completed full
product build, physical rescue and hardware remain separate requirements.

`scripts/prepare.py` defaults to PLAN_ONLY. With `--stage`, it checks pinned
handoff inputs and copies only into a fresh builder directory. It selects the
compiled combined r5 kernel and matching config explicitly, replaces the stale
staged prebuilt, and stages the corrected full BOOT tools with their exact
dependencies. Existing candidate and active source trees must remain unchanged.
No AOSP build is started and no full SYSTEM/data image is copied.

The actual builder candidate is `/srv/android/asus-product-integration-staging/r1`.
Relative to the reviewed radio staging, only `BoardConfig.mk` and the prebuilt
kernel changed. The standalone kernel config is included for later active
header generation. `evidence/remote-staging.json` records every product and
Connectivity hash, the eight packaging inputs, and unchanged active inputs.

The actual staged kernel's embedded config equals the selected resolved config
(`067090e0...045f`), and its image hash is `46895deb...ec401`. The staged source
command matches the current build's actual dumpvars. Applying the reviewed
contract yields a 92-byte header with `enforcing=1`; the actual Image/DT passes
the maximum 4 MiB ramdisk memory check and the fstab hash matches.
`evidence/actual-kernel-contract.json` records this read-only check. It does not
establish the eventual real ramdisk size, physical RAM fixups or dynamic consys
allocation. No full BOOT image was generated.

The initial parent command-check fixture read only the assignment line and
omitted its two append lines. The corrected check combines all three and compares
against actual dumpvars; no production command-line change was necessary. The
initial failure is retained in `evidence/initial-command-check.json`.

`evidence/firstboot-parent-acceptance.json` now accepts the scoped r7
file-locking/cgroup/init parity supplement. Parent verified all 84 exported
payloads, inspected real positive and negative observations, independently
rehashed the 290 selected source files on the builder and checked 134 selected
options against the staged physical config. This clears that specific
integration gate. It does not execute the combined physical kernel or establish
the complete keystore/APEX/adbd chain. The earlier immutable `STAGED.json` keeps
its original pending status; use the supplemental receipt rather than changing
historical evidence.

`python3 -B scripts/prepare.py` remains a local-only PLAN_ONLY check. Do not rerun
`--stage`: the completed remote revision and local receipt refuse overwrite.
Evidence is stored here. Before active
integration, finish the firstboot parity handoff, verify actual termination of
the original full build, acquire its build lock, and preserve its outputs.
The previous integrator paths refer to an older candidate; they must not be
executed unchanged against this new staging directory.
