# Built corrected SD common core

The only runtime source change from `../2026-11-07-asus-offline-stock-fallback/` is `source/sd_mount.h`: require exact `removable=0` instead of `1`, plus the explaining comment. Every other source and every input is byte-identical. The helper includes `rescue.c`, so all four programs were rebuilt and all four actual binary hashes changed. Earlier spikes and the old deployment adapter remain untouched.

Pinned physical e9 Linux4.9 MMC `drivers/mmc/card/block.c` lines 3263–3277 leaves GENHD_FL_REMOVABLE unset for removable block devices with permanent media. Copied evidence: `evidence/mmc-media-flags.json`; actual block.c SHA256 `dbd9ec9f0063449a9b8e179fef7b7da22d2bf2f1f7b15cf7aac4cd0aaee97ca6`. This is the source-backed reason for exact zero, not a physical SD trial.

## Actual delivered products

| Product in artifacts/ | Bytes | SHA256 |
| --- | ---: | --- |
| os-rescue | 776472 | `9eb39bc4d160f42f52cafdae4b9a76739a06a67f1525696bf44a068fa9461a25` |
| rescue-sd | 775920 | `4a82061696558aafb7da08512913528b396b4c6cb2c1e2a8edc09c1d1ab75257` |
| rescue-sd-supervisor | 778224 | `c15fddcac86838986159baafb5695c9222aa7f12a0e57ba1c3309b85928623d6` |
| p10-restore | 775536 | `f69d60001ae81f92c0403dfa85242a5aef5d26a569042a7408eec07b185a4e05` |
| sepolicy | 391284 | `e559a17ee13b141ceca868df7311bee2e095cf340afee2fedb549d314b5cad11` |
| file_contexts.bin | 225637 | `23b72f009d21abd8222b65b573506d59f6b00228271316ad2fa62a672c26fbad` |
| common-rootfs.cpio.gz | 2125754 | `2c7cf027c140a63680b9f8abf7f80197e9ee63c03f5ebb2307a8e42ebd7cf856` |

`artifacts/ARTIFACTS.json` records those actual bytes. `evidence/DELIVERY_PINS.json` SHA256 is `9f837a84b2b59f0cb9f2c117c2f697595c309c9991ab09de3dd8ffafa7c528aa`. `scripts/final_package.py` remains byte-identical to the old packager, SHA256 `382b753f9c0af7bad1f821a468c6e6ec5541544603b1a0ca2a9ee54efa7fecee`; its sibling-relative paths now resolve this corrected common core and its real refreshed delivery pins. Policy and compiled contexts were copied exactly and were not rebuilt or modified.

## Parent continuation: local only, after genuine admissions

From `/OWNER_HOME/Documents/workspace/ideas`, with variables pointing to the parent's actual inputs:

```sh
python3 -B 2026-11-07-asus-sd-media-flag-core/scripts/final_package.py \
  --manifest "$ASUSR002_MANIFEST" \
  --arm-file "$ASUS_SD_ARM_FILE" \
  --kernel "$ASUS_LINUX49_IMAGE_GZ_DTB" \
  --output-dir 2026-11-07-asus-sd-media-flag-core/artifacts/final
```

Output directory must not exist. This command was not executed. Genuine final SYSTEM/BOOT admissions are still pending. No candidate, final manifest, arm ID or binding was fabricated. Do not send private DATA or its table/manifest to the VM. The unchanged packager requires the genuine five-role ASUSR002 manifest, actual original-pair prefix, exact role geometry/chunk records and real parent arm ID. It retains final DATA SHA256 `cf433efa509f09814bff0877368f0c1b811b7615eefd3cd2a02f58b57995131b` (11331268096 bytes), exact original manifest SHA256 `605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47`, physical e9 kernel SHA256 `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`, and config SHA256 `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`.

The common rootfs still lacks final manifest/arm/current binding and automatic selector startup. Final local assembly emits the actual current binding and exact mode/trigger files as described in the earlier fallback HANDOFF.md. All byte-join, LK/MTK/layout checks and source pins remain unchanged.

## Smallest old deployment adapter integration

Apply only these two assignments in `../2026-11-07-asus-final-sd-wifi-deployment/source/admission.py` when root integrates:

```python
CORE = WORK / '2026-11-07-asus-sd-media-flag-core'
DELIVERY_SHA = '9f837a84b2b59f0cb9f2c117c2f697595c309c9991ab09de3dd8ffafa7c528aa'
```

`DEFAULT_ASSEMBLY` follows CORE automatically. All SOURCE_PINS remain identical. The exact unapplied patch is `evidence/admission.patch`; the old adapter was not edited. Its admission behavior still needs the genuine final product before it can run.

## Minimal actual verification and preserved behavior

`evidence/build-log.json` records four successful serial static AArch64 compilation/link commands with existing `aarch64-linux-gnu-gcc`, one host test compile, two focused fixture executions and the common-rootfs rebuild. `evidence/elf.json` confirms static AArch64 ET_EXEC with no dynamic/interpreter dependency. The two actual-header fixture cases accept valid removable=0 SD with canonical links, parent and fixed dev179:32/33 plus VFAT mount identity, and refuse that same fixture when type changes to MMC. These are host fixtures, not physical qualification.

`evidence/local-check.json` records exact source delta, all other sources/inputs byte-identical, unchanged packager/assembler, exact policy/contexts, actual artifact hashes, and archive comparison. Only the four sbin executable contents differ inside the actual common rootfs; all other entries, modes and ownership are unchanged. `evidence/source.patch` contains the complete runtime source diff. No exhaustive suites/reviews were run.

SD type=SD, mmcblk1p1 only, config32 fixed179:32/33, canonical links/parent, internal-device distinction, size bounds and mounted VFAT identity remain. Manifest/source/chunk/readback/terminal/p10 safeguards, normal order SYSTEM2→DATA4→BOOT3 and actual child exit0 before reboot remain. Normal installation retains custom recovery. Deliberate stock selection remains SYSTEM0→BOOT1→writer retirement/lock transfer→fixed original-p10 helper→durable OEM_RESET_REQUIRED→flush/unmount→power-off. No new permissions, arm flags, approvals, retries, defaults or fallback-on-failure were introduced. Full detailed layout/runtime contracts remain in the earlier fallback HANDOFF.md and unchanged source.

All remote writes/builds were confined to new owned `/srv/android/asus-sd-media-flag-core-20261107`, through the existing fixed SSH helper. One CPU, serial jobs, own-process 95MiB address-space cap, recorded owned allocation 8482816 bytes (<96MiB). Local delivery contains only compact core products; no recovery duplication or large image. No kernel/platform/native/Soong/Ninja build, active source/out/cache modification, process inspection/control, device/ADB/USB/card/cloud lifecycle or excluded PCM/private data operations occurred. Separate SD probe folders were not touched. Physical boot/card/flash GO remains absent.
