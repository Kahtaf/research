# Stock USB reporter: two read-only preconditions

Question: does the exact shipped stock 3.18.35 kernel have the four required builtins, and does the verified running stock Android expose exactly one UDC directory entry?

Status: **UNKNOWN_INPUT_REQUIRED**. One bounded preflight ran on 2026-11-07. No calibration was executed. This covers only the two concrete checks delivered in the [consultation](../2026-11-07-asus-opus-next-step/calibration/CLAUDE-CALIBRATION-RECOMMENDATION.md); its remaining advice was not delivered.

The pinned public `original.img` hash matched `f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140`. Its decompressed actual stock Image matched `db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a`. This input is a recompressed unchanged stock Image with a diagnostic ramdisk, not an original full partition. Android image ID, 512-byte MTK kernel wrapper, one gzip stream, and appended FDT framing were checked. The Image has zero `IKCFG_ST` markers. The one unprivileged `/proc/config.gz` fallback returned “No such file or directory” (remote exit 1, host exit 0, complete nonce frame; remote stderr merged into stdout by legacy shell transport).

All four config values are **UNKNOWN**: `CONFIG_CONFIGFS_FS`, `CONFIG_USB_CONFIGFS`, `CONFIG_USB_CONFIGFS_MASS_STORAGE`, and `CONFIG_TMPFS`. No exact config was obtained, so there is no config hash or extracted config file. No reference defconfig was substituted. Missing embedded config is not evidence of an unsupported feature.

Fresh stock identity matched serial `DEVICE_SERIAL_REDACTED`, device `P00A_2`, SDK `24`, boot completed `1`, secure ADB `1`, SELinux `Enforcing`, and kernel `3.18.35`. The freshly read boot UUID was `3525090a-4d53-4ec6-b704-7ba459bdc610`, equal to the previously verified boot. Exactly one directory listing of `/sys/class/udc` returned one controller: `musb-hdrc.0.auto`. No controller attributes were read. The pinned ADB executable matched its expected hash and the existing server on 5037 answered a read-only version query; no server restart was requested.

Outputs:

- `scripts/preflight.py`: rerunnable host script using Python's standard library and the pinned ADB client.
- `evidence.json`: actual hashes, config unknowns, fresh identity, controller name/count, nonce framing, and exact failure output. Explicit remote exit/framing fields were decoded from the collected frames without another device observation.

Rerun, only when another observation of these same two checks is wanted:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-usb-reporter-preflight/scripts/preflight.py
```

It overwrites this spike's evidence, performs no retries, refuses unexpected device identity, and never invokes root. An exact config, if obtained on a future run, is saved with its SHA-256 and selected values. Original inputs are read only. The run made only the identity read, one UDC directory listing, and one permitted unprivileged config read on the device.

Continuation / next decision: **stop before calibration; parent must supply the exact shipped 3.18.35 config.** No deployment or physical-readiness approval follows from this preflight. The exact USB reporter has never physically passed a positive control, so its absence on experimental 4.9 alone does not prove kernel failure.
