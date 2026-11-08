# Future parent commands and acceptance limits

Prepared implementation lives at `/srv/android/asus-full-system-observer-preparation-20261106`. **Do not run against partial r8 or active output.** R8's parent-reported 23:48:28 UTC exit 1/WebView LFS failure is ineligible. The separate r9 owner supplies a later successful product and producer receipts. This preparation does not inspect or poll that work.

## Produce the external expectation group

Follow [contracts/receipt-contract.md](contracts/receipt-contract.md) exactly. Missing today: a genuine later `complete.json` and pinned native terminal binding, coherent public source/installed-output capture, and the two SDK37 host resolver build/execution receipts. The parent must provide actual compiler/linker/dependency/source pins for the prepared fixed-path resolver TUs. No AOSP build was started here to obtain them.

1. Admit the actual completed product and preserve its existing whole raw/original image digests. Use the existing parent materialized `complete.raw_system.path`; do not make another full copy or recompute its whole hash here. Capture final stat identities after making artifacts immutable.
2. Freeze the actual plan-resolved BoardConfig, creation Python/config, generated SYSTEM stanza/properties, fs_config source and consumed override inventory, and coherent final compiled contexts. Freeze only the four public installed output files in `capture_root/installed/` with their original `/system/...` relative layout. Do not extract expectations from the image being tested.
3. Compile `source/resolve_fs_config.cpp` against that exact admitted SDK37 libcutils and its captured headers/dependencies. Its only argument is the coherent frozen TARGET_OUT; it resolves the four fixed files through real fs_config, including consumed binary overrides. Compile `source/resolve_contexts.c` against admitted SDK37 libselinux; its only argument is the frozen final-context stem whose pinned `.bin` contains the actual final merged contexts. Exclude unpinned sidecars. Run both serially under the limits below, capture exact stdout and exit 0, then publish the exact `asus-public-metadata-resolution/v1` receipt. These host producer build/exit receipts remain missing; the sources have not been compiled/run against genuine product inputs in this task.
4. Supply the independently pinned complete, source binding and resolution references to the expectation publisher. These variables must come from the parent's real admitted receipt group, not this fixture:

```sh
PREP=/srv/android/asus-full-system-observer-preparation-20261106
python3 -B "$PREP/scripts/capture_expectations.py" \
  --complete "$PARENT_COMPLETE" --complete-pin "$PARENT_COMPLETE_SHA256" \
  --source-binding "$PARENT_SOURCE_BINDING" --source-binding-pin "$PARENT_SOURCE_BINDING_SHA256" \
  --resolution "$PARENT_METADATA_RESOLUTION" --resolution-pin "$PARENT_METADATA_RESOLUTION_SHA256"
```

This emits only source-derived expectation receipts beneath the frozen capture's fresh `expectation-receipts/` directory. The publisher is production-only and refused fixture completion in QA. It has not been positively exercised against a real product because none was supplied.

The parent then reviews all actual origins/receipts and publishes the `asus-fs-parent-admission/v1` file and its external fixed SHA256. Merely computing the hash of an unreviewed JSON file does not confer admission. This parser's trust root is that parent decision and pin.

## Plan, generate, execute

The production interface has no `--raw`, arbitrary guest paths, input command list, or fixture switch. Each missing input fails closed before creating a header. All fields are mandatory; the later complete/source/content/metadata/terminal documents must bind one group.

Default invocation performs only admission and read-only header/identity checks, prints the plan, and emits no production observer input:

```sh
python3 -B "$PREP/scripts/full_system.py" \
  --admission "$PARENT_ADMISSION" --admission-pin "$PARENT_ADMISSION_SHA256"
```

Optional generation-only inspection, in a fresh owned directory:

```sh
python3 -B "$PREP/scripts/full_system.py" --mode GENERATE \
  --admission "$PARENT_ADMISSION" --admission-pin "$PARENT_ADMISSION_SHA256" \
  --output "$PREP/runs/r9-generated-01"
```

When the parent explicitly elects the actual filesystem test, execute in a different fresh directory. This generates the admitted observer, then performs the real read-only mount test. It does not copy the raw image:

```sh
python3 -B "$PREP/scripts/full_system.py" --mode EXECUTE \
  --admission "$PARENT_ADMISSION" --admission-pin "$PARENT_ADMISSION_SHA256" \
  --output "$PREP/runs/r9-full-fs-01"
```

The runner fixes QEMU's file and raw block nodes to read-only, uses only `complete.raw_system.path`, verifies host identities before/after, and retains exact argv/serial/generation/result. Kernel c59e/config0426746d are rechecked; no virtual config is deployed. The observer uses only its fixed four public paths, opens each component without following symlinks, reads to EOF in 64 KiB buffers with SHA256, checks exact bytes/stat/xattrs, confirms EROFS, and unmounts. No product binary is executed. Files exceeding 16 MiB or total expected bytes above 32 MiB require a separately reviewed scope change.

Required runtime evidence is exactly one `FULL_SYSTEM_FS_RESULT failures=0 scope=GENUINE_COMPLETED_PRODUCT`, exactly one `FULL_SYSTEM_FS_EXIT status=0 scope=GENUINE_COMPLETED_PRODUCT` from the PID-1 wait status, QEMU exit 0 without timeout, unchanged admitted host identities, and no kernel ext4/I/O/panic error. QEMU exit 0 alone is insufficient: both negative controls power off cleanly while the observer child exits 1. All four content, metadata and security-xattr checks must pass; capability absence must explicitly be expected and return ENODATA. `selinux=0` is a retrieval-mechanism fixture adaptation, not enforcing-policy acceptance.

## Separate final host check

The host check remains separate from guest acceptance and defaults to PLAN_ONLY too:

```sh
python3 -B "$PREP/scripts/host_fsck.py" \
  --admission "$PARENT_ADMISSION" --admission-pin "$PARENT_ADMISSION_SHA256"
python3 -B "$PREP/scripts/host_fsck.py" --mode EXECUTE \
  --admission "$PARENT_ADMISSION" --admission-pin "$PARENT_ADMISSION_SHA256" \
  --output "$PREP/runs/r9-host-fsck-01"
```

This fixes the command to the pinned copied `e2fsck -f -n` and admitted raw path, retains its exit and identities, and performs no creation, repair, raw expansion or whole-image hash. Never use mke2fs, including `mke2fs -n`, as a checker of an owner artifact.

## Bounds and decision

Every remote process is pinned to one available host CPU with `RLIMIT_AS=1073741824`, `RLIMIT_CPU=60`, and a 90-second wall alarm/child timeout. QEMU has one Cortex-A53 vCPU, 384 MiB, single-thread TCG/16 MiB cache, no NIC, and no monitor. Compilers and guests run serially. No lifecycle operations on parent/cloud processes occur. Keep all large artifacts on the builder.

Admission/generation/interface refusal exits 2; completed observer failure exits the CLI 1; a successful observer or host check exits 0 for that **individual step**. The result always leaves `production_image_accepted`/`full_SYSTEM_accepted` false until the parent reconciles the separate genuine guest and host receipts. No helper claims whole Android runtime, wholekernel, hardware, physical boot, flashing readiness or GO.
