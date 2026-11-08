# Frozen namespace ownership handoff v1

Status: READY FOR PARENT REVIEW / ORDINARY COMBINED INCREMENTAL BUILD. These bytes are frozen independently of the continuing owned finite runtime fixture. No worker active AOSP source/out edit or global native build occurred.

Defect: graphics-r6 makes the P00A legacy vendor default delegate to BuildSystemDefaultNamespace. Both that default and BuildVendorSection's separate system namespace then advertise all41 actual SYSTEM provider records. The genuine resolver aborts at heapprofd_client_api.so. The library is merely the first duplicate; its payload must remain installed.

Repair: in BuildSystemDefaultNamespace, omit SYSTEM provider advertisements only when DefaultConfig && VendorSection && IsP00aLegacyGraphics. BuildVendorSection always constructs the separate system namespace, which retains all41 records. All requirements, core-first system/system_ext/vendor search paths, isolation, Binder/C++ ABI behavior, resolver guards, and non-P00A/APEX/recovery behavior remain unchanged. No new API, provider-payload deletion or duplicate-guard bypass.

Existing product gate remains exactly the r6 gate: P00A_LEGACY_GRAPHICS build opt-in, parsed first API>0 and<26, and no vendor/product VNDK property. Only the namespace source and one new focused test file are integration deltas. namespace.patch is relative to the system/linkerconfig project.

Exact source preimage: 2f0851395a0bbdf3c54f0f59b7d9e76894274f493e6ae73e40783905b610d34f.
Exact source postimage: e2aa65d9382f2f0e5c7600e5312046e4236ec2b7b1e108fa5cc12bd7d911f3c8.
New focused test preimage: absent; postimage: 00b8df1c513b2819c85a7ab30b4483decbda077d8af6170840ddeee5e007b85e.
Patch SHA256: d7c6088b233ebb0d893e46816768d11798609c499a8b64337ccf98843bb4abcc.

Proof: frozen upstream f6b4bd983b909a907cf7e9fae8a6365d827638b6 plus retained compatibility/graphics-r6 patches reproduces all7 r6 source postimage pins and matches the stable genuine source snapshot. Original19 host tests pass; fixed26 and non-P00A22 tests pass. Added tests cover provider owner, empty/missing provider cases, gate negatives, APEX/recovery/legacy invariance, and genuine duplicate/strict-missing fatal guards.

The selected genuine generator Context/builders/resolver/writer reproduce the exact duplicate SIGABRT before the fix, with both4 actual bootstrap and39 full actual APEX records plus the actual SYSTEM PB. Both profiles generate base and per-APEX configurations exit0 afterward; vendor default advertises0 SYSTEM providers and system advertises41. The driver only supplies frozen actual metadata and writes output; no resolver or readiness semantics are replaced.

Target closure is available: exact android_arm64_armv8-a_apex10000 leaf commands, objects/archives/headers and compiler pins were snapshotted read-only after the parent's completed-image handoff. Its existing stripped ELF SHA f697b2f950e3693449989cfc3e1c94ae9845f48dc9ff1e9af271b01a815bd157 matches actual runtime APEX bin/linkerconfig; actual SYSTEM has no /system/bin/linkerconfig. Fixed target SHA cb03a693acab8781ffa9ee4ccaca3ecd4967bd985ff87db3a23af14e5357c573 is an isolated compiled candidate, not a production signed APEX.

Qualification boundary at freeze: a root-enabled immutable-image fixture has executed the candidate using an explicit directory bind after genuine bootstrap activation; actual linkerconfig generation succeeds. Enforcing1, real manager Binder/HIDL PINGs, software Keymaster4 discovery, Keystore2 registration/earlyBootEnded IPC,39 genuine post-data APEX activations and the original module-hash wait have been observed. Final post-activation namespace continuation is a separate ongoing immutable fixture and is not required to review/integrate this source unit. No full Android/GMS/root-authentication/hardware/CTS/flash GO is claimed.

Parent owns active integration and ordinary native/APEX rebuild with its already accepted device10 metadata changes. Preserve the old failed images/runs. Review pins before applying; no worker integration, regeneration or Ninja action is implied by this handoff.
