# Genuine SDK37 service runtime handoff

**Real init, servicemanager and hwservicemanager now execute under enforcing SELinux, and both managers answer functional IPC calls. The chain stops at the mandatory, genuinely missing platform BoringSSL self-test. Keymaster/keystore/APEX/adbd qualification remains blocked.**

All work belongs to `/srv/android/asus-genuine-service-runtime`. No AOSP/Ninja build, full-kernel or product-image build, active-source/output edit, cloud lifecycle operation, physical device/ADB/USB/root operation, user-key access, or previous-fixture mutation occurred. No physical GO or deployment readiness is implied. No subagents were used.

## Frozen inputs and policy

The coherent initial capture finished **22:19:09 UTC**, before the parent’s r6 integration/build. Its 377 selected files total 48,077,822 bytes; every source/copy/before/after hash matched, including the five actual product service ELFs, their available dependency candidates, init/VINTF sources and actual adbd CAPEX. The installed service hashes match the parent’s completion receipt. Missing host-resolved APEX symlinks are recorded as missing, rather than mistaken for completed package contents. Genuine ICU dependencies were separately captured with provenance. No whole SYSTEM or pristine 11.3 GB data image was copied or hashed.

The final fixture uses the initial capture’s **872,703-byte policy**, SHA256 `f2559923357169800212cb33c8a931dabe6ce02b56f372e43627e2e532728033`, policy version30. Its exact genuine `secilc` command was reproduced in owned storage from frozen CILs; output byte-matches the product-compiled policy. Unchanged supporting CILs came from the qualified prior capture. Every service-context output was checked against this policy. The earlier 872,537-byte policy remains preserved in earlier runs. The vendor CIL delta identifies existing backlight/battery labels and light-HAL permissions; no policy relaxation was introduced by this worker.

A late supplemental capture failed equality against that earlier policy. It is quarantined and was never used as a guest input. This is **not** evidence of a new r6 native compilation: the current policy was already present in the 22:19 snapshot. The parent reports r6 exit1 before native compilation; no parent build was polled or restarted.

## Actual runtime result

Final **run-boot-r9**, launcher PID1556965, ran **22:34:54–22:34:59 UTC**. QEMU exited0 without timeout because the guest performed its normal fatal reboot; exit0 is not a boot-success assertion. Eight serial runs and their commands/statuses remain preserved. `evidence/qualification-final.json` verifies **24 expected observations**, including negative controls and the preserved fatal gate.

Observed in the final run:

- Genuine first-stage and second-stage init; enforcement1; actual init, shell, servicemanager and hwservicemanager SIDs.
- Real servicemanager Binder PING reply: flags0, empty success payload.
- Real hwservicemanager HIDL IBase PING reply: flags0, four-byte status0.
- **The real hwservicemanager** sets `hwservicemanager.disabled=false` and `hwservicemanager.ready=true`. Diagnostic init commands only read/print those properties.
- An invalid Binder handle returns BR_FAILED_REPLY. The allowed diagnostic property round-trips through the real property service; the forbidden persistent write is rejected and remains unset.
- Genuine apexd executes, scans `com.android.adbd.capex`, exits bootstrap0, and reports **zero activated packages**. This establishes execution/scanning, not activation or trust qualification.

Two fixture-input failures were corrected without service/policy code changes. Missing service-context files caused genuine servicemanager’s `gSehandle != nullptr` abort. Nine exact selected m4 outputs, validated by genuine checkfc, remove that failure. Missing VINTF metadata prevented HIDL manager registration. Exact selected assemble_vintf rules generate the vendor/software-Keymaster declaration, system_ext manager declaration and required base system manifest. The base manifest must exist before libvintf merges system_ext; adding only the extension was insufficient. Before/after serial negatives and successful IPC are retained.

## Remaining gates and parent action

The unchanged mandatory init action cannot find `/system/bin/boringssl_self_test32`, then requests `reboot,boringssl-self-check-failed`. The platform 32/64-bit link outputs are absent. Completed Conscrypt `*_apex31` variants are different outputs and were not substituted.

The selected signed `com.android.runtime.apex` is also absent. Apexd activates no bootstrap packages, and init cannot execute `/apex/com.android.runtime/bin/linkerconfig`. The standalone genuine linkerconfig was not redirected there. Exact package variant, direct missing dependencies and official property/APEX-key generator edges are in the evidence and [PARENT-REQUEST.md](PARENT-REQUEST.md).

After the parent’s separately owned build, supply the official platform self-tests, selected runtime APEX and genuine generated system/system_ext/product properties and aggregate APEX-key metadata. Do not interrupt or change a parent build for this fixture. Normal official context/VINTF outputs can replace the byte-pinned owned generator results in a new coherent input revision.

Still unproved: Keymaster HAL registration/hardware-info/crypto; keystore database and crypto/module-hash handoff; post-data APEX activation, verity/trust and final namespaces; execution of adbd from an activated package; isolated negative/positive authentication and userdebug root boundaries. No ADB server, transport or fixture keys were created because those prerequisites were not reached. The shell observer reports no value for `keystore.module_hash.sent` or `sys.boot_completed`; protected-property visibility limits mean this read alone does not prove global absence. No readiness setters were introduced, the genuine waits remain intact, and no downstream completion is claimed. No BPF readiness was forged or patch12 ELF used.

## Scope and continuation

Every QEMU run used one CPU, 1 GiB RAM, 64 MiB TCG cache, a 2.5 GiB process address-space bound, no NIC and a 90-second wall limit. Small probe/policy compilations and metadata generators were serial and bounded. Disposable legacy ext4 scratch is 512 MiB per run; post-data mounting/activation was not reached. The vda=data/vdb=system mapping, entropy seed, bootstrap library layout and diagnostic observer are fixture adaptations. Virtual FunctionFS fails as recorded; USB functionality is not qualified, and no host/physical USB was forwarded.

The unchanged qualified virtual kernel is `95a62a8b…`; config `c2ea1277…`. All 290 selected virtual source pins and 134 options were rechecked. The inherited parent receipt relates those selected pins to physical BMC156 image `e9cde06e…`, config `10b212ca…`. This is scoped correspondence, not whole-kernel, hardware-driver or physical execution proof. No virtual configuration was copied onto hardware.

Read HANDOFF and final qualification first. Create a new input/run number after official artifacts arrive; preserve every prior directory. `python3 source/run.py r10 r9` reproduces the current pinned failure into new disposable disks. Do not rerun initial capture/preparation against an existing fixture. Known preparation/probe/parser failures and corrections are explicitly preserved in `evidence/preparation-failures.json`; r4 is excluded from revised-probe claims. Large images/ELFs remain on the VM. The compact export contains raw serial, hashes, source and commands.
