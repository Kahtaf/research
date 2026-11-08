# Android 17 port: coordinated continuation

Current authoritative summary: [CURRENT_STATUS.md](CURRENT_STATUS.md), with
hashed evidence in [current-gates.json](evidence/current-gates.json).
The older entries below are retained chronological history; their process,
device and readiness statements must not be treated as current observations.

Question: can actual SDK 37 / Android 17 boot usefully on the ASUS Z380M
(P00A_2), with working hardware and a recoverable first test?

Status: active. The user requested Astra implementation subagents, with the
parent retaining orchestration. The stock-kernel diagnostic recovery was flashed, executed and returned automatically; original recovery is now fully verified restored. No Android 17 or new-kernel image has been flashed. Ordinary compiler
failures are work items, not a reason to mark the goal blocked.

## Work ownership

1. Graphics agent: proprietary graphics staging scripts/inputs, current minimal
   device product and memory shim, scoped platform compatibility, and ALL VM
   source mutations/builds. Deliver strict graphics build evidence and exact
   integration changes needed in the separate full candidate. Do not edit
   candidates/full, or deploy a full product.
2. Full-product agent: only candidates/full and its own evidence/report files.
   Complete init, USB/configfs, mount lifecycle and appropriate memory setup.
   Read VM source if needed, but no remote writes/builds or device operations.
3. Diagnostic agent: separate new spike for an isolated recovery diagnostic
   candidate. Read backups/source; no device writes, VM writes/builds, or edits
   to the other agents' owned paths. Deliver concrete offline artifacts/checks
   and a conservative restore procedure.
4. Connectivity agent: separate new spike for Wi-Fi/Bluetooth kernel, firmware
   and Android17 HAL integration. Read-only VM access; staged patches/configs
   only. No edits to full candidate, live platform or live kernel.
5. Battery agent: separate new spike for real main-battery gauge/health integration
   and remaining charger prerequisites. Read-only VM access; staged patches
   only. Preserve diagnostic charging inhibition. No live kernel mutations.
6. Boot-path agent: separate new spike for the locked-LK custom-image acceptance
   question and known Z380M boot/recovery routes. Reuse existing disassembly;
   read-only research and concrete bounded test plan. No device operations,
   bootloader/security writes, or changes to the diagnostic agent's images.
7. Google integration agent: takes ownership of the existing Google integration
   spike to prepare pinned upstream inline source inputs and builder staging.
   No full-candidate edits or VM mutations/builds until parent integration.
8. Recovery transport agent: new separate spike implementing the fixed recovery
   install/restore inverse procedure after boot-path review. Source and offline
   validation only; no device commands. Parent reviews before any execution.
9. Connectivity kernel follow-up: separate source staging spike to implement
   missing MT8163 WMT/STP/gen2 WLAN against4.9 using completed connectivity
   findings. Read-only VM access; parent serializes target builds later.

Parent owns integration, global STATUS/plan, full product deployment/build after
graphics is complete, and the decision about physical testing/flashing. Agents
must not spawn other agents, stop the VM, change goal status, or claim runtime
hardware success from compilation. Keep source modifications outside live
builds. Preserve existing artifacts and nested Git repositories.

Full-product agent completed at 14:05 UTC; parent reviewed source/report and
reran all 21 offline checks successfully. It is ready for integration review,
not a compiled/flash-ready image. The agent's real mkbootimg test exposed the
unused second-address distinction: AOSP writes0 with no second payload, whereas
stock MTK header stores0x40f00000. Parent fixed the full-image validator to
accept the AOSP intermediate and require the stock value for both-wrapped MTK
output. Both cases pass the actual-kernel header test recorded in
evidence/empty-second-address-check.json. Do not fabricate a second payload.

The full report exposes an additional first-boot dependency: init waits for
keystore.module_hash.sent before final APEX setup. Actual inherited
KeyMint/keystore service selection and persistent metadata requirements must be
resolved alongside data preparation. A bounded follow-up agent owns only a
separate first-boot services staging spike, not the completed full candidate.

Boot-path agent completed at 14:09 UTC. Parent read the bounded disassembly
interpretation and reran check_evidence.py successfully: exact LK bytes show the
recovery verification return overwritten by the header-magic success result;
the earlier policy failure stores red state and rejoins loading. Both exact
recovery backups and GPT p10 geometry verify again. This supports CONDITIONAL GO
for the stock-kernel diagnostic control, not runtime acceptance or full-ROM go.
Read ../2026-11-06-asus-custom-boot-path/REPORT.md before any device operation.
Only recovery /dev/block/mmcblk0p10, 16,740,352 bytes, is contemplated; preserve
normal boot/system/data and restore full stock recovery afterwards. Diagnostic
candidate completion and parent's reviewed inverse procedure remain required.

## Verified checkpoints

- Genuine SDK 37 framework/app_process64/SurfaceFlinger/services.jar built.
- Static ARM64 first-stage init, libc/linker, shell, network components,
  ASUS AIDL backlight and memory shim built.
- Actual Android 17 libc/linker/toybox and fork/RNG test passed on generic
  ARM64 Linux 4.9 under QEMU; not a GUI or physical ASUS boot.
- Full source and artifacts: ../2026-11-05-asus-android17-device-product.
- Userspace runtime evidence: ../2026-11-06-asus-android17-userspace-startup.

## Current graphics issue

Build r4 and keep-going collection both ended. No graphics success marker.
Vendor ELF checks reject old private symbols. Actual full core libc exports
the flagged ARM EABI and __pthread_gettid symbols; actual core libsync exports
sw_sync_*; core libbinder exports PermissionCache, but vendor libbinder truly
omits it. Many old libraries import logging/sync without a direct dependency.
Investigate a scoped pre-Treble core ABI profile, rather than large fake shims
or globally disabling ELF checks. This is a hypothesis to verify, not a mandate
to apply an unsafe namespace change. Current generation scripts and r3/r4 logs
are the starting point. Detailed preceding history is in product STATUS.md.

## Builder / boundaries

GCP PROJECT_REDACTED, us-central1-a,
PROJECT_REDACTED, 16 CPUs / 64 GiB / 600 GiB disk / 32 GiB swap.
All resources labeled; no new resources needed. Auto-stop approximately 17 UTC.
SSH host IP_REDACTED, user android; key ~/.ssh/asus_p00a_android17;
HostKeyAlias compute.8549823276971553556; known hosts
~/.ssh/google_compute_known_hosts. Never copy private keys into artifacts.
Use IdentitiesOnly=yes, BatchMode=yes, ConnectTimeout=15,
StrictHostKeyChecking=yes. Source /srv/android/lineage24; working area
/srv/android/asus-device-product. No rg on VM; use Python/grep.

Physical kernel: /srv/android/asus-android17/kernel-bpf-fd at
717bb3c9e13ce573cfdd2dda856debd27a0fa17f. Build output
/srv/android/asus-android17/build-bpf-fd/arch/arm64/boot/Image.gz-dtb,
SHA256 7c7051c147b03ca865b3481d55cd832bc6f2732eef1c0063af9404823b0ceaa4.
Kernel configfs USB enabled, legacy USB_ANDROID absent; PSI and zram enabled,
MEMCG absent. Charging deliberately inhibited. Corrected14:12UTC: UG31xx is the
optional cover; the pad uses MT6323 ADC plus the MediaTek OAM software gauge.
The battery report corrects channel routing, battery NTC versus board NTC,
and profile mismatch assumptions; padSOC/current remain incomplete.

Device serial DEVICE_SERIAL_REDACTED, Android 7 stock, on-demand root. Last probe found
it absent. Continue offline. Bootloader locked, standard temporary boot denied.
Normal Boot via boot menu and holding Power five seconds have restored Android.
Recovery partition is backed up twice, SHA256
902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20,
16,740,352 bytes. BROM/DA write recovery is not demonstrated. Stock userdata FDE;
no automatic data formatting, migration or decryption claims. Google/Play must
remain an end-result requirement. A full ROM is not flash-ready yet.

## Continue

Read each completed agent's report, inspect actual diffs/artifacts and evidence,
then integrate sequentially. Do not poll running delegates: completion wakes the
parent. Keep the goal active while delegates run. The immediate delivery is a
buildable full product and controlled first hardware test, not full modern
kernel feature parity or a security certification exercise.

## Full-image integration runner

Parent-owned scripts/build_full_product.sh and scripts/verify_full_images.py
are ready for the later builder handoff. Upload beside the product scripts only
after graphics finishes and the reviewed full candidate is deployed. Run with
a new revision and capture its log/PID using the established supervisor pattern.
The script deliberately refuses a reused revision or overlapping source build.
It records the real exit status and only creates completion after image checks.
Evidence/full-image-validator-checks.json records the actual local checks.
Image layout success is not flash readiness or proof of Android/hardware boot.

The reviewed full device source is frozen as artifacts/full-product-inputs-r1.tar.gz
(17 files; SHA256 b16f0b47e7c538c30639ed24b5afd949d189271930a96f46d145c17a27c7ce25).
It excludes reports, private keys and generated evidence. It is a baseline;
merge final graphics/firstboot/Google inputs, then freeze a NEW revision before
deployment. Updated prepare_full_product.py requires this source manifest and
verifies every source size/hash before altering the active product. Its kernel
link precondition now runs before copying anything. Upload the updated script,
not the earlier VM copy. The full runner builds host_init_verifier and health
and parses all three new init scripts before building full images.

Runtime preflight at 14:00 UTC: source build processes soong_ui PID797003 and
ckati PID799887 are live, available RAM ~58GiB and disk ~357GiB. No restart or
source change was made. Actual GCP stop timestamp is 2026-11-06T17:04:43.960284Z.
The documented GCP runtime-update procedure requires the VM stopped first:
https://docs.cloud.google.com/compute/docs/instances/limit-vm-runtime
After current build ownership is handed back, arrange a safe stop/update/start
with a 24h maximum run duration BEFORE beginning the long full-image build.
Preserve labels/disk, verify no active source jobs or agent remote writes, and
refresh the ephemeral IP if it changes. Do not stop a live build to edit this
timer. Captured actual resource state: evidence/builder-pre-full-image-window.json.

## Google integration input ready

The parent independently verified the pinned Android17 ARM64 Google package in
../2026-11-06-asus-android17-google-integration. Normal tablet payload is
734,779,374 bytes. Signed Google GMS APEX uses EROFS incompat1, recognized by the
actual4.9 backport; mount/activation remains untested. Include the full normal
upstream Google set via pinned vendor/gapps source after graphics finishes,
then prove total filesystem fit. Do not silently strip Google apps for space.

## Data and physical-test gate

At 13:56 UTC, ADB has no ASUS device (ignore offline emulator-5554). Offline
work continues. Stock identity/fstab establish block FDE with a separate
metadata area. Actual pinned Android17 vold retains cryptfs.cpp for external
volume metadata encryption, but its header/AIDL no longer expose the old
cryptfs_check_passwd/cryptfs_restart/fdeCheckPassword/fdeRestart interfaces.
Do not infer stock FDE unlock support from that filename or from dm-crypt alone.
Exact source/revision evidence: evidence/android17-data-interface.json.

The isolated recovery diagnostic deliberately avoids user-data mounts, so this
does not prevent its controlled test. Before a normal full OS test, resolve a
fresh test-data backing plus full stock restore/data-preservation plan. A
RAM-only or external test data volume may be a temporary bring-up tool; it is
not the final persistent tablet experience. Do not silently format encrypted
userdata. Fixed encryption-area snapshots are not a complete userdata backup.

The local Mac has little free space, but the attached FrigateSSD has ~1 TiB
free. No files were allocated there or moved. Capacity is available for a
future local complete backup when the tablet returns; private user data need
not be uploaded to the cloud builder. Evidence/data-migration-gate.json records
the measured capacity, device absence and unresolved migration state.

## Current orchestrator handoff — 2026-11-06 15:25 UTC

Stock-control v3 physically executed despite Red State warning. Custom ADB
product/model and report-only helper were observed on serial 0123456789ABCDEF,
which differs from stock serial DEVICE_SERIAL_REDACTED. Report read failed errno13.
User confirmed automatic return without touching Power. Captured /proc/last_kmsg
confirms deadline started at uptime2.466 and recovery reached reboot at131.255.
Stock restore tool outcome verified_already_restored: original full p10 hash
902b2f...f1f20, cleanup verified, AndroidSDK24 bootcomplete and Enforcing.
Evidence: evidence/stock-control-runtime-20261106.json; private log referenced there.
No 4.9 test until report permission and new-kernel preparation reviewed.

Builder: r4 full product and exact Google sources staged successfully, public ADB
key only. Full build r1 exited1 during lunch preliminary release-config query: 
TARGET_BUILD_VARIANT is temporarily eng and the product's eng guard rejects it
before lunch applies userdebug. This is a build configuration issue to fix, not
a device or goal blocker. No active build remains. Prior r7 graphics success is
retained. Supervisor, logs and exit markers are /srv/android/asus-device-product.
The build runner installclean preserves intermediates and prevents stale vendor
installed copies; currently invoked only r1, but r1 failed before reaching it,
so next successful revision must run installclean once and record completion.

New ownership supersedes old graphics ownership above: designated full-build
Astra delegate owns live device/platform/kernel source and all main builds.
Radio continuation delegate may write/build ONLY its own isolated Linux fixture
under /srv/android/asus-radio-kernel-port, max-j2; pinned committed kernel inputs,
never active source. Recovery follow-up owns a separate offline spike only.
Parent alone owns all ADB/root/physical operations and cloud lifecycle.
SOC handoff completed in ../2026-11-06-asus-android17-main-battery-soc/REPORT.md;
not applied/compiled yet. Integrate it coherently before physical full-OS boot.

Fresh storage audit15:29UTC: no removable disk/microSD detected by block/sysfs/vold.
Stock/data encrypted ext4 mounted throughdm-0;3,810,960KiB free. System p25
read-onlyext4, start1072424,size7331840sectors,179:25 confirmed fresh withroot.
Unprivilegedreadlink/ls was denied; retained failed preflight separately. Host
free~1.3GiB cannot hold3,753,902,080byte system backup. Parent owns independent
stock-system streaming backup preparation and any execution; no userdata or
calibration cloud upload. Card availability question pending. Evidence:
evidence/data-storage-audit-20261106.json. Backup preparation may write only
/srv/android/asus-stock-system-backup on VM, isolated from all build inputs.

User now prefers INTERNAL STORAGE (no microSD), explicitly confirmed via pending
question reply. Non-secret footer classification from existing private matching
metadata backups: AOSP1.3footer2352,DEFAULTpassword,KDF5SCRYPT_KEYMASTER,
1338bytekeymasterblob,aes-cbc-essiv:sha256. No keyderivation/export or userdata
modification. See evidence/internal-data-encryption-format-20261106.json.
Do not assume defaultpassword alone unlocks or point Android17 at old/data.
Rescue/fullbuild agents received user preference via in-turn steering. Parent
asks whether existing personalfiles/appdata needpreservation; no erase decision.
Stock baseline hardware dump captured privately; public summary in
evidence/stock-hardware-baseline-20261106.json distinguishes reportedstate vs
actualexercise (no newkernelphysicaltest).

15:36UTC user answered: NOTHING on tablet needskeeping. Use cleanINTERNAL/data
migration when OSbackup/rescue/imagegates pass; no microSD or fullpersonalbackup
required. Do not block on legacyhardware-backedFDEdecrypt. Parenthasnotformatted
anything. StockOSrollbackstillrequires verifiedboot/systembackup and tested
stockfactoryreset/cryptofooterreinitialization semantics (metadata separatefrom
p26). Rescueagentstages boundedp26ext4provision/rollbackplan, no blanketmetadata
orcalibrationwrite. Fullbuild/backup/rescue ownersreceivedusersteering. See
evidence/internal-data-migration-decision-20261106.json.

15:38UTC parent completed a recovery-only roundtrip WITHOUT REBOOT to prove
explicitinversewriter, independently of Android autorepair. Installrun
20261106T153714Z-e4827f74 candidatewritten/fullhashverified, thenrestorerun
20261106T153750Z-6848d5f2 actuallywrotestock once andfullhashmatched
902b2f...f1f20. Bothcleanupverified, freshstockhealthyEnforcing. Zero
boot/system/userdatablockwrites. See evidence/explicit-recovery-inverse-runtime-20261106.json.
The stock-root-based explicitinverseisnowruntimeproven; independent recoveryOS
restore and4.9returnremainseparategates. No further recoverychangespending.

Additional independent runtime-validation owner may write/build ONLY a new
/srv/android/asus-android17-runtime-prereqs fixture, max-j2, QEMU<=2vCPU/2GiB,
network/physicalUSB disabled. No liveAOSP or physicalkernel mutations; capture
immutable archivedSDK37 inputs ratherthan reading changinginstallstaging.
Goal: actualEROFSAPEX/loop/O_DIRECT/ext4 and SDK37BinderIPC on equivalent4.9
generic fixture. Existing libc/forkpass and staticAPEXformat checks do notprove
these. Any required kernel patches stagedfor mainbuildowner, notappliedlive.
Parent owns integration, keeping main Android17 imagebuild prioritized.

15:43UTC parent completed separate offline OEM restore-source audit at
../2026-11-06-asus-stock-firmware-restore-source. Pinned ASUSfirmwareZIP hash
verified. OEMbootzero-padded16,740,352byteimage matchesBOTHactualstockboot
backups exactly (SHA7bb685...3316). System transferlistv4 coversall916,480
4KiBphysicalblocks once, canonicalzero-discardimagehashedinboundedmemory
without3.75GBfile. Defined-rangedigest available. Actualsystembackupcomparison
PENDING; canonicaldigestisnotlivebackuphashuntilmatched. OEMupdateralso
writespreloader/LK/TEE: neverrunwholeZIPforthisrestore; selectedpayloadonly.
No device/cloudoperationsduringaudit. Fourbinary/invalidinputtests passed.

15:55UTC stock-system backup parentreviewed; firstpreflightrefusedunprivileged
readlink-f /data/local/tmp (notpermissionsoridentityfailure). Actualstat and
no-symlinkcomponentchecks pass: /data1000:1000:771,/data/local0:0:751,
/data/local/tmp2000:2000:771. Parentfixedpre-rootandbinarychecks toper-component
metadata/no-symlink checks, retainingcanonicalidentitycheckinsideEVERYroot
session.38offline tests nowpass. Originalagentreviewpreserved; newparent
review evidence at stock-system-stream-backup/evidence/parent-review-android7-paths.json.
FreshpreflightPASSED, verifiedGCPRUNNING/maxRunDuration86400from14:52UTC
Nov6 (old17:04stoptimestampinsomeREADMEhistoryissuperseded).
Actualbackup RUNNING under nativeexecsession7118, run20261106T155044Z-37006c5ee075db08.
Parentexclusivelyownsdevice; do notrunanyconcurrentADB/root/flash/reboot until
backupfinishes. Onlyp25reads,temp/data/local/tmpstaging,privateVMsystembackup.
No rawblockwrites. Currentrunreceipt evidence/stock-system-backup-active-run.json.
Toolsourcefrozenwhilelive. CompletionrequiresCOMPLETE+independentremoteverify
andOEMcanonicalcomparison. Do not restart fromobservationtimeout.

SELinuxstaticformatcheck: frozenphysicalkernel717... supportsmaxpolicy30;
frozenAOSPsepolicycommitd61fd808...build/soong/policy.go setsPolicyVers30.
Sourcehashes in evidence/selinux-policy-format-compatibility.json. Noversion
mismatch, butfinalcompiledpolicyload/permissionsremainruntimeunproved.

15:59UTC correction/currentbackup: nativeexec7118 endedSTOP afterfirst32MiB
source/export. USBbrieflydisconnected inunprivilegedprecheck beforesecondroot
read. Stockkerneluptimecontinued, no nativecrashlog; transientcauseundetermined.
Firstfilebytehash153560b7...3dd81 preserved. Nativeexec33669 actual32MiB
`adb shell -T` (advertisedshell_v2) probe matchedbyte-for-byte andimmediate
stockhealthquerypassed. Parentreviewedexactstaleinode472372/32MiB+runmarker
andremovedONLYdevicea.bin/owner/stagedir; failedhostchunk/remotebegin/evidence
retained. No rawwrites. Updatedbackupbinarychannelrequiresadvertisedshell_v2,
no PTY;39offline tests passed. Sourcesfrozenperparent-review-shell-v2.json.
FreshpreflightPASSED. CURRENT ACTUAL backup nativeexecsession34488, run
20261106T155844Z-80cb7ab425df604b. Parent-onlyADB/root; allotherworkersno device
operations. ObserveSAMEhandle/ownjournals, no blindrestart aftertimeout.
Completion/fullverificationpending. PreviousRUNNING7118noteissuperseded.

16:15UTC radiohandoffactualcompiled despitefinalworkspaceack; parentrehashed
41compileroutputs andexit0 forfullkernel/loader/radio. See radio-compiled-handoff.json.
Fullbuildownerreceivedradiosourceinputs andlatercharging0003patch(11files,
SHAaa827a...a187,173sourcechecks), preservinginhibitedDT andsourcefreeze.
TargetcompilecombinedSOC/radio/chargingstillpending.
Runtimeprereqs r5actualAPEXdmverity/directIOmaterialreads68hashes/Binder200reply
20oneway/death/threadtestPASS,58configsmatchedphysicalbaseline; no newphysical
patchneeded. FullSELinux/apexd/keystore/framework/hardwareNOTproved.
Diagnosticrepairreviewedconditionally: newmanifestin evidence/reviewed-stock-control-report-repair.json;
OFFLINEPLANONLY, no concurrentdeviceops whilebackup. LegacyUSBstockkernelonly.

CRITICALbeforep26format: preservefactorycalibrationcurrentlyunderold/data, even
thoughpersonalapps/filesneedn'tbekept. ExactBT_Addr64bytesandWIFI512bytes must
beindependentlyreadtwiceandkeptPRIVATELOCAL, ownership/mode/labelcaptured.
No cloud/productblobupload. See factory-calibration-preservation-gate.json.
ParentwillcollectAFTERbackup; no otherADB/rootowner.

Newtarget-rescueAstra owns separateLinuxfixture /srv/android/asus-target-rescue,
max-j2 andQEMU<=2GiB ifneeded; mainbuildandruntimehandoffsourcepreserved.
FinishrealLinuxFD/socketadapter,UID2000proxy,dedicatedpolicy andbootable
stockkernelrescueimage; existingrescue-UNARMEDexit78isNOTusable. No deviceops.
Parentalonechoosesphysicaltrials. Dedicatedrescuemustnotautotimerreboot during
writes. Currentbackupsession34488/run20261106T155844Z-80cb7ab425df604b continues.

16:24UTC IMPORTANTcurrentstate: USBbackup native34488 STOPPED at77verifiedchunks
(2464MiB), binaryreadshortstatus255midnextchunk. No fullbackup/COMPLETE/READY.
User confirms DEVICE USBPORT FINICKY; shell_v2didnotfixphysicalcontact.
Allfailedlocal/remotestagingpreserved; do notblindlyrerun/resumeoldtool.
CurrentstockAndroidhealthyEnforcinganddidnotreboot. MacADBbackendNATIVE37.0.1.
ParentenabledstockauthenticatedADB service.adb.tcp.port5555(privateLANonly),
connectedIP_REDACTED:5555, verifiedexactH5serial/P00A_2/SDK24/fingerprint/secure1
plusbootcompleteEnforcing overWiFi. No newkey/firewall/publiclistener.
Transitionevidence artifacts/private/wifi-adb-transition-20261106.
SeparateWiFihelper at ../2026-11-06-asus-wifi-device-access/scripts/root_shell_wifi.py
keepsoriginalUSBhelperunchanged, pinsoldbinary and exactprivateendpoint+hardware
properties, validatespathcomponents, carriesTEXTonly, handlesinnernonce/status
andEnforcingrestoration. RuntimeUID0+exit17proof innewspike/evidence.
It addsnoOSblockwriter/permanentrootdaemon. Parent-onlydevicecommands; no live
backup currently. Afteruse stopTCPlistener with adb -sIP_REDACTED:5555 usb.
NewWiFibackupadaptertask ownsownspike/codeonly, parentexecutesafterreview.
NewtargetrescuetaskmusthandlefinickyUSBwithframedboundedwrites and safe explicit
verifiedresume/reconnect; no120secautoreboot or blindretry.

ChargingAstrareport/patchcompleted(173sourcechecks,3sanitizersuites), parent
rehashaa827a...a187; mainownerreceiveditandradiohand-off. KernelchargeDTremains
inhibited. RuntimeAPEX/Binderprerequisitescompleted/parentvalidatePASS(211captured
entries68readhashes,58configs,282sourcefiles). Mainownerreceivednofurtherphysical
patchneed. Currentmainbuildcontinues; parentwillreviewactualkernel/imageoutputs.

16:46UTC current: authenticated WiFi stockbackup started after fullparentreview
of47tests/adapterdiff/pins. Nativeexec handle recordedbyparent tool; run
20261106T163857Z-845d682705925287, source2026-11-06-asus-stock-system-wifi-backup.
Currentreceipt evidence/stock-system-wifi-backup-active-run.json. ParentONLY
ADB/root untilitends; no concurrentdevicecommands. OriginalUSBbackup34488
isTERMINALfailed at77chunks, notrunning. Botholdpartialrunsretained.

Factorycalibration is PRESERVED locally: actual BTcontainer66B, WIFI514B,
not64/512physicalfiles. Two matchingindependentcopies/metadata/labels savedin
../2026-11-06-asus-factory-calibration-preservation/artifacts/private/20261106T163652Z.
Tempdevicecopiesremovedverified, stocksourceunchanged. No payloadcloudcopy.
APIlogicalrecordsare64/512atprefix0; actualMACcorrelationBTat0,WIFIat4
confirmsno2-byteprefix. Trailing2containerbytespreserveduninterpreted.
Initial64/512sizeguardcorrectlyrefusedbeforepayloadreads; parentreviewedactual
metadataandcapturedWHOLE66/514files. See localpreservationreceipt.

CurrentradioBTreader incorrectlyrejectsOEM66Bcontainer. Parentstagedonlyone
read-onlyABIcompatibilitypatch in calibration-preservation/integration, retaining
logicalAPI64/count1/readonlyFD andfull66Bsource. ASan/UBSan actualprivatefile
passes; truncated64/extra67/multicast refused; sourceunchanged. PatchSHA
0bdcc9b6f8beb148314c98ece4866c31dc27c9fe60a6d7321f68a21576093dfe.
Mainbuildowner mustapplyafterradiostaging; donottrimfactoryfiles oruploadthem.

Mainbuild originaldelegate3f5 completed its turn while actualr5 remainsLIVE:
parentverifiedsupervisorPID78673,bashbuild_full_product.sh r5; sisoPID132874
bootimage/systemimage local_jobs8,30861/170205tasks(~18%) at16:32UTC.
No r5exit/finished/complete marker. PreservefrozenactivesourcesandSAMEjob.
SOC-onlykernelactuallycompiled0d530f1f...d0f5acf,7230152B, localbuild-integration
artifact. CompiledHealth/frameworkservices+4initparserchecks passedbeforeimage
phase. Radio/charging onlypreparedfornextserializedrevision, notmergedyet.
A new maincontinuationAstra willown drain/fix/fullimages and isolatedcombined
kernelfixture for parentRAMprobe whileactualr5continues.

16:55UTC update: WiFi backup run20261106T163857Z-845d682705925287 is TERMINAL
exit2,11 fully verified32MiB chunks. Failure is helper PRE-root getenforce exit255,
not a block operation; latest root operation was not dispatched. Native PID15094
absent and wrapper receipt terminal. All staging preserved. Fresh read-only ADB
shows real H5 serial, bootcomplete1,Enforcing,uptime5509.77. Do not call this a
complete backup or restart old run blindly. Need verified prefix continuation.

New parent recovery WiFi adapter spike2026-11-06-asus-recovery-control-wifi:
33 offline tests pass; original USB source unchanged, existing repaired diagnostic
manifest PLAN_ONLY validated. No device operation by adapter. It shares original
USB writer hostlock, fixed TCPendpoint but separately validates realserial and
secureADB, keeps exact stockkernel/p10 bounds/readback/inverse/no-write-retry.
Not a 4.9 kernel writer. Physical trial remains parent-supervised after backup.
Main continuation task9d33c6d2-050c-403a-889d-b90575de4c78 running; target rescue
4ef9811a-27c1-4997-ae4d-fb71ceee8e69 running. No delegate status polls.

17:03UTC USER STEERING: continue offline for now; physicalreporting trial held.
No device writes/reboots performed. Parent reran actualbinarypolicy/image/DAC
checker: PASS repaired7d74df...18ea5, exactstockkernel, padding6c6a3f...2db925.
120secdeadline sourceIDENTICALtoearlierphysicallyprovencontrol. FreshreadonlyUSB
pin was captured beforeusersteering; do nottreatitfreshindefinitely. WiFirecovery
adapter's new conditionalreview+manifestfaae628d...e0bc44 allowsONLYsupervised
p10stockkernelreporting whenusernearby; fullOSbackupremainsfullOSflashgate,
not prerequisiteforRAM-onlystockkernelcontrol. CurrentuserunavailablemeansNO
execution. Defaultplanandobserverplanvalid; nextphysicaltrialnotqueued.
All fourAstra offline tracks continue; goal remainsactive. Deviceoperations
pauseduntil user availability; no fullOSreadiness claim.

User clarified unavailable ~6hours, permits programmatic recovery entry/exit if
possible. Parent will review exact stockinit/MediatekRTC/LK one-shotselection
before anyunattendedstockkerneltest; previoussupervisedflagcannotbefalsely
asserted. First4.9kerneltestheldforphysicalfallback. No devicewritesdispatched.
Newcurrent-source networking review found existinglegacyConnectivitypatches04/05
alreadyapplied, so oldSTATUSunmodified5.10floor alone is stale. ActualrequiredBPF
objects/maps/netd/Java initialization on4.9 remainsruntimeunproved; objectinfo
andotherBPFAPIbackports beyondenumeration/getFD remain potentiallyneeded.
Do notclaimnetworkreadyfromlegacyloadfailuretoleranceorcompiledELFs.

17:20UTC parent accepted full-size internal-data handoff: matching raw11331268096B
SHA1602ea...e0c1 freshremote reread;2Linux4.9boots,136APEXmaterialhashes,
18negativecases;84archiveentriesverified. Noactualinit/policy/apexd/physicalproof.
Passedinputsenttoongoingmain/rescue/firstbootowners. Preservepristine0400file;
primary338*32MiBhashes and10807*1MiBfragment notinterchangeableprotocols.
IndependentOEMcomparisonmetadata generatedstreamingall112chunks, hash853e98...7140.
Historical77USB/11WiFi receipts allmatchOEMcanonical. FreshREMOTEread-only77USB
files2583691264B allmatchtwo-sourcecaptured+OEMcanonical+definedranges hashes:
stock-firmware-restore-source/evidence/remote-prefix-comparison-20261106T171652Z.json.
Earlierread-onlycheckerfailedonfinaldatetimealiasafterreads; receiptretained,
fixedandrerunactualcomparisonPASS. StillNOTfullsystembackup/noREADYforprefix.

17:22UTC actualbackupCONTINUATION LIVE: run20261106T172146Z-89fc7700813aad85,
nativeexec27871,actualPIDsrecordedin evidence/stock-system-continuation-exec-handle.json.
Parentreviewednewhelper/health/coordinator/policy/worker,72testsrepassed,
preparedinputhash78c42f...46251reproduced. Livepreflightexit0; freshbackupstarted.
It rereads/copies77actualoldchunks intoNEWrun anddoublecapturesremaining35.
No oldruncleanup/hardlinks/in-placeappend; schemav2truthfulaggregateprovenance.
ParentexclusivelyownsADB/rootuntilnativejobends. Do notconcurrentlyquerydevice
orchangefrozencode/helper. Separatefinalverify+OEMfullhashcomparisonpending.
Earlycombinedkernel/probe-R2milestonearrived; maincontinuesfullimages. Newkernel
firstphysicaltrialhelduntilusernearby; reviewpackaging/initrd/UDC/policyoffline.
