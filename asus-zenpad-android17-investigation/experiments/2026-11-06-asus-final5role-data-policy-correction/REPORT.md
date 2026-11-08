# Offline future final5role DATA policy correction

Status: **IMPLEMENTED; UNQUALIFIED-future5role-policy; integration held.** This implements P1/P2 from the independent final5role design review in a new isolated spike. It is Android 7 stock-kernel rescue policy, not SDK 37 product policy. Actual install SYSTEM/BOOT admissions remain missing and were not needed for this offline policy delta.

The actual new binary is `artifacts/UNQUALIFIED-future5role-policy`, **390,437 bytes**, SHA256 **`3d982859fdbf06336d6274e7e700ca64a2551effd769a8cb119b4fed97388815`**. It is neither packaged nor deployed. The frozen 390,383-byte `16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2` policy remains an immutable two-role reference and fails the new mandatory-DATA audit.

## Source delta and audit

`patches/three-file-policy-correction.patch` modifies only the copied stock-only `source/policy_build.c`, `source/policy_audit.c`, and `tests/policy_checks.py`. The original files are retained under `baseline/`; exact pre/post source hashes are in `evidence/source-delta.json`. `patches/offline-xperm-test-support.patch` adds one host-only query source, `tests/policy_xperms.c`, needed by the expanded tests. The other scripts and mutation tool are local fixture infrastructure, not target-source changes. Both patches were applied to pristine baseline copies and checked byte-for-byte against the delivered sources (`evidence/patch-application.json`).

The builder adds exactly these two calls after indexing, using its existing functions:

```
allow("os_rescue","rescue_userdata_device","blk_file","open read write getattr ioctl");
ioctl_only("rescue_userdata_device");
```

They emit exactly:

```
allow os_rescue rescue_userdata_device:blk_file { open read write getattr ioctl };
allowxperm os_rescue rescue_userdata_device:blk_file ioctl { 0x1272 };
```

The copied audit keeps the old-edge invariant. Its sole exception requires the exact daemon/userdata/blk_file key, exact `AVTAB_ALLOWED` five-permission mask, and exact `AVTAB_XPERMS_ALLOWED` function bitmap with driver `0x12` and only function `0x72`. Both entries must actually exist exactly once; either missing entry fails. Every other old AV/xperm datum must match in both directions, including additional xperm datums sharing an old key. No substring, rule-count-only, or wholesale old-edge acceptance is used.

The audit also checks old constraints/validatetrans, bounds, type attributes, permissive map and empty conditional behavior. Helper block grants must be precisely the original four targets/masks, with sole writable p10 and four distinct singleton ioctl pairs. Its additional fourth command-line argument supplies the exact pinned frozen helper policy. After validating the two exceptions, the auditor removes only those two entries from its in-memory candidate and serializes it alongside the frozen policy. These serializations must be byte-identical. This checks every other serialized policy field, including helper rules, transition/FD behavior, class/symbol definitions, roles/users, attributes, constraints, bounds and conditional state. It never rewrites an input or candidate file. Assertions must stay enabled when compiling this inherited assert-based auditor.

## Actual binary evidence

`evidence/final-policy-audit.json` passes against the actual generated policy. `evidence/frozen-not-final5role.json` proves the old frozen policy cannot pass as a future DATA-capable policy.

`evidence/effective-policy.json` contains fresh compiled-native libsepol queries for 144 rows each on the frozen and future policies. All frozen rows match the independent review. Exactly one AV row changes: `os_rescue -> rescue_userdata_device:blk_file` changes from empty to precisely `getattr, ioctl, open, read, write`. The other 143 rows remain equal. These are effective TE/MLS/RBAC decisions, not source-string checks.

`evidence/policy-checks.json` reports **218 passing checks**, comprising the original 43 policy queries plus original 29 context lookups (all 72 retained), and **146 additional assertions**. Coverage includes daemon DATA positive access; refusal of additional DATA permissions; retained helper DATA denial and SYSTEM/BOOT write denial; daemon p10/disk/generic/p20-related write exclusions; helper capabilities/mount/setenforce/shell restrictions; shell/adbd block exclusions; existing FD/socket/entrypoint permissions; and a freshly compiled native transition-result query yielding `u:r:p10_restore:s0`. This is an offline policy transition decision, not execution acceptance.

The added native xperm reader loads the actual binary with pinned libsepol, expands source/target attribute membership, combines actual xperm datums and checks effective ioctl AV via libsepol. It refuses conditional policies and bounded endpoints; it is not presented as a general SELinux evaluator. For each of five daemon pairs and four helper pairs, all 65,536 SELinux ioctl driver/function keys are enumerated: exactly `0x1272` is allowed, and the other 65,535 are denied. Helper DATA has zero allowed keys. Sixty command checks include BLKROSET `0x125d`, BLKDISCARD `0x1277`, neighbor `0x1273`, other driver `0x1372`, and `0xffff`. `evidence/effective-xperms.json` summarizes the ten pairs. This restriction is scoped to these daemon/helper pairs; no global stock-actor ioctl claim is made.

The exact unchanged compiled contexts hash is `d82c9ca28d1d9017aea5f58d1cb9b46f6122ef22953ab32b7b4a3a8ccd07186c`. Its 907 parsed rows equal the unchanged text contexts as a multiset. All 29 native libselinux/Android-PCRE lookups pass, including direct and by-name block nodes, non-block modes, alias best-match and helper executable context. Device-like paths are only lookup strings; no device is opened.

## Negative fixtures and reproduction

All **19** binary negative fixtures load successfully and fail the audit (`evidence/negative-fixtures.json`). They cover helper DATA read/write, helper SYSTEM write, daemon p10/disk/generic write, extra DATA permission, changed old AV, either missing required DATA rule, whole-driver DATA ioctl, extra DATA/old/helper ioctl function, attribute/bound/permissive/constraint changes, and an extra helper FD edge. For the six grant fixtures, effective libsepol queries first prove the unwanted permission exists; for the four broad-ioctl fixtures, the binary xperm query first proves `0x1273` becomes allowed. Failures therefore demonstrate rejection of actual bad policies. Rejected binaries and full assertion diagnostics remain in this spike.

The unmodified copied builder reproduces the original frozen policy byte-for-byte from base policy `189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842`. Two new-policy generations match. A separate clean extraction/build of the vendored library and recompilation of the copied builder yields the same new policy (`evidence/reproduction.json`, `evidence/clean-reproduction.json`). Reproduction is on the same native host/toolchain; no cross-platform reproducibility claim is made.

The vendored Android `7.1.2_r39` libsepol archive is SHA256 `c17c444d73f1080a8959cfda2d4bdb529efd88f5af58a9e571917f473f83ff27`. Native context tools were compiled from the pinned Android libselinux and PCRE archives. `evidence/toolchain.json`, `SOURCE_PINS.json`, and `evidence/commands.jsonl` record archives, headers, compiler/linker/ar/make/Python identities, flags, tool binaries and command results. System dynamic-runtime/SDK contents are not comprehensively pinned; their host/SDK versions are recorded.

## Resources, retained attempts and preservation

Compilation uses `make -j1`; native queries are single-threaded and final host commands are serialized with a file lock. Host children have 60-second CPU limits, finite wall limits (120 seconds normally), and a 300-second command-start deadline per script. Policy checks have 10-second CPU/wall bounds per query, a 180-second command-start deadline and a 190-second supervisor bound. No product/kernel build, VM, container, network or target execution was used.

Darwin rejected all three 1 GiB AS/DATA/RSS hard-limit probes; CPU affinity is unavailable through this native interface. Peak observed child RSS was **79,495,168 bytes**, below 1 GiB; the policy suite observed **3,457,024 bytes**. These are observed process high-water bounds, not an aggregate memory quota or hard one-core affinity guarantee. Compiler/linker OS threads are not affinity constrained. Probe failures are retained in `evidence/resource-limit-probes.json` and the command log.

The initial matrix and policy-check processes interleaved after a yielded tool call. That initial QA pass is retained and explicitly does not establish strict sequential scheduling (`evidence/initial-run-scheduling.json`, initial receipts/log). A command lock was added; accepted final QA and clean reproduction ran sequentially. No other failed compilation/test run is omitted; expected negative-query exits and audit assertion failures are recorded.

All **154** original public files pinned before work match after work, including the stock-only delivery and corrected parent/review documents. `evidence/original-files-before.json`, `original-files-after.json`, and `preservation.json` record equality. Frozen compact image `5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f`, logical zero-padded p10 `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`, frozen policy, original sources/flags, contexts, kernel and core remain exact. The padded p10 hash was streamed with a small zero buffer; no padded image was created. Frozen core equality preserves its init/auth-adbd contents. Nested repositories and active trees/out were not modified. No private factory/calibration/key material was opened.

## Parent continuation

Use `INTEGRATION.md` for the patch preimages, new audit CLI and offline QA inputs. The new actual policy identity belongs before future core/helper/container binding derivation. Never substitute frozen `16f6…` for it. Do not package this fixture policy as an admitted final profile.

Parent owns fresh independent review, exact reachable-writer graph review, actual SYSTEM/BOOT source admissions, all later terminal-gate implementation and core/helper/image assembly, fit/binding reproduction, and any physical application. No terminal manifest/header was generated; no terminal gate or phase-proof optimization was implemented. No target daemon/helper/recovery image, deployment or approval flags were changed. This result does not establish final5role helper compatibility, image admission, global source-writer requalification, actual SELinux application, physical transition/locking/I/O, timing/durability, or flash GO.
