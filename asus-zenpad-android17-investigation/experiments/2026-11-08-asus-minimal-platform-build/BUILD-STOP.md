# Compiler failure handoff

One helper compile succeeded. One kernel compile was dispatched and returned exit 2. The first failing translation unit was `drivers/misc/mediatek/devapc/mt8163/devapc.c`:

```text
122:49: error: unknown type name ‘E_MASK_DOM’
123:33: error: unknown type name ‘APC_ATTR’
164:12: error: ‘clear_vio_status’ defined but not used [-Werror=unused-function]
139:13: error: ‘init_devpac’ defined but not used [-Werror=unused-function]
134:12: error: ‘unmask_module_irq’ defined but not used [-Werror=unused-function]
```

The source places these declarations in `#ifndef CONFIG_MTK_IN_HOUSE_TEE_SUPPORT`, inside the non-Trustonic branch. The accepted configuration keeps DEVAPC and disables the in-house TEE consumer. The local declaration header has no `E_MASK_DOM` or `APC_ATTR` types. This branch was not exposed by the earlier TEE-enabled ancestor. The failure is more than a warning-policy mismatch: the two unknown types independently prevent compilation. This bounded evidence collection read only the failed source and its local header; it did not audit or repair other drivers.

Exact command that ran once:

```sh
make -C /srv/android/asus-minimal-platform-build-20261108/kernel \
  O=/srv/android/asus-minimal-platform-build-20261108/out \
  ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- HOSTCC=gcc HOSTCXX=g++ \
  LOCALVERSION=-minplat -j8 Image.gz-dtb
```

No address-space limit or timeout-kill was introduced. The process completed naturally; parallel jobs finished before evidence collection. Build timestamps, status, command and complete log are preserved. The config after make is exactly the parent SHA `add8f8e85e0fe007364da835f2d45d91663551876387ba4a695e410d4c1cc7bb`.

Genuine helper command that ran once, without source edits after the authoritative parent overlay:

```sh
aarch64-linux-gnu-gcc -static -Os -std=gnu11 -Wall -Wextra -Werror -fno-ident \
  -I/srv/android/asus-minimal-platform-build-20261108/helper \
  -o /srv/android/asus-minimal-platform-build-20261108/helper/init \
  /srv/android/asus-minimal-platform-build-20261108/helper/ram_pid1.c
```

The helper's source, static ELF/readelf, main/handler disassembly and checksum reference are retained. No ARM64 code was executed. The real initramfs has only `init`, `dev`, `proc`. Its wrapper is not a recovery package. No target installer was generated; `source/adb` is the unchanged 0755 adapter only.

No final Image.gz-dtb, vmlinux, System.map, compiled/runtime DT, recovery candidate or full p10 exists for this attempt. Therefore linked keeper/removal validation, package/profile admission, isolated PLAN, strict decoder fixtures and any physical action were not performed. There are no candidate hashes to report. Generated UTS_RELEASE/compile headers are explicitly named `partial-*` evidence and do not imply a completed kernel.

The parent-supplied current installed full p10 remains `d78e6ddd7f4a555201515df3aef6d8d7f15203c20e3b8d201ea7eb2f4c5df081`; this unit made no fresh target observation. No installer preimages or common execute/Transport/Guard/adapters were changed. Previous recovery/Android installation and sources remain untouched.

The exact existing VM `PROJECT_REDACTED/us-central1-a/PROJECT_REDACTED`, ID `8549823276971553556`, was stopped after collecting failure evidence; `evidence/after.stdout` records `TERMINATED`. `/tmp/asumbld-1108` was this spike's only master and is closed. Partial artifacts remain at `/srv/android/asus-minimal-platform-build-20261108` for later authorized review.

Parent's immediate read-only commands:

```sh
cat 2026-11-08-asus-minimal-platform-build/evidence/failure-receipt.json
cat 2026-11-08-asus-minimal-platform-build/evidence/helper-verification.json
shasum -a 256 2026-11-08-asus-minimal-platform-build/artifacts/init
```

Do not rerun the make command or deliver partial artifacts to a device. Any DEVAPC/TEE/config repair requires the parent's new decision under the retained protection boundary. No proposed hardware-writing replacement or automatic alternate configuration is supplied here.
