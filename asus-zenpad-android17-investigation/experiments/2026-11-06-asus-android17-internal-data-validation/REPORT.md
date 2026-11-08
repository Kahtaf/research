# Full-size internal A17DATA validation

**PASS for full-size host construction and the matching Linux 4.9 filesystem runtime workloads.** The pristine raw image exists on the existing VM. Two independent QEMU boots used the same disposable full-size clone and passed mount, durability, permissions, direct I/O, real APEX loop/dm-verity reads and clean unmount. This result does not depend on the stock-system backup or the concurrent full Android build. No physical device operations occurred.

## Artifact for parent integration

Remote pristine image:
`/srv/android/asus-internal-data-validation/artifacts/A17DATA-pristine.raw`

- Exact raw length: **11,331,268,096 bytes**.
- SHA-256: **`1602ea3644246871468b6987bc90e9a6e0c430f6b46efb4e79cc3555b688e0c1`**.
- Primary manifest: `evidence/image-manifest.json`, locally and under the remote fixture root. It records **338 chunks of at most 32 MiB**, explicit offsets and lengths, actual per-chunk SHA-256, the full hash, tool pin and formatter argv. The last chunk starts at 11,307,843,584 and contains 23,424,512 bytes.
- Fixed p26 geometry: start sector **8,404,264**, **22,131,383** sectors of **512** bytes. Filesystem: **2,766,422 × 4096 = 11,331,264,512 bytes**, followed by exactly **3584 zero bytes**.
- UUID `be11dc64-b759-40a3-af67-1236cc8cb655`; label `A17DATA`; inode size 256; zero reserved blocks; pristine root 0:0/0755.

The image is an ordinary sparse host file, initially exclusively created mode 0600 and now mode 0400. It has never been attached writable to a guest. Its original full hash was independently reread with `sha256sum`; after both guest boots, another complete read reproduced the full hash and every 32 MiB chunk hash. Read-only mode is an operational guard, not a claim that the owning account cannot deliberately chmod it. Root contents are only `.`/`..` and `lost+found`: no QA sentinels, APEXes, calibration, keys or Android-ready properties are present in the pristine image.

**Sparse holes describe zero-valued input bytes, not permission to skip target writes.** Parent must materialize every raw byte on p26, including holes and the final 3584 bytes, and verify all 11,331,268,096 destination bytes. Neither flashing nor a physical destination readback was performed here.

The older `os-rescue/source/rescue.py` reference controller uses **1 MiB** frames, whereas this task requires a 32 MiB artifact manifest. `evidence/fresh_userdata.reference-1MiB.json` is an additional exact `{bytes, sha256, chunks}` fragment for its `images.fresh_userdata` slot. It was derived from another complete image read and checked against both the full hash and all 32 MiB groups. It contains no approval, device identity, backup receipts or invented runtime gates. Parent must match the actual qualified rescue protocol rather than treating the primary 32 MiB manifest as a drop-in controller manifest.

## Host construction and checks

`source/image.py` implements the fixed recipe and inspector. There is no formatter target argument or device adapter. Its only build output is the fixed new file inside this fixture. It rejects paths outside the fixture, `..`, symlink ancestors, nonregular files and existing output paths; creation uses `O_EXCL|O_NOFOLLOW`. It fsyncs the raw file and containing directory.

The actual formatter was `/usr/sbin/mke2fs`, **1.47.0 (5-Feb-2023)**, SHA-256 `07cd24ce58a410cc9cee93c55ae5ac95986df016c5907dc7a49b55389bd41ed2`. Its identity was checked against the captured tool pin before use. The captured config SHA-256 is `def9e1d4dbf51f44c51303349338086cf23d60c3cc7e9e99442ee554eb9f5de6`.

Actual recipe, with `MKE2FS_CONFIG` pointing at this fixture's captured config and `E2FSPROGS_FAKE_TIME=1793952000`:

```sh
/usr/sbin/mke2fs -t ext4 -b 4096 -I 256 -m 0 -L A17DATA \
  -U be11dc64-b759-40a3-af67-1236cc8cb655 \
  -O none,has_journal,ext_attr,dir_index,filetype,extent,sparse_super,large_file,uninit_bg,dir_nlink,extra_isize \
  -E nodiscard,lazy_itable_init=0,lazy_journal_init=0,root_owner=0:0 \
  -- /srv/android/asus-internal-data-validation/artifacts/A17DATA-pristine.raw 2766422
```

The exact masks are **compat 0x2c, incompat 0x42, ro_compat 0x73**. No 64bit, encrypt, verity, metadata_csum_seed or orphan_file features are present. The inspector validates exact partition/filesystem geometry, UUID/label, inode sizing/count, clean state, all **85 group descriptor bounds**, bitmap/table separation, every inode-table and bitmap read, root inode and tail. There are **692,240 inodes**. Additional read-only inspection validates root/journal extent trees and their bounds. The 64 MiB journal has a real JBD2 header followed by **16,383 zero blocks**, and all inode tables carry the initialized/zeroed flag. `debugfs` confirms the empty root listing.

`e2fsck -fn` returned **0**, with all five passes successful: 11/692240 files, 59844/2766422 blocks. `dumpe2fs`, formatter output, independent reread and allocation evidence are preserved. The recipe is reproducible; a future newly formatted image may have a different hash because formatter-generated seeds are not all fixed. The delivered image and manifest are the exact frozen artifact.

`source/test_image.py` ran **18 negative cases** against a separate host clone. It rejected unsupported feature masks, wrong root UID/mode, wrong block count/inode size, a final-group inode table extending beyond the filesystem, nonzero tail, short/long raw lengths, output collisions, symlink input/output/parent, device/outside-root paths, traversal and directory inputs. It never opens the rejected `/dev/null` path. Results are in `evidence/negative-tests.json`.

## Actual runtime qualification

Successful run: remote `r2`, captured locally as `evidence/runtime-r2`. The two result files and serial logs are authoritative. Both QEMU exits are **0**, both guest failure counts **0**, both post-unmount `e2fsck -fn` exits **0**, with no timeouts. `r1` was a compile-only failure caused by misleading C indentation under `-Werror`; braces corrected it before any guest ran. Its log remains preserved.

The frozen kernel SHA-256 is `113c4f19c736b949626c62bbf68cf23c9e3c5a821ec6ab031a5684cdcba14431`, reporting **Linux 4.9.337**. This is a byte-checked copy of the prior passing build-r4 kernel. The existing prerequisite report establishes its 58 matching physical configuration values and 282 matching subsystem source files; the sole whole-tree difference was the generic GIC guard. No kernel was built or patched here. The final physical combined kernel still needs its own equivalence/acceptance gate.

Each boot uses QEMU `virt,gic-version=3`, Cortex-A53, **2 vCPUs, 1536 MiB**, no NIC, one full-size QA disk, `cache=none`, a static init fixture and captured genuine SDK37 linker/libc/toybox. Exact commands and input hashes are recorded. The clone initially matched the pristine full hash. The second boot attaches the same clone after the first guest powered off and a read-only filesystem check completed.

Each guest reads the raw exact-size block device, superblock, every group bitmap and inode table, and trailing bytes before mounting. It mounts ext4 **read/write** with `nosuid,nodev,noatime,noauto_da_alloc,errors=remount-ro`. `statvfs` reports 4096-byte blocks and **2,706,583 usable filesystem blocks**; the difference from the raw superblock count is metadata overhead.

The filesystem-only directory requirements were derived from the captured real `system/core/rootdir/init.rc`, then independently matched to committed `system/core` revision **65d661b1a536701e8b118be4e9728d7b5ca727c9**. The numeric AIDs were checked against that revision's actual `android_filesystem_config.h`. The fixture performs the specified root transition to 1000:1000/0771 and checks **20 selected directories**, including vendor, misc, keystore, property, apex backing directories, system, media and CE/DE parent directories. Their source lines, modes, IDs and unexecuted encryption options are in `evidence/data-requirements.json`. A real child with UID/GID 1000 and no supplementary groups can open `/data/system` and is denied `/data/misc/keystore` with EACCES.

On boot 1, an aligned **8 MiB O_DIRECT pwrite** writes an ordinary deterministic sentinel on this full-size filesystem. It receives UID/GID 1000:1000, mode 0640 and `user.asus_fixture=durable-v1`; both the file and containing directory are fsynced. Aligned O_DIRECT reads verify every byte. Boot 2 checks the persisted data, xattr, file attributes, root and directory attributes again. Both actual toybox hashes match the host-derived digest `b6bf05c6218db64b47747a9913880dc53a4d7f08a2a20c200cae0772bcc4ae6a`.

The existing genuine adbd and Google GMS APEX inputs were copied read-only into this fixture, double-hash checked, then copied only onto the QA filesystem by boot 1. Each boot opens those files with O_DIRECT and configures actual loop devices at their real ZIP offsets. Both loops report **flags 21**, including DIRECT_IO. Each payload mounts first as EROFS over the loop and then as EROFS over its actual AVB-derived dm-verity mapping. Every boot passes **68 independently expected regular-file hashes**, including the complete 217,107,692-byte GMS APK: **136 matching hashes across both boots**. Active tables show `restart_on_corruption ignore_zero_blocks check_at_most_once`. Mappings are removed, loops released, and `/data` is cleanly unmounted before poweroff. The prior prerequisite fixture's corruption negative control is not newly claimed as a test here.

This fixture executes filesystem operations drawn from init; it does **not** execute Android init, apexd, Keymaster/keystore, property service, framework or product SELinux policy. The tested xattr is an ordinary `user.*` attribute. It does not establish security.selinux labeling, encryption=Require behavior in init, APEX activation/signature trust/namespace setup, or physical eMMC/4.9 compatibility. No Android readiness property is fabricated.

## Fstab integration

`source/fstab.internal-data.4.9.in` contains the correct line:

```fstab
/dev/block/platform/soc/11230000.mmc/by-name/userdata /data ext4 noatime,nosuid,nodev,noauto_da_alloc,errors=remount-ro wait,check,latemount
```

The full current candidate already uses this line. Do **not** replace it with the older template's `mtk-msdc.0/11230000.MSDC0` alias. `source/fstab.mt8163.proposed` retains every active entry, including first-stage read-only system and 512 MiB zram; `source/fstab-comment-update.patch` only updates stale data-migration comments. `evidence/fstab-validation.json` verifies this. No active AOSP file was changed. Main owner must preserve this behavior in all installed fstab copies and retain the real late-mount/service sequence.

## Stock rollback: evidence and limits

Captured OEM `init.mt8163.rc:78–83` creates the legacy MMC alias and calls `mount_all /fstab.mt8163`. The captured OEM boot/recovery fstabs use `forceencrypt=.../by-name/metadata` for userdata. Captured stock `init.rc` starts vold and has the real `vold.decrypt` post-fs-data/framework restart triggers. This proves the stock mount configuration and supporting init hooks; it does not prove the missing OEM system-side vold service configuration, effective properties or cryptfs execution.

The saved OEM recovery ELF was independently disassembled again. At **0x407fd0–0x408028**, an absolute key_loc is opened, sized by the helper and passed to the wipe function. The size helper uses **BLKGETSIZE64**; at **0x41b2b4** the discard range is `[0, whole length]`. With the captured recovery fstab, normal data reset therefore includes the entire **32 MiB p20 metadata partition**, not merely four footer bytes. Captured AOSP7 `roots.cpp:222–233` corroborates the key_loc wipe. Its recovery code also reformats data/cache and handles recovery/BCB bookkeeping. Any OEM-specific PreWipeData/PostWipeData hooks remain an additional exact-reset review consideration.

Captured AOSP7 `cryptfs.c:3262–3266` reads `ro.vold.wipe_on_crypt_fail` with default `0`; if it equals `1` on an encryption failure, it requests recovery `--wipe_data`. This is upstream reference behavior. The actual OEM vold executable/service rc and effective property value were not present in the inspected captured inputs, and the property was absent from the captured ramdisk rc/default.prop search. Its absence there does **not** prove the stock runtime value. No stock encryption or factory-reset runtime was performed.

The earlier report's four-byte magic invalidation was an agent's proposed narrow route, **not a user restriction or a requirement of this image**. User has authorized discarding old data. Parent may choose a legitimate standard OEM reset once its actual bounded effects are reviewed, including p20, cache and bookkeeping. This task imposes no new approval barrier and supplies no metadata writer. **Leave p20 untouched for the Android17 trial.** Stock re-encryption remains unproven until the actual stock runtime completes it; do not claim the new ext4 image alone proves rollback reinitialization.

## Reproduction and remaining parent gates

The complete raw image and QA disk remain remote. Local capture is compact evidence and source only. `source/setup_remote.py` documents input freezing into this new fixture; it refuses existing directories. `source/image.py build` refuses an existing output. Do not rerun setup/build over the qualified artifact. For an additional isolated runtime test, use a new unused revision in this fixture:

```sh
python3 /srv/android/asus-internal-data-validation/source/run_runtime.py r3
```

The runner builds only the small static init, creates a fresh full-size clone, performs both boots, checks e2fsck and material hashes, and verifies pristine bytes afterward. Preserve all completed run directories. Do not invoke or mutate the original runtime-prerequisites r6 path. The known SSH options are in `source/remote.py`; no key contents are copied or read by these scripts.

Parent owns the remaining physical gates: qualified/re-enterable rescue and authenticated exclusive writer; exact fresh device/GPT/CID/partition identity and bounds; complete verified rollback BOOT/SYSTEM/recovery materials as required by the chosen rescue; the final product fstab and real service/policy integration; full raw p26 materialization and complete readback; final combined physical-kernel acceptance. Product SELinux labeling, keystore/crypto, complete APEX startup and framework boot are separate gates. No device, ADB, USB, cloud lifecycle, calibration/private-data upload or active build-tree mutation occurred in this task.
