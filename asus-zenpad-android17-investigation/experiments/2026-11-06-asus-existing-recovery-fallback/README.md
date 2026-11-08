# Existing Z380M TWRP as a recovery fallback

Question: can a historical, exact Z380M recovery shorten the independent recovery path toward the first Android 17 boot?

Status: bounded investigation complete. A public archived primary maintainer post was recovered. Its exact recovery artifact was **unavailable through the checked public routes**, so it is **not a qualified candidate for a parent physical trial**. This is a recovery-tool lead only; the objective remains Android 17.

## Verified primary lead

The [2020-11-29 03:23:50 UTC Internet Archive snapshot](https://web.archive.org/web/20201129032350id_/https://forum.xda-developers.com/zenpad-8/development/twrp-custom-recovery-asus-zenpad-8-0-t3588765) contains diplomatic's first post, original post ID 71839234. The archived metadata identifies diplomatic as author, with original publication April 13, 2017 and modification June 4, 2020. The thread explicitly targets Z380M; a reply on that first page identifies Z380M P00A. The /e/ thread's P001 label does not establish identity with the actual P00A_2 target.

The maintainer identifies:

- Normal recovery: `twrp-3.2.1-0-z380m.zip`, attachment **4408923**, listed size **13.90 MB**, containing the named `twrp-3.2.1-0-z380m.img`.
- [Exact original ZIP URL](https://forum.xda-developers.com/attachment.php?attachmentid=4408923&d=1517718308).
- Separate Flash Tool package: `twrp-3.2.1-0-z380m-flashtool.zip`, attachment **4408924**. The maintainer restricts that special image to Flash Tool. Do not substitute it for the normal image in a parent's raw partition writer.
- Source attachment: `android_device_asus8163_ew_380.tar`, **4408925**. Scatter attachment: `asus8163_ew_380_Z380M_scatter.txt`, **4788946**. These are recorded leads, not downloaded or qualified inputs.

The February 3, 2018 update describes firmware **5.3.18** kernel provenance and TWRP 3.2.1 sources. The post claims locked-bootloader operation and functional ADB, touch and storage. It also reports a kernel configuration limit on initial ramdisk size, recommends keeping system read-only, warns of stock recovery's data-wipe entry behavior and Android's automatic stock-recovery replacement, and cautions about differing tethered-boot kernel parameters. These are historical maintainer claims, not measurements of this tablet or binary.

## Acquisition and identity decision

The current primary thread returned HTTP 403 to a direct public fetch; web fetch independently returned 502. Both the exact original ZIP URL and an explicitly recorded, inferred XenForo migrated URL returned **403 HTML**, not ZIP bytes. There was no login, cookie challenge solving, authenticated session or access-control bypass. Wayback availability returned empty snapshot objects for the attachment query with and without its timestamp, both schemeless and explicit HTTPS forms. That is evidence about these checked URL forms, not proof that no public copy exists anywhere.

Unauthenticated GitHub repository search for `z380m twrp` returned zero repositories. The broader `z380m` search returned the already-known Alpine project and ASUS kernel copy, with no recovery release established. The official Asus TWRP device list had no Z380/P00A/ZenPad entry. Exact-ZIP web search yielded no result. No alternate hardware artifact was downloaded.

**Rejected lead:** AndroidFileHost **673956719939831308**, `twrp-3.2.1-0-20180325-P024.img`. Its broad Z380KL/C/M grouping is not device qualification; P024 is unrelated hardware for this task. The search result appeared but no binary was requested.

## Static qualification and risks

No recovery ZIP/image was acquired. Therefore **there is no artifact SHA-256**, and all requested binary checks remain unperformed: Android header, MTK wrappers/signatures, image size versus p10, kernel architecture/release/hash, DT board identity, ramdisk fstab/init/adbd/default security, block paths/partition geometry, and startup write behavior. A filename and a 5.3.18 kernel claim do not prove compatibility with **P00A_2 WW 5.3.20** or equality with the known stock kernel. Public/stock helpers were not used to inspect private backups. No existing custom-rescue audit was expanded.

**Mandatory future entry gate:** the parent reports stale p12 recovery arguments `recovery\n--wipe_data`, whole-partition hash prefix `8d0cf5c...`, with command/status zero. This state was not reread here. Before any TWRP entry, the parent must clear/reconcile and verify these arguments through its separately owned BCB operation. Empty command/status and a system-read-only UI choice do not prove that TWRP will ignore recovery arguments, scripts, or other startup writes. Minimal PID1 ignoring the argument is not evidence that TWRP does. No BCB clearing or device operation was performed by this spike.

No TWRP physical trial is supported by this result. The smallest already-prepared physical discriminator remains the parent's **known-stock tiny RAM probe `535a`**, which can distinguish basic recovery/PID1/USB reachability from the failed custom rescue `3f99`; its deployment and return-to-stock guard belong to the parent. A future qualified TWRP's first physical discriminator would be basic recovery entry plus independent UI/ADB liveness and verified stock return, only after BCB/startup-write risks are resolved. This document grants no flash GO and adds no transport implementation.

## Important outputs and continuation

- `research/xda-archived-primary.body`: exact archived HTML, **215166 bytes**, SHA-256 **60494146497b8e5e4bd51d7aa1c508c6afd0fdac917a587c93fd8bfc42cb8eb8**.
- `research/maintainer-first-post.txt`: readable derived primary-post text; the original HTML is the provenance authority.
- `research/*.json`: per-fetch URLs, UTC timestamps, response status, byte counts and body SHA-256 values. Error-page hashes identify error pages, never recovery artifacts.
- `qa/acquisition-summary.json`: machine-readable decision and fetch summary.
- `qa/SHA256SUMS`: source/evidence checksums.
- `source/fetch_public.py`: public, unauthenticated finite fetch helper. It was invoked explicitly for **13 URLs**, returned **261367 body bytes**, and never executed downloaded material. Metadata fetches have 2 MiB caps; ZIP attempts had 32 MiB caps and yielded only small error pages. The work finished well inside ten minutes and 64 MiB.

Continue only if an exact maintainer-linked normal ZIP or a publicly archived copy becomes available. Preserve its URL chain and SHA-256, enforce ZIP <=32 MiB/image <=16.7 MiB and bounded decompression, inspect without execution, and compare only with authorized public stock inputs before considering a parent trial. Do not retry blocked routes endlessly, fetch a generic P001/P024 replacement, execute source/tools from attachments, or change the Android 17 objective.
