# Original STOCK-only RAM rescue build

**Offline implementation, compilation, packaging and reproduction complete. STOCK-ONLY/UNAPPROVED.** This is a new candidate with **two actual original SYSTEM/BOOT manifest records** and the fixed terminal original-p10 restorer. It is not the prior zero-record delivery. It grants no deployment, restore, reboot, reset or physical commissioning approval.

The owned fixture is `/srv/android/2026-11-06-asus-stock-only-ram-rescue-build` on the authorized existing builder. The old fixture was read only. Public host `ARMED=False` and `TIMING_QUALIFIED=False`; the session contract has `execute_approved=false`, `physical_GO=false` and `physical_validation=false`. No live execute profile or approval was generated. The parent owns independent review and commissioning.

## Exact candidate and scope

| Item | SHA256 |
| --- | --- |
| `artifacts/candidate/UNAPPROVED-STOCK-ONLY.img` | `5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f` |
| Full zero-padded `UNAPPROVED-STOCK-ONLY.p10.raw`, VM only | `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a` |
| Exact original two-role manifest | `605cdec038dafe3dddabfe92b8bd6cd189734f740230dfc362d02a43421e4e47` |
| Original p10 payload, VM only in this spike | `902b2f06a01cca574b4aa374e67c4e7f8f0ed53f6e6a55017b6d96351f0f1f20` |
| Static ARM64 helper | `c5df268a9f0bdc31e01140a5378d404f9cb7b091b8ec50e5c2be992434089859` |
| Extended static ARM64 daemon, unchanged | `606b659f213e1acb80de469bc8273203ddc60cc0b2ca76d943cccfe5ebc8ec63` |
| Padded compressed core | `f83a2b221e1e146f66160b4f0f508ad1b62cdbd32f72eadf5e62fc2ce615ea1b` |
| Exact corrected host overlay | `2d6acd11f5b46585bec820188463e4ecb863ec19a6f106a83320f14c24c479d9` |
| Unchanged policy | `16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2` |
| Unchanged compiled contexts | `d82c9ca28d1d9017aea5f58d1cb9b46f6122ef22953ab32b7b4a3a8ccd07186c` |
| Unchanged stock wrapped kernel | `b0e5d48bf2889b418dda0fc867f70e42e27a0aeb0a0a3d37539d9a7435430880` |

The manifest is byte-identical to the one in the prior STOCK commissioning image and the original restorer's `original-stock.manifest`. It contains only original SYSTEM (p25, 3,753,902,080 bytes, 3,580 chunks, SHA `4597a7b5a9f30f9e851f1ae71b54a2db1845465e36a1a55b70ae26e171d5cd49`) and original BOOT (p9, 16,740,352 bytes, 16 chunks, SHA `7bb68511b1ade34d24c3e932da7260e6753fa87270bd8249a7218755a5df3316`). These pins were read from the existing public manifest; no full SYSTEM/data copy or hash was performed.

The only additional writer remains the terminal fixed original p10 operation: `/dev/block/mmcblk0p10`, alias `/dev/block/platform/mtk-msdc.0/11230000.MSDC0/by-name/recovery`, major/minor 179:10, start sector 160184, 32696 sectors, 16,740,352 bytes. No Android17 install, new userdata, five-role profile, arbitrary image/hash/path/offset or p20 writer is bound here. The existing generic manifest parser's ability to parse four/five records is not authorization: the fixed helper's exact two-role/hash gate rejects them and the authenticated core binds this specific pair.

## Construction and preservation

The build copied only whitelisted public recovery inputs from the original fixture. It compiled the extended daemon, regenerated the exact existing policy/contexts, selected `original-stock.manifest` in the immutable core, built the deterministic padded gzip, regenerated `core_binding.h`, compiled the actual static AArch64 helper, assembled its canonical uncompressed newc member, built the Android/MTK image and full-p10 zero padding, then generated external host pins. No self-referential final-image hash was introduced.

A second isolated build reproduced the daemon, core, helper, helper archive, image and full padded p10 byte-for-byte. Generated core binding, external host binding and session contract also matched. The extension-disabled daemon reproduced the legacy pin `30ae9252e575d7c9c837783d60e51016a16bcadb46bd38215d8e49e5bb5d1c53`.

All 18 inherited production source files were compared. Only `host.py`, generated `core_binding.h` and generated `generated_host_binding.py` differ. The daemon/helper C, fixed stock binding, container predicate, restore core, policy builder/auditor and protocol implementation are unchanged. There is no source policy expansion. Host source matches the parent's required overlay exactly, including its qualification gate. Its inherited “unarmed” wording describes the public host flag; it must not be read as saying this new target has zero records.

The compressed core is 2,159,876 bytes; the canonical helper archive is 775,680 bytes. Combined ramdisk is 2,935,556 bytes, leaving 1,258,748 bytes below the existing 4 MiB reservation cap. The Android image is 10,412,032 bytes, leaving 6,328,320 bytes in p10. Page size is 2048. Original firmware header addresses are preserved: kernel 1074266112, ramdisk 1140850688, second 1089470464, tags 1308622848. These are layout checks, not hardware memory-placement qualification.

Independent parsers checked actual Android image ID, MTK wrappers, member alignment, padding, normalized immutable component bindings, partition fit, static AArch64 ELF headers, manifest, policy/context/daemon mapping, and exact stock kernel/init/authenticated-adbd equality. The original OEM payload is hash-verified in full; its original tail is not assumed to follow this candidate's canonical zero-padding rule.

The old zero-record image remains `94e6747bc5998d7e5cf58a33280d362bb0dd97c14941c7fae6625117cc53ef91`, and its full p10 remains `e3df64342477816bc9aa2c8bb44cb61adf7a0f910d2d016c339c3250ff8457e3`. All 117 locally pinned original inputs and all 37 remotely pinned public inputs/source files were checked unchanged. The older commissioning image was preserved and its actual manifest re-extracted for equality. Public parent userdata-contract and preservation receipts were adopted unchanged; no private values were reopened.

## Runtime guarantees retained and limits

The fixed original recovery payload is fully loaded into host RAM before protocol activity. Target staging remains bounded anonymous RAM; full hash, read-only `mprotect` seal and rehash precede any writable p10 open. Payload is an external fixed public host/fixture input, not an added file in the candidate ramdisk. This task did not preload anything on the tablet.

Both full original SYSTEM/BOOT proofs remain: before exec and in the helper. Root, UID2000/shell peer, exact domain, Enforcing, inherited writer lock, CID/GPT, no swap, mount/holder/alias/geometry and held-descriptor checks remain. The helper still requires full current p10 admission, repeat preimage checks, `O_RDWR|O_EXCL|O_DIRECT|O_NOFOLLOW`, all per-chunk prefix/suffix full scans, and final fsync/close/reopen/full readback. No timeout retry, automatic connection/reconnection, reboot, write fallback or terminal-state reset exists.

External full-image/helper authentication by the parent remains indispensable. The target checks an immutable core and a canonical helper capsule against trusted RAM helper bytes; this is not self-authentication against hostile privileged RAM/kernel. The generated host independently binds the final full-p10 digest. The 37 adversarial cases retain the explicit simultaneous RAM-helper/capsule replacement boundary demonstration and refusal of disk-only replacement.

## Host completion and timing contract

Schema-2 `attempt.json` stays durably UNKNOWN. On-disk `receipt.json` always has `outcome=UNKNOWN` and `publication_accepted=false`; `device_outcome` may report observed DONE/SKIPPED. Only a successful live return after publication admits DONE/SKIPPED with `publication_accepted=true`. A visible renamed file, target DONE, later stock readback or replay cannot recreate lost acceptance. Publication failure, crash/lost return, protocol failure and deadline expiry remain UNKNOWN, with no retry/reboot/reset inference.

Provisional whole-phase ceilings are handoff 180 seconds, staging 15 seconds per chunk, prepare 60 seconds and restore 120 seconds under a hard 600-second deadline. They are **not measured or claimed sufficient**. `TIMING_QUALIFIED=False` blocks the public entry even under a modeled future ARMED binding; today's binding is also `ARMED=False`. Neither original-pair proofs nor p10 scans were removed or cached away to satisfy timing.

## Fresh verification evidence

| Evidence | Passing count / result |
| --- | --- |
| `evidence/core-tests.json` | 24 production-core memory cases against the new full-p10 container/helper |
| `evidence/adversarial-core.json` | 37 cases: 16 partial-write positions, 17 fsync positions, post-open mutation, post-seal rehash, external trust boundary |
| `evidence/host-tests.json` | 16 actual C session / exact corrected host cases, including terminal UNKNOWN and no second attempt |
| `evidence/host-durability.json` | 5 receipt/source cases |
| `evidence/build-log.json`, `tests/contract_tests.py` run | 7 regression methods, including post-rename fsync/storage-loss, live-return-only acceptance, delayed valid reply, all four phase overruns, fragmented phase deadline and unqualified public refusal |
| `evidence/build-log.json`, legacy adapter run | 24 legacy RSC behavior cases |
| `evidence/handoff-review.json` | 11 small-file daemon handoff/transaction/descriptor cases |
| `evidence/manifest-admission.json` | 12 native production-parser/helper-entry cases using the actual new core manifest and full geometry |
| `evidence/policy-checks.json` | 72 binary policy/context checks, including 29 compiled lookups and 907 context rows |
| `evidence/policy-structure.json` | Original rules/constraints/permissive map unchanged; one helper block writer; BLKGETSIZE64-only block ioctl; no broad inherited attributes |
| `evidence/concat-guest.json` | Fresh ARM64 guest extracted the actual two members and executed the actual helper's non-operative argument refusal |
| `evidence/reproduction.json` | Fresh complete byte-identical reproduction |
| `evidence/independent-container.json`, `bindings-and-geometry.json` | Actual image/layout/stock equality and external binding checks |
| `evidence/compact-delivery-verification.json` | Local delivery/source pins, original inputs unchanged, original manifest and stock equality, full-p10 pin reconstructed only in RAM, public host refusal |

There are **129 passing behavior cases plus seven host regression methods**. Counts exclude policy checks, artifact assertions and the guest probe; no physical test is included.

The new manifest harness compiles the unchanged production `p10_restore.c`, including `load_manifest` and `main_restore`, without `RESCUE_TEST`. Linker wrappers model root/peer/lock and redirect only public fixture reads. It stops at `load_self` before any partition read. Exact shipped two-role manifest reaches that boundary (intentional return85). Valid zero/four/five manifests, changed original SYSTEM/BOOT or chunk/CID bindings, changed role/partition/size and appended arbitrary path refuse (return84). These are admission checks, not successful live helper execution or physical identity qualification. The 11 inherited handoff cases separately use small regular-file geometry and intercepted exec; the 16 C socket cases exercise the production session/core with the actual new container/helper bytes.

Native storage adapters model memory or small regular files, not real eMMC/O_EXCL hardware. The QEMU run used an existing compatible fixture kernel, one vCPU, 384 MiB RAM and 16 MiB JIT cache, with no block devices, USB or network. A test-only third archive holds its observer. It returned zero with the pass marker; it did not boot the delivered stock kernel or prove a real SELinux domain transition. Every compiler/test child was bounded to one allowed CPU and 1 GiB address space; compilation was sequential. No product Ninja/full kernel build ran.

## Delivery and remaining gates

`ARTIFACTS.json` inventories VM artifacts, including the full padded p10 and original payload. `SOURCE_PINS.json` pins delivered code/tests/public inputs; `BUILD_SOURCE_PINS.json` preserves the source inventory at completed build audit. `evidence/toolchain.json` pins compilers, linker, compiler internals/static libraries, policy library/headers/tools, Python/QEMU and the existing guest kernel. The compact Mac delivery contains the approximately 10 MB recovery image and compact verification inputs. Full padded p10, original payload copy and fixture initramfs stay on the VM. No full SYSTEM/data artifact was transferred, copied or hashed.

No offline implementation blocker remains. Remaining parent-owned gates are independent review of these exact bytes; separately authorized read-only physical rescue and timing commissioning; justified proof/write phase budgets tied to evidence in a later reviewed revision; real authenticated proxy/UID/domain/labels/CID/GPT/geometry/swap/mount/holder/exclusive-descriptor and exact current p10 checks; independent fallback/direct original recovery entry; and separately authorized whole fixed-p10 durability qualification. The first physical write is not already proven by these fixtures.

Only the parent may later decide direct original recovery entry after accepted original SYSTEM/BOOT inverse and exact p10 completion, OEM reset, crypto/data startup, persistence and factory-state acceptance. The adopted OEM-reset contract retains its own legitimate p20/p26/cache/para effects; this build does not perform it. Full OS flashing, five-role profiles and first Linux 4.9 probe remain unqualified. Device availability is an external parent concern, untouched here.

No tablet contact, ADB, USB, fastboot, root/device IPC, reboot/flashing, arming, private calibration/key-content access, cloud lifecycle/new resources, active AOSP/out mutation or other agent inspection occurred. Only the authorized builder SSH transport and offline fixture processes/sockets were used. Retained setup/audit harness failures and their narrow corrections are documented in `evidence/DEVELOPMENT.md`; no completed candidate was rebuilt or replaced to hide them.
