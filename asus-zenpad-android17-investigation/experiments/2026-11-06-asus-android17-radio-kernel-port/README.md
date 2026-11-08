# MT8163 radio kernel port

Question: can the ASUS CONSYS_8163 BTIF WMT/STP and AHB gen2 WLAN implementation run with the pinned Linux 4.9 / Android 17 product?

Status: **implemented and ARM64 compiled; hardware and Android product integration unvalidated**. The isolated full kernel builds through `Image.gz-dtb`; all selected radio objects link. A matching source-built ARM64 static loader/resident server is included. The current verification run passes 815 checks, including patch replay and three behavior suites. This is not a flash-ready full-product image or proof of functioning radios on the tablet.

Read [REPORT.md](REPORT.md) for the implementation, exact integration order, ABI changes, compiler evidence, limitations and runtime gates. [PROVENANCE.md](PROVENANCE.md) describes source and blob licences. No device, ADB, charging, calibration transfer, cloud-lifecycle or main-product operation was performed.

Important outputs:

- `patches/0001-import-asus-mt8163-radio.patch`, then `0002-wire-mt8163-radio-kbuild.patch`: 244 imported files and two changed existing Kbuild/config files, against `717bb3c9e13ce573cfdd2dda856debd27a0fa17f`.
- `staged/device/asus/p00a/radio/`: loader/server, firmware protocol, narrow read-only BT record provider, scoped ASUS library adaptation, Android.bp/init/VINTF/policy inputs.
- `evidence/linux-build/`: actual ARM64 image, linked radio object, config, System.map, compiler logs/exit codes and static loader executable.
- `evidence/verification.json`, `protocol-tests.json`, `power-tests.json`, `bt-record-tests.json`: host evidence; hardware primitives are simulated in host tests.
- `artifacts/radio-source-bundle.tar.gz`: deterministic source/integration/evidence bundle and adjacent SHA256 file.

Continue with `python3 scripts/verify.py`. Preflight a separate kernel using `python3 scripts/apply.py /path/to/kernel`; add `--apply` only to apply. This checks exact touched-file preimages and refuses conflicts. Do not copy the whole `kernel-input` overlay onto a parent's changed tree. The original prepare/adapt scripts are retained as development history; the final two patches and manifest are the authoritative reproducible result.

The only remote fixture owned here is `/srv/android/asus-radio-kernel-port`, with `kernel`, `build`, `userspace`, and `logs` subdirectories. It was created by `git archive` of the pinned commit, never by copying the active working tree or build output. Build with `-j2`. `scripts/remote.py` contains the established VM SSH options; it does not contain a key. Parent/main-build ownership and all physical/cloud operations remain outside this spike.
