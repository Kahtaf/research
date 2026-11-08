# Exact USB RAM reporter on stock 3.18.35

Question: does the exact existing RAM USB PID1 reporter work on the known-working stock kernel? This reporter has never passed a stock-kernel physical control. Status: **locally packaged; preservation/hash checks and exactly one isolated PLAN passed; no physical/fullOS GO**. Parent owns fresh identity/preimage checks and every physical operation. This task used only local public packaging inputs: no device, network, SSH, root, private-data content, installation, reboot, kernel build, C compilation, VM or broader test/review campaign. No further consultation occurred; the partial Opus response is not deployment approval.

Important outputs, with SHA-256 of the actual written/read-back files:

- `artifacts/candidate.img`: 7,737,344 bytes; `e7d5f3c93a1c94d0f27c3f19e7b29aab32d70d5139e296bad8ab749c3852c57e`.
- `artifacts/candidate.p10.raw`: 16,740,352 bytes, exact candidate followed by zero padding; `039c5a52d9ac04fd515c2081c455066057d1503d6979fc81a5b2c70712bc7dba`.
- `artifacts/ramdisk.wrapped`: 255,651 bytes; `51e6d1dc0acb742522c69b29355d2d77d8ba73a3597fb8ad3354fa9f0c494e49`. Extracted unchanged from `../2026-11-07-asus-linux49-usb-ram-report/artifacts/candidate.img`, verified SHA `6b8c2d1c41685c7592a4aa42cd809e070e8033c0226febb9137285ef4e379f5d`. Neither the wrapper nor compressed payload was regenerated. `/init` remains 597,856 bytes, static AArch64 ELF, SHA `d081c46dcf40684b35ec5f16bb4238b60662dd857a7211d46241e98f96ac872b`.
- [Packaging receipt](evidence/packaging-receipt.json): pinned inputs, actual component/output hashes, exact byte offsets, metadata changes and preservation assertions.
- [PLAN output](evidence/install-plan.json) and [isolation receipt](evidence/plan-isolation-receipt.json): one actual delivered installer `main()` call, exit 0, `PLAN_ONLY`, `device_contacted=false`, `reboot=false`.
- [Installer diff](source/install.diff), `scripts/build.py`, `scripts/plan_only.py`, and `SHA256SUMS` support local reproduction and handoff.

The source stock image is `../2026-11-07-asus-stock-kernel-version-control/artifacts/original.img`, 7,804,928 bytes, SHA `f0bf4834a2d3ec207590c6742d0adb4fd9a3adc9a2dab5d0ec7c28f27963b140`. Its exact 7,414,580-byte gzip stream is retained, SHA `1392786809c70332e92b1838f913a04fa4b4ad3ea02511a5bbe732a8c28a84cf`; decompression still yields the unchanged 16,963,568-byte stock Image, SHA `db90ee7fff379f35ac2b0aafb11a6abee7b2c283b57d352c40ae7c6d7c35eb2a`. No recompression or kernel-code/data mutation occurred. The exact 512-byte kernel wrapper is retained.

The only FDT change replaces the existing `/chosen/bootargs` token `initrd=0x44000200,0x200000` with `initrd=0x44000200,0x03e4a3`. The leading zero preserves its text width. This changes six bytes at FDT offsets 54,929–54,934 (wrapped-kernel offsets 7,470,021–7,470,026). FDT length remains 62,482 bytes, and every other property, token, reservation, string and hardware byte is exact. No `linux,initrd-start` or `linux,initrd-end` properties are added. FDT SHA changes from `77e2d8fbeced5a827ede6c0b8589140e9211d8dc3ca77aaa31a1dd1787a9c455` to `cf58f4b22c9edb149424ffaca6201d5fee12332ab4c25d818a97996f488461bc`. Consequently the complete wrapped-kernel SHA changes from `d585f856946b4f4e02f95e7ef796423a046ce7c0c2a661680abd87b8b5326952` to `3ed4cfa61ee6e0f7229ce148381f8e6a29c8ad15eb3e360070d6fbb49b5344e4`; its length stays 7,477,574 bytes.

The stock initrd pointer starts at the compressed payload, **after** the MTK wrapper: wrapper load address `0x44000000`, payload start `0x44000200`, exact payload length 255,139 (`0x3e4a3`), exclusive end `0x4403e6a3`. The 512 wrapper bytes are excluded from the bound. Payload SHA is `80333fefe8beda9395f9181a0485218284468546914f573cd79fa15399538cf2`.

Android header changes are limited to ramdisk length (322,200 → 255,651; changed bytes 16–18) and required image ID (changed bytes 576–595). The ID becomes `260a598f810e33a163a9c0dbaaef81b3cef0e1ab000000000000000000000000`. Kernel length, all load addresses, page size 2048, and all other header bytes are exact. Component alignment uses zero padding for the replacement ramdisk. The exact stock header command line remains:

```text
androidboot.selinux=permissive bootopt=64S3,32N2,64N2 build_version=3
```

The stock FDT command line remains `console=ttyS0,921600n1 root=/dev/ram` plus the length-adjusted existing initrd token. The stock header already included its permissive setting; no 4.9 command line, `console=null`, or `maxcpus=1` was imported.

The reporter helper, C, run, USB configuration and nominal 60-second reboot attempt are unchanged. Run `9342cbf1-3bf0-44d4-b655-a1ca30146a99`; serial `P499342cbf13bf044d4b655`; VID:PID `0b05:4a49`; product `ASUS-PID1:<actual uname.release>`; FAT label `P49RAM`; report `PROBE.TXT`. The read-only RAM medium and actual uname-derived report/product remain the existing reporter's behavior. Its physical automatic return and exact physical fallback remain unqualified.

[Direct capability evidence](../2026-11-07-asus-stock-usb-direct-capabilities/evidence.json) and its [README](../2026-11-07-asus-stock-usb-direct-capabilities/README.md) establish linked stock configfs/gadget/mass-storage implementation and runtime filesystem registration. Literal original config flags remain unavailable; none were invented. These capabilities do not establish that this exact reporter works physically.

`source/install.py` is minimally specialized from `../2026-11-07-asus-early-watchdog-handoff/source/install.py`: exactly five literal replacements update compact SHA, full-p10 SHA, compact length, journal profile, and the preimage tuple. The supplied currently installed p10 hash `81bc90ed8f8c25a291c8ffca205de94a0188b5cbab37379b3f667ad1ac42ba2d` is appended; all existing admissions remain, including original stock recovery `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20`. The actual imported tuple was checked in the single isolated PLAN. No current device state was observed here. `execute()`, `Transport`, and `Guard` source blocks and both legacy adapters are byte-identical. The inherited guards, complete readback, bounded inverse, uncertainty stop, mutation lock and no-reboot behavior remain. No new private source or root helper was copied. The inherited adb shim still targets the existing wifi-microsd legacy adapter; its sibling source/transport dependencies must stay in place. Inherited SD wording is retained in installer descriptions/errors.

The isolated PLAN follows the prior `scripts/plan_only.py` approach: **only in memory**, `b.local_inputs` supplied the pinned public stock image for header geometry, and `a.check_sources` was replaced by a no-op to avoid root-helper manifest reads. The delivered installer and its guards were not modified by PLAN. An audit hook prohibited private/device paths, subprocesses and network operations. Original private stock backup and restricted source/dependency hashes were deliberately not validated. This isolated PLAN is not a complete live installer preflight or approval.

Continuation: parent first performs fresh identity and complete current-p10 preimage checks through its existing authorized workflow. Parent owns the decision to run the following next installer command, which was **not executed here**, and all later boot/observation/fallback operations:

```sh
python3 -B /OWNER_HOME/Documents/workspace/ideas/2026-11-07-asus-stock-exact-usb-reporter-control/source/install.py --execute
```

The unchanged reporter deliberately reuses the original run and USB identity; parent must establish a fresh physical observation, not accept an old host report. A positive stock control validates this reporter on stock, not every 4.9 ABI or environment assumption. A negative stock control makes prior absent USB reports insufficient to blame 4.9: stop creating additional 4.9 variants until the reporter works. Packaging and PLAN alone settle neither result.

Local packaging can be reproduced with `python3 -B scripts/build.py` from this spike. `scripts/plan_only.py` refuses a second PLAN while its receipt exists; this delivery already contains the single required run. Repackaging overwrites local artifacts/packaging receipt; regenerate `SHA256SUMS` if any delivery changes. No additional tests or physical trial are part of this handoff.
