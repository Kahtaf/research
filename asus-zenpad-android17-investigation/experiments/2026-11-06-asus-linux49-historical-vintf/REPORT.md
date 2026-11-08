# Validated experimental P00A P/4.9 retrofit candidate

The staged device-only integration patch passes the actual SDK37 `checkvintf` with the exact physical kernel's complete embedded configuration. No kernel flags or version strings were changed. The actual SDK37 assembler accepts the source manifest and constructs the historical kernel/framework matrices. This resolves the unsupported-catalog failure for the tested experimental profile; it does not establish hardware first boot, functional HAL completeness, or official Android 17/CTS admission.

- Integration patch: [candidate/integration.patch](candidate/integration.patch).
- Actual result: [VM P check command](evidence/vm/05-p-checkvintf.json), [raw COMPATIBLE log](evidence/vm/05-p-checkvintf.log).
- Exact config comparison: [config-comparison.json](evidence/config-comparison.json).
- Constraint preservation: [constraint-audit.json](evidence/constraint-audit.json).
- Preserved negative control: [Q command](evidence/vm/10-q-checkvintf.json), [raw incompatibility log](evidence/vm/10-q-checkvintf.log).

## Source provenance and selected predicates

All network fetches are from official `android.googlesource.com`. Raw Gitiles JSON/base64 responses and decoded file bytes are under `upstream/`; URLs, commit/tree/blob IDs and SHA256s are in [upstream-provenance.json](evidence/upstream-provenance.json). No repository clone or history expansion occurred.

The original Pie branch resolves to kernel/configs commit `506b245cbbb1d06dd5b1a9ee2898988716a1f7d7`. Its `p/android-4.9` tree is the requested `6c4e69e56a41b45ed5510fb5c071be20b7f524a3`. Four original `.cfg` files were preserved. [Original pinned tree](https://android.googlesource.com/kernel/configs/+/506b245cbbb1d06dd5b1a9ee2898988716a1f7d7/p/android-4.9/).

The selected, later-retained P requirements are copied byte-for-byte from kernel/configs commit `e92f32aef4ca28afbd3cd259e179313719940f6c`: `p/android-4.9/android-base.config`, both architecture fragments, and `android-base-conditional.xml`. The corresponding `Android.bp`, build rule and fixup script are also preserved. Minimum LTS is **4.9.84**. The Q profile at the same commit has minimum LTS **4.9.165**. [Pinned P files](https://android.googlesource.com/kernel/configs/+/e92f32aef4ca28afbd3cd259e179313719940f6c/p/android-4.9/), [pinned Q files](https://android.googlesource.com/kernel/configs/+/e92f32aef4ca28afbd3cd259e179313719940f6c/q/android-4.9/).

The official hardware/interfaces commit is fully resolved to `f16c6d3a5741768356159f099d04bfe2219c81fe`. Its `compatibility_matrices/Android.bp` maps FCM 3 to `kernel_config_p_4.9` and FCM 4 to `kernel_config_q_4.9`. Both complete HAL matrix source files and the corresponding build rule are retained. The candidate copies all **57 P HAL catalog entries**, including the original optional/presence annotations, without editing them. [Pinned mapping](https://android.googlesource.com/platform/hardware/interfaces/+/f16c6d3a5741768356159f099d04bfe2219c81fe/compatibility_matrices/Android.bp), [complete P HAL matrix](https://android.googlesource.com/platform/hardware/interfaces/+/f16c6d3a5741768356159f099d04bfe2219c81fe/compatibility_matrices/compatibility_matrix.3.xml).

The retained P profile is not identical to the earliest Pie text. The exact comparison is in [pie-to-retained-p.json](evidence/pie-to-retained-p.json): binder-device text is quoted for typed parsing; the original unconditional QTAGUID requirement becomes the official conditional QTAGUID-or-OWNER/BPF alternative; RT_GROUP_SCHED is no longer a required predicate. This is upstream historical maintenance, not a waiver introduced by this candidate. The actual kernel has `CONFIG_RT_GROUP_SCHED=y`, `CONFIG_NETFILTER_XT_MATCH_OWNER=y`, and `CONFIG_NET_CLS_BPF=y`. QTAGUID is absent, so the genuine OWNER/BPF branch applies. Both official conditionals are retained in the generated matrix. Architecture fragments become CONFIG_ARM/CONFIG_ARM64 conditional groups through the actual assembler's filename rules.

## Exact kernel comparison

Kernel artifact SHA256 remains `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`. The predecessor's direct extraction proved its embedded IKCONFIG equals resolved.config, SHA256 `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`. This task reuses the frozen exact config and release:

`4.9.337-asus-p00a-experimental-g717bb3c9e13c-dirty`

The actual 4.9.337 satisfies both historical LTS minima. P has **191 active predicates and zero mismatches**: 185 common, four ARM64 predicates, and two applicable OWNER/BPF predicates. ARM-only and the alternative inactive network group remain in the generated matrix; they are not deleted. No empty kernel block substitutes for the populated requirement block.

Q has **231 active predicates and ten mismatches**:

| Config | Actual | Q requires |
| --- | --- | --- |
| CONFIG_PM_AUTOSLEEP | y | n |
| CONFIG_DEBUG_SET_MODULE_RONX | n | y |
| CONFIG_L2TP | n | y |
| CONFIG_NET_IPGRE_DEMUX | n | y |
| CONFIG_PPPOL2TP | n | y |
| CONFIG_PPTP | n | y |
| CONFIG_SCHED_DEBUG | n | y |
| CONFIG_XFRM_INTERFACE | n | y |
| CONFIG_XFRM_STATISTICS | n | y |
| CONFIG_ARM64_SW_TTBR0_PAN | n | y |

The actual Q `checkvintf` run exits 65 and reports the first nine base-predicate failures together. The ARM64 PAN gap is additionally established by the active conditional source comparison; the tool stops after the failed base block before evaluating that conditional. No modified test config was used to bypass the earlier failures.

Therefore the smallest **tested** kernel work for this experimental P profile is **none**. These Q predicates are real gaps if adopting Q; they are not prerequisites that this task silently removed from P. The config/profile match is not a complete SDK37 syscall/ioctl/BPF or vendor-binary ABI audit. Existing runtime and feature validation remain necessary. In particular, the P requirements do not demand MEMCG, so the existing disabled MEMCG is not a config failure under this genuine profile.

## Concrete integration change and semantics

The patch changes only `device/asus/p00a`:

1. `manifest.xml`: declare `target-level="3"` and `<kernel target-level="3"/>`.
2. `device.mk`: install the additional `p00a_experimental_legacy_fcm3.xml` module.
3. Add `vintf-legacy/Android.bp`, the unmodified complete P HAL catalog, the four unmodified P kernel files, and exact provenance.

The new module uses the existing SDK37 `kernel_config` and `vintf_compatibility_matrix` producers. It installs `system/etc/vintf/compatibility_matrix.p00a-legacy.xml`; no global framework build rule is edited. No kernel-source, prebuilt-kernel, property, build-authentication, sepolicy, or AVB setting changes. `PRODUCT_SHIPPING_API_LEVEL := 23` stays unchanged.

FCM 3 here is an **explicit experimental retrofit contract**, not a statement that this ASUS originally launched with Android P/Treble, FCM 7, or Android 17. `Level.h` describes the manifest level as the FCM it implements. Source mapping substantiates the P/4.9 combination; all active predicates are actually met. The manifest's kernel FCM pins that implemented P requirement set rather than relying on unspecified-kernel heuristics.

The retained SDK37 source behavior was already copied in the predecessor spike: `VintfObject.cpp` otherwise substitutes the oldest available numbered matrix (7) when manifest level is absent, while `checkDeprecation` independently rejects the missing Shipping FCM Version. First API 23 does not automatically generate a missing historical matrix or assign this FCM. `HalManifest::inferredKernelLevel`, `KernelInfo::getMatchedKernelRequirements`, and `AssembleVintf::checkDeviceManifestNoKernelLevel` permit the explicit P target/kernel combination; an explicit old kernel FCM combined with target T/7 would violate the current assembler's guard. The candidate's source manifest was itself assembled successfully with SDK37 using the unchanged installed sepolicy version 202704.

## Every compatibility change and retained check

The audit compares actual SDK37-assembled combined framework matrices, not just source filenames:

- All **509 effective SDK37 HAL version/interface/instance contracts remain**; the P catalog adds **58** contracts. Zero existing contracts are removed. Every added tuple is enumerated in `constraint-audit.json`.
- All **101 modern kernel requirement blocks remain**. Five genuine P 4.9 blocks are added: populated base, two networking conditions, ARM, and ARM64. No existing kernel condition or config is edited.
- Combined sepolicy and AVB elements are identical. Actual framework-manifest min/max-level filtering has **zero changes** for the frozen installed manifests.
- All 27 existing metadata files other than the vendor main manifest are byte-identical. The main manifest preserves every HAL declaration and sepolicy entry; only target/kernel level declarations are added by the assembler. One framework matrix file is added.
- All 57 historical P HAL entries and their source annotations are retained. No historical kernel condition or HAL catalog row was dropped to obtain the pass.
- The actual checker runs its normal compatibility, deprecation, and applicable unused-HAL logic with `--kernel` and the original first-API/SKU inputs. No disabling or ignore flag is supplied. Exit 0 includes the normal deprecation result; the earlier missing-target and missing-kernel-catalog failures remain preserved in the predecessor spike.

SDK37's native behavior must not be confused with historical mandatory-presence enforcement: its parser/serializer no longer carries the old `optional` distinction, and `HalManifest::checkCompatibility` does not generically test that every historical `optional=false` HAL exists. The assembler drops those attributes as part of unchanged SDK37 behavior. This task preserves their original source, explicitly inventories their unmet contracts below, and does not claim that checker success proves them functional. Current feature checks are not edited or disabled. Historical CTS admission is not made into a new first-boot prerequisite.

## Real HAL and feature work still visible

The full historical mandatory-presence inventory is in `historical-hal-contracts.json` and the declaration observations in `constraint-audit.json`. The three required legacy graphics declarations are present: allocator 2.0, composer 2.1 within 2.1–2.2, mapper 2.0 within 2.0–2.1. Their runtime operation remains untested.

The frozen manifests lack these exact historical interface declarations:

- `android.hardware.audio@4.0::IDevicesFactory/default`.
- `android.hardware.audio.effect@4.0::IEffectsFactory/default`.
- `android.hardware.drm@1.1::ICryptoFactory/*` and `IDrmFactory/*`.
- `android.hardware.gatekeeper@1.0::IGatekeeper/default`.
- `android.hardware.media.omx@1.0::IOmx/default` and `IOmxStore/default`.

There is also no old HIDL health 2.0 declaration, but the current vendor manifest declares **AIDL health V5 IHealth/default**, preserved by this profile. Do not install an obsolete HIDL health HAL merely to reproduce the historical catalog. The framework declares software Codec2 HIDL 1.2 and AIDL V2 stores, also unchanged; those are modern media paths, not proof of the old OMX interface or complete media behavior. Whether these modern paths supply the intended features is a runtime question. Missing audio/DRM/gatekeeper and legacy OMX declarations are concrete feature gaps to review, not failures disguised by deleting their matrix entries, and not newly invented prerequisites for the parent's bounded first-boot objective.

The modern sensor, Bluetooth, keymaster, health, lights, CAS, and supplicant declarations remain exactly as frozen. No service implementation, feature XML, vendor library, or functional validation was altered. Real service registration, behavior, binder/vendor ABI compatibility, filesystem/memory/BPF startup, and the parent's other acceptance gates remain outside the claimed metadata pass. Runtime kernel policy capability also remains unproved: the host tool's static RuntimeInfo sets policy support to SIZE_MAX; the real on-device path queries the kernel. Default host AVB-version checking remains the tool's existing default, not a new bypass.

## Actual execution and preservation

The new VM sibling is `/srv/android/asus-linux49-historical-vintf-20261106`. It copies only the predecessor's frozen VINTF/APEX metadata, full config and release. It never reads current installed/out metadata. The earlier permission to read common-matrix tools in place was used once to copy the actual SDK37 host executables and required shared libraries, checking source hashes before/after copy. All subsequent tool execution and dependency resolution use the owned copies; `final-audit.json` shows no out dependency in the copied assembler's ldd output. Checkvintf SHA256 is the original `f67a37ca56cc1fbb8cf5c919a69990e8493ab0a17248a9cd053ff97d7d1ba4c0`; assemble_vintf is `ddf6512ab57b3ce726cf3e257435f1c88fb9fc9088b3412b43d5c648437604d6`.

Actual P fixup, kernel assembly, final matrix assembly, copied-vendor manifest assembly and `checkvintf` all exit 0. The candidate source manifest also assembles with exit 0. Actual Q assembly succeeds, then `checkvintf` fails at the real configs with exit 65. Both candidates use the identical exact config/release. Source and generated matrices pass the actual copied SDK37 compatibility-matrix XSD under xmllint. The integration patch dry-run against captured device source preimages succeeds. No Ninja/Soong or kernel compile was run, so future parent integration still needs its normal native build checks.

Commands inherit single-CPU affinity, a 1 GiB address-space limit, a finite 90-second worker alarm and 30-second individual tool timeouts. The final VM audit observed approximately **18.6 MB allocated**, below 256 MiB, with frozen inputs and copied tools unchanged. Three device-source preimages were also unchanged on final read; the concurrent root-property source file was excluded. No process inspection, build polling/signaling, lock operation, active source/out/image write, prior-fixture rewrite, device/ADB/USB action, credential read, cloud lifecycle action or child agent was used.

Retained preparatory failures are explicit: one initial official Go-file URL returned 404 before the pinned directory revealed the correct filename; the first snapshot export stopped on a nonexistent device-root Android.bp after copying metadata; a bounded search for retained tool bundles timed out. These are preserved and are not compatibility-test failures or reasons for weakening the profile.

## Parent continuation

Review `candidate/integration.patch` and its provenance. Integrate only after the current image owner's build is complete and under the parent's existing ownership/lock rules. The patch does not include or undo the concurrent one-line root fix. There is **no required kernel config delta for the tested P profile** and no kernel-compile authorization is assumed. Regenerate the real manifests/matrix through the normal native build when the parent authorizes integration; rerun the kernel-enabled checker on the new actual metadata and exact kernel config, retain failures, and keep real feature/runtime gates separate. Parent owns image integration, acceptance, runtime validation and physical GO.
