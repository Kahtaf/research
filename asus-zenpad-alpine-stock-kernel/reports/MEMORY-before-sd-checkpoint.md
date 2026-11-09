# ASUS Alpine handoff — 2026-11-08

## Latest live state — independent Alpine running

The tablet is NOW booted into independent Alpine PID1 on originalstock3.18.35, notAndroid/chroot. New bootID and pinnedLANSSH endpoint/key are in private/standalone-ssh.json. Use scripts/standalone-ssh.py (notoldAndroidrootwrapper) for currentdevicecommands; USBserial via scripts/capsule-serial-rpc.py is fallback. Recoveryinstalledimage is dac48be3...; laterbuilderartifacts differ and are NOT installed yet. OriginalnormalBOOT remains7bb68511..., GPT/SYSTEM/DATA/factory untouched; staleBCBwipe request cleared/readbackverified.

ColdWMTloader was run EXACTLYONCE; ioctl0x80047704=0 andstpwmtregistered. Launcherinitiallykilledbecausemdevhad reset/dev/urandom,etc to660rootroot. Runtimechmod666 standardnodes fixedit; restarted ONLYlauncher, neverloader. Stockpatchesdownloaded, wlan0created, nativeWPA/DHCP/TLS andhost-key-pinnedLANSSH/SQLite/HTTPS PASS (experiments11b/12). Sourceinit nowfixesdevpermissionsAFTERmdev andloUP; repeatbootautomaticproofpending. SDcal/privateprofilecopiesoriginalmatch.

FirefoxESR140.12 installed, defaultheadlessHTTPSrender PASS; artifact artifacts/firefox-standalone-https.png visuallyinspected. Packages~645MiB, currentRAMroot768MiB. GUIpersistentoverlayprepared; parentupload/startpending. /dev/shm192MiBtmpfs and/run/user/0(700) preparedforbrowser. Physicaltouchstillunverified.

Persistencehelper nowrunsinRAM/etc/asus-alpine/state.py. CardreopenedprotectedRW uid0gid0,nosuid,nodev,noexec,fmask0177,dmask0077; ownservice-data bound to/var/lib/asus-dashboard; stableEd25519hostkey saved underownprivate. DashboardPID/log in/run/asus-alpine. HTTPhealthverified; initialimmediatecurlracedstartup, laterhealthpassed. OpenSSH10.3 ssh-keygen-y emitsacomment; helperfixedtocomparefirsttwo public-keyfields. No privatekeyoutput. PERSISTENCE.ENABLE staged, nextbootintegrationpreparedbutnotverified.

Currentwork: persistenttouchdesktop + on-screenkeyboard; buildone1GiBext4rootfileonexistingSD (no repartition) soapps/normalLinuxfilespersist. Agent stock_ram_boot_capsule editingrecovery-init/build foroptionalROOT.EXT4.ENABLE; parenthandlesactualfilesystemcreation. ExcludeSYSTEM,/mnt,/proc,/sys,/dev,/run,/tmp,calibration/profiles andSSHhostkeys whencloningsoftware. Noadditionalcloud/kernelwork. GoalNOTcomplete: GUIphysicaltap, practicalJSworkload, persistentSDrootandrepeatbootstillpending.

Serialtransportlesson: nonblockingos.write mayreturnpartial. RPCnow sendsallbytesin256Bchunks andusesone-linebase64scriptpayload, handshakebeforedispatch. EarlierpartialmultilinecommandsproducedPS2prompts; oneexplicitinputresetwasdoneafterconfirmedunexecutedparse, notdevice/job restart. CurrentLANSSHstable, preferit.

## Current recovery RAM trial — deployment verified, boot next

Property gate is now physically proved in the sealed chroot: ready=no never opens stpwmt; ready=yes reaches expected ENOENT. Opus exact binary analysis and the paired traces establish the property-file workaround. Cold readiness now requires exactly one successful module-init ioctl plus registered stpwmt, never loader exit status. See reports/opus-wmt-readiness.md and private/live/experiment-10-property-gate.txt.

Recovery-only RAM capsule dac48be3cc2db22e2a099ef3948618f8561d737cc4bc2b49de14cd1ef5816cee has been written to p10 and FULL read-back matched. The backed-up stale BCB recovery arguments were cleared (20 nonzero bytes removed; command/status/reserved preserved) and read-back matched e5a00aa9.... Normal BOOT remains original7bb68511.... SYSTEM/DATA/GPT/bootloader/factory untouched. Stock recovery rollback file902b2f06... is staged on tablet and canonical backups retained. Enforcing verified after write. No reboot yet at this checkpoint. SD COLD-WIFI.ENABLE is staged; root archive+calibration copies verified. Next is one independent stock-kernel RAM boot; use USB serial observer, then SSH. Old statements of no internal writes below are historical.

## Current execution checkpoint — supersedes historical preparation below

Read [reports/CHECKPOINT.md](reports/CHECKPOINT.md) for current state. Alpine3.24.4 physically runs in512MiB RAM on stock3.18.35. Passed native Alpine supplicant/DHCP/HTTPS with stockWMT retained, bounded USB-forwarded SSH shell/SQLite/TLS, Xorg/JWM/Goodix bridge and NetSurf live dashboard. Physical taps and permanent service/independent boot remain unqualified. microSD new dated folder has real SQLite persistence and private sidecars; old triggers untouched. No internal partition writes.

Fresh BOOT and RECOVERY hashes BOTH match canonical STOCK backups, superseding the stale diagnostic-recovery claim below. BCB command is empty but recovery still contains `recovery\n--wipe_data`; preserve/reconcile before entering recovery. Android Wi-Fi restoration needs the screen awake because stock PNO fails. Display services, real stock connectivity and Enforcing were verified after trials.

ColdWMT readiness is unresolved: stock Bionic launcher requires randomness/proc, then loops before stpwmt, with Android property_get/set and service.wcn.driver.ready involved. Isolated diagnostic ignored TERM; exact identity checked SIGKILL cleanup succeeded and Enforcing restored. Do not rerun the stock loader on this warm kernel. Offline stock-kernel RAM recovery capsule built, WMT gated off, no deploy. See capsule report. Software snapshot captured over USB SSH and compressed on Mac after tablet gzip hit its bound; archive checks passed, see checkpoint and private/live/sd-rootfs-stage.txt for SD verification. Opus5.5 consultation on exact property-readiness branch is running; completion will resume work. No internal writes or recovery entry.

Original text below describes the initial handoff and is historical where it conflicts with this checkpoint.

## Owner's new objective

Android 17 and Linux 4.9 bring-up are parked. Investigate the newest stable Alpine aarch64 userspace on this tablet's **own working stock 3.18.35 kernel**. Intended uses: touch dashboard, usable browser, SSH and small long-lived services, potentially an API-backed coding-agent client. Heavy builds and indexing belong on the Mac mini. A modern userspace does not make the old kernel secure or guarantee current browser compatibility; demonstrate the actual workload.

This folder is preparation only: no Alpine build, download, installation or tablet operation was performed in this closing task. Do not restart Android 17, upgrade the kernel, or recreate GCP infrastructure by default. Read UPSTREAM.md and PROMPT.md next.

## Device and access

ASUS ZenPad 8.0 Z380M / P00A_2, MediaTek MT8163 ARM64, approximately 2 GiB RAM. Working stock Android 7 / API24, WW 5.3.20, kernel 3.18.35. Android was running at the last physical verification. Device identifiers and prior transport endpoints are in ignored `private/ACCESS.json`; they are historical, not fresh bindings.

USB data is intermittent even when charging works. Wi-Fi ADB was established, but it does not survive every transition. Keep the shared ADB server. Authentication and device identity must be observed again before using any saved target or command. Stock on-demand root worked repeatedly, with SELinux restored Enforcing; the app-context Wi-Fi-root setup failed. No persistent root daemon was installed by this project.

Existing USB root wrapper: `../2026-11-07-asus-usb-retained-log-collector/scripts/root_shell_usb.py`, SHA256 `76b28970223c63b9cdd6774c2190051953beee2d89cde1a22b30d1eebba5c78c`. Inspect before using; it belongs to the old guarded transport, not an Alpine installer.

Normal BOOT/SYSTEM/DATA were **not replaced by Android 17**. Recovery p10 last verified as the retired diagnostic full image `b3ff63a119f791e8d38ab75d2586aba52cf77086026cdfb7ff3fab706d1474c1`. Its artifacts are deliberately retained in `../2026-11-08-asus-global-delay-budget/`. Entering Recovery can stall. Owner has explicitly said to proceed without repeatedly asking whether they are nearby; they will use Power when available if stuck. This does not authorize unrelated destructive operations.

A stale BCB `recovery\n--wipe_data` was observed earlier. Its current reconciliation is not asserted here. Inspect before any stock recovery/TWRP entry; do not factory-reset automatically. Old ASUS17 microSD contents may include installation bundles or triggers. No physical card was cleaned by this task: inspect and neutralize old triggers before reusing it. Do not reuse Android17's proposed DATA layout or partition aliases without checking actual stock GPT/fstab.

## Best existing starting point

The remembered project is **kaantcp/z380m-alpine**, pinned at `7218a276f252a59874ab860683c061fa2b856519`. It uses a stock kernel and reports a lightweight Alpine desktop. Wi-Fi is unresolved upstream. UPSTREAM.md separates claims and published evidence.

Our own stock Wi-Fi and internet were functional, so the radio hardware/vendor stack is a concrete resource rather than a theoretical port. Earlier investigation identifies the CONSYS_8163 WMT/STP BTIF and AHB gen2 WLAN route. Recover actual stock init ordering, firmware, vendor userspace, device nodes, permissions and calibration dependencies before guessing a different chip or writing a driver.

Relevant retained notes:

- `../2026-11-05-asus-root-hardware-validation/README.md`
- `../2026-11-06-asus-android17-radio-kernel-port/README.md`
- `../2026-11-06-asus-hardware-completeness-audit/report/HARDWARE-MATRIX.md`
- Stock GPL: `../2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/`
- Cached donor docs/code: `../2026-11-05-asus-boot-access-audit/sources/z380m-alpine/`
- Donor file provenance: `../2026-11-05-asus-boot-access-audit/evidence/z380m-alpine-source-manifest.json`

Our touchscreen was observed as **Goodix GT6108**, unlike the donor project's ELAN panel. Do not assume donor event numbers, ranges, or bridge configuration. Stock framebuffer evidence suggested 800×1280, 32 bpp, stride3200; verify actual runtime before relying on it. Stock kernel uses legacy android_usb; configfs reporting assumptions failed during the prior investigation. The donor also uses legacy USB and no-devtmpfs handling.

## Rollback and private inputs — keep

Canonical stock backups: `../2026-11-06-asus-local-stock-rollback/artifacts/stock-rollback/`.

| File | Bytes | SHA256 |
|---|---:|---|
| recovery.img | 16740352 | `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20` |
| boot.img | 16740352 | `7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316` |
| system.img | 3753902080 | `4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49` |

All were fully rehashed and matched on Nov8 before cleanup. Receipt: `../2026-11-08-asus-port-investigation-archive/private/local-rollback-verification.json`. These backups were excluded from deletion. Factory/calibration material remains under `../2026-11-06-asus-factory-state-preservation/`, `../2026-11-06-asus-factory-calibration-preservation/` where present, and `../2026-11-05-asus-root-hardware-validation/artifacts/private/`. Existing preservation completeness is not established merely by folder presence. Never publish factory payloads, NVRAM, credentials, ADB keys, or private logs.

Preserve the bootloader and GPT. Donor install instructions replace BOOT and part of SYSTEM, so they are not a harmless live-boot recipe. Prefer a bounded RAM/SD-root demonstration if technically feasible; otherwise prepare a concrete rollback-aware installation plan before writes. Use our exact stock kernel, not a donor kernel or 4.9 diagnostic.

## Prior work: what matters and what to leave parked

4.9 reached real kernel entry and PID1 on this hardware. Reliable completion of the selected normal-priority computation/timer exposure remained unproved. Many absent reports originally came from uncalibrated reporting, so absence is UNKNOWN rather than proof of nonexecution. Final reduced-platform and delay-budget trials did not produce a justified shipping fix. Do not resume that diagnostic ladder in the Alpine thread.

The Android17 build and early-service work produced useful source patches, but did not achieve a physical usable Android17 boot. It is not the base for this stock-kernel project. Lessons: calibrate an observable on the working system first; one question/change/outcome per experiment; cheap focused checks; stop a failed premise instead of adding speculative variants; measure the user's actual workflow early.

Public archive: https://github.com/Kahtaf/research/tree/main/asus-zenpad-android17-investigation

Commit: `122a693d4f9a5fe78b17d2486231225b457245c9`. It contains findings, blocker resolutions, failed experiments, process lessons, patches and 391 experiment references, approximately 43 MB of text. No firmware images or private target logs. Fuller compact local archive: `../2026-11-08-asus-port-investigation-archive/repository/`. The research checkout is nested under that archive's private folder; preserve it.

## Retired infrastructure and cleanup

GCP VM, its single 600 GB disk, and reserved IP were deleted and independently queried absent. No snapshots were created; unrelated resources were untouched. Receipt: `../2026-11-08-asus-port-investigation-archive/evidence/cloud-retirement-verified.json`. Generated Android images on that VM were intentionally discarded. Their paths in old reports are historical, not available downloads.

The old project HTTP setup server was stopped by one identity-checked TERM. Shared ADB and unrelated processes were left running. Native child agents were all completed. Goal was already paused; the UI's `/goal clear` command is queued for handback, with actual clearing not yet observed during this run.

Local cleanup deleted 6,250 retired generated/duplicate files, 18.05 GB logical, increasing free space by 17.78 GB to about 29.0 GB. Stock and factory/calibration backups, fetched source, text reports, nested Git repositories, new handoff and latest installed diagnostic were preserved. Seventeen uncertain images were retained. Details: `evidence/cleanup-summary.json`; exact private per-file hashes/metadata: `private/deleted-files.jsonl`. Some old scripts now intentionally lack generated dependencies: historical PLAN results do not make those installers runnable today. Rebuild only an input actually needed for the new objective.

## Working agreement for the new session

Use this dated folder, with README and supporting outputs inside it. Preserve independent old spikes and nested repositories. Do not touch workspace-root AGENTS.md for project notes. Private/artifacts/downloads are ignored here; verify ignore rules before any Git publication.

Keep experiments tightly scoped and explain the predicted positive/negative result before a trial. Avoid large test suites for low-impact edits. Use gpt-6.1-sol for implementation delegation if needed. If stuck, ask Opus5.5 for evidence-based next steps first, then Large v2 only if Opus refuses; never silently substitute Opus4.8. Do not ask the owner repeatedly whether they are beside the device. Report real blockers plainly and keep focus on a usable OS, especially Wi-Fi, touch, browser and persistent services.
