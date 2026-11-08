# Pending commands and inputs — DO NOT RUN YET

Parent review must first accept the concrete retained closure in `DEPENDENCIES.md`. No new unresolved-decision model was invoked; the prior Opus whole-plan advice was read. If a keeper/design decision remains unresolved, parent consults Opus first, Large only upon refusal, before authorizing one build. There is no physical GO from this preparation.

The exact existing VM `PROJECT_REDACTED/us-central1-a/PROJECT_REDACTED`, ID `8549823276971553556`, IP `IP_REDACTED`, is now verified TERMINATED. Future operations must retain that identity check, the pinned `remote.py` SHA `c22884576a780cbb1ddf5e1b02f0b6e9d6eb5c25f8d9bc82fb077543f05cf4ab`, an owned short SSH master, and stop verification. Do not replay this spike's acquisition/resolution scripts: their one-use guards are intentional.

Prepared remote prefix: `/srv/android/asus-minimal-platform-preparation-20261108`. It contains an independent ordinary source copy and configuration-only `out` with `.config`/`.config.old`; no out tree copy, new Image, new vmlinux or helper executable. `helper/{ram_pid1.c,run_identity.h}` and the proposed kernel files match `evidence/08_freeze_design.json`.

Verify the prepared hashes against that receipt and the final config SHA `04d93e9d2864f23d9fb5a9dcc0958be39e69f07a43d20b1a428042a098893314`. The single `minimal-platform.delta.patch` reconstructs the same source/config/helper delta when applied at an independent prefix containing `kernel/` copied from the calibrated ancestor and `out/.config` copied from its old output. Do not apply it to the ancestor or latest battery-uevent revision.

After explicit parent authorization, the pending commands on the exact VM are:

```sh
unset MAKEFLAGS MFLAGS KBUILD_OUTPUT KCONFIG_CONFIG LOCALVERSION CROSS_COMPILE KBUILD_BUILD_TIMESTAMP KBUILD_BUILD_VERSION
export TMPDIR=/srv/android/asus-minimal-platform-preparation-20261108/tmp
export KBUILD_BUILD_VERSION=1
make -C /srv/android/asus-minimal-platform-preparation-20261108/kernel \
  O=/srv/android/asus-minimal-platform-preparation-20261108/out \
  ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ \
  LOCALVERSION=-minplat -j8 Image.gz-dtb

aarch64-linux-gnu-gcc -static -Os -std=gnu11 -Wall -Wextra -Werror -fno-ident \
  -I/srv/android/asus-minimal-platform-preparation-20261108/helper \
  -o /srv/android/asus-minimal-platform-preparation-20261108/helper/init \
  /srv/android/asus-minimal-platform-preparation-20261108/helper/ram_pid1.c
```

These commands have not run, including syntax-only compilation. The helper's static libc/toolchain availability and C diagnostics remain untested. Preserve failure evidence and stop rather than automatically repairing/rebuilding or trying a second configuration. The anticipated release is `4.9.337-asus-p00a-experimental-minplat`; generated UTS_RELEASE must match the entry tag or the build is not packageable as prepared. Collect actual artifact hashes only after real output exists.

Before any later packaging authorization, check the actual linked artifact for entry ABI/geometry and ordinary writer path, absent early 8250 console and unchanged watchdog initcall behavior; source/config pins; expected removed consumers; preserved thermal/charger/reset symbol/call paths; exact DT differences, addresses, reservations and selected bootargs. Warning-free olddefconfig and ancestor disassembly do not replace those checks. A link/dependency conflict stops the one build for review; do not add stubs or remove keepers to obtain a successful image.

Packaging is a separate future action, with no packaging command supplied here. The old packager must not be rerun: it intentionally preserves the old USB helper, old full config and byte-identical old DT. A later package must use the newly compiled DT and this helper while preserving Android/MTK wrapper load addresses, bounded DT/memory admission and the existing transport/installation guard boundary. Baseline Android loads are kernel `0x40080000`, ramdisk `0x44000000`, second `0x40f00000`, tags `0x4e000000`, 2048-byte pages (see `evidence/load-contract.json`).

Preserve RAM bank `0x40000000..0xbd600000`, retained console `0x44400000..0x44480000`, minirdump and all other reservations, including secure pool `0xb3400000..0xbd400000`. Preserve the initrd start `0x44000000`; derive the new exact payload/end from the real future ramdisk, excluding its 512-byte wrapper, within the pre-console window (end at or below `0x44400000`) and with all original nonoverlap/size checks. The ancestor end `0x4403f007` describes its old payload, not the future helper. No arbitrary memory admission or guard deletion.

Selected Android header and runtime DT command line before exact initrd geometry is added:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3 console=null maxcpus=1 nr_cpus=1
```

Use the same selection in the config fallback and board DT. Do not revive `ttyMT0`, earlycon, initcall_debug, nohlt/FIFO/directclock, polling budgets or diagnostics. No compiled Image/helper/ramdisk/DTB/package hash is predicted by this design. Latest physical recovery remains the owner-supplied full-p10 hash `d78e6ddd7f4a555201515df3aef6d8d7f15203c20e3b8d201ea7eb2f4c5df081`; it was not contacted or read back here. Any installer preimage decision belongs to later authorized work.
