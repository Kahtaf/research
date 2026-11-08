# Independent final5role terminal restoration design review

Disposition: **HOLD implementation/integration pending the policy correction and real admissions.** This is a fresh design review, not affirmative approval. The exact frozen policy denies DATA; the proposed shared terminal manifest predicate does not resolve that denial. No target source, frozen artifact, flag or reviewed document was changed. No placeholder header was generated. The separate recovery-phase optimization remains unadopted and final integration remains held.

## P1 — the exact frozen policy cannot provision DATA

`CONTRACT.md:3` says no policy permission is needed. `CONTRACT.md:89` says the daemon already has SYSTEM/BOOT/DATA authority and proposes preserving policy `16f6ce7f25c1b56aba9e4179573c49a6c55f9b9fe3f18336029f6d83b5b4b2c2`. `WORK_AND_ACCEPTANCE.md:17` repeats that no initial policy change is needed. These are false for the exact delivered binary policy. This is a design bug, independent of the missing install-image admissions.

Fresh read-only native libsepol queries loaded `2026-11-06-asus-stock-only-ram-rescue-build/artifacts/restore-sepolicy` directly. Its 390,383 bytes and SHA256 match the phase-proof copy. All **144** effective permission rows match the saved phase-proof result, including the userdata rows. The previous matrix did include userdata. It was not merely a 144-row BOOT/SYSTEM/p10 check.

| Actor | Effective permissions on `rescue_userdata_device:blk_file` |
| --- | --- |
| init | getattr, setattr, relabelto |
| ueventd | create, unlink, getattr, setattr |
| adbd | none |
| shell | none |
| os_rescue | **none** |
| p10_restore | **none** |

The denied set includes open, read, write, getattr and ioctl. Thus role-4 reconciliation cannot open/read DATA, role-4 activation cannot open it writable, and install BOOT's `verify_image(4)` prerequisite cannot prove DATA. A syntactically accepted five-role manifest or the new terminal predicate cannot change those decisions.

The generic target-rescue builder's optional `--userdata` is not evidence of the frozen policy's contents. Provenance is consistent with the binary result: stock commissioning `source/package.py:59` requires the narrow no-userdata base policy `189c477ac73ecb161a6527f7f98a6fec76a913b0d5cf8d11591d440dc79af842`; restorer preparation extracts it as base-policy; stock-only construction inherits that base and adds the helper. The current stock-only base file has that exact hash. The decision above comes from the final policy, not from this provenance or a builder default.

**Smallest future source correction:** in a new parent-owned final5role fork of the pinned stock-only `source/policy_build.c`, add exactly these grants to the existing, already labeled userdata type:

```text
allow os_rescue rescue_userdata_device:blk_file { open read write getattr ioctl };
allowxperm os_rescue rescue_userdata_device:blk_file ioctl { 0x1272 };
```

The existing `allow(...)` and `ioctl_only(...)` functions can emit these two rules after indexing. Do not regenerate a generic policy with guessed flags or broaden a domain/device attribute. `0x1272` is the SELinux ioctl driver/function key for BLKGETSIZE64; this does not grant BLKDISCARD, BLKROSET or arbitrary commands. No helper DATA grant, helper SYSTEM/BOOT write, daemon p10 write, p20 permission, capability, permissive bit, transition, FD or context expansion is needed. Existing DATA node/alias labels can remain exact.

This future policy necessarily has a **new, presently unknown digest**. Do not invent it or reuse `16f6ce…` as the final5role policy pin. Regenerate the compressed core, core binding, helper, canonical capsule, final image/padded-p10 and host pins from actual new bytes in the documented acyclic order. Even if the source delta is only two rules, binary lookup evidence and physical application/transition acceptance must be re-established for the changed final container. The frozen two-role policy/image/flags stay exact.

## P2 — policy QA and preservation instructions would reject or mis-scope the necessary correction

This is a concrete consequence of P1 that must be fixed before implementation, rather than treating the new policy as byte-identical carry-forward evidence. `WORK_AND_ACCEPTANCE.md:34` requires exact policy preservation, and its changed-container section allows unchanged-policy lookup reuse. For a usable final5role provisioning profile, the policy cannot be unchanged.

The pinned `source/policy_audit.c` currently forbids every new edge between old types. Both `os_rescue` and `rescue_userdata_device` are old types, so adding the required rules makes this audit fail. Removing that invariant wholesale would weaken the boundary. Existing `tests/policy_checks.py` checks helper DATA denial but does not assert daemon DATA access.

Smallest corrections to the parent plan and future QA source:

1. Replace CONTRACT's no-policy-expansion claim and WORK's no-policy-change/policy-preservation clauses with the exact two-rule exception above. Require a new `policy_sha256` in final receipts; retain exact contexts/init/auth-adbd/kernel preservation unless independently changed. Keep the helper policy unchanged.
2. In the future fork's policy audit, permit only the exact new daemon→userdata `AVTAB_ALLOWED` mask and `AVTAB_XPERMS_ALLOWED` singleton, with all other old rules, constraints, bounds, permissive map and attribute memberships unchanged. Continue checking the helper's sole writable block type and four restricted ioctl pairs. Do not replace old-edge checks with count-only or broad-attribute acceptance.
3. Extend policy tests to require daemon DATA open/read/write/getattr/ioctl, exactly BLKGETSIZE64, and refusal of other ioctls; retain helper DATA denial, helper SYSTEM/BOOT write denial, daemon p10/disk/generic writes denied, and shell/adbd denial. Recheck direct/alias compiled contexts and the sole helper entry transition. Preserve the existing 72-check/29-lookup regression **scope**; additional assertions will have new counts/results.
4. Re-establish reachable-writer exclusion and actual final policy/core/helper identities. No optimization is adopted by doing this, and no offline decision is physical SELinux or timing acceptance.

## What the exact policy inspection establishes

The supplementary read-only binary inspector decodes the exact version-30 policy's symbol tables and 17,901 unconditional AV entries, verifies an empty conditional-rule list, and uniquely decodes the trailing 1,573 type-attribute maps. It checks bounds, permissive bits and inherited xperm matches. It is a structural supplement to the native effective AV query, not a replacement general policy evaluator.

| Actor | BOOT / SYSTEM | p10 | whole disk | DATA / generic block |
| --- | --- | --- | --- | --- |
| os_rescue | open/read/write/getattr; ioctl 0x1272 only | open/read/getattr; ioctl 0x1272 only | open/read/getattr; ioctl 0x1272 only | no permissions |
| p10_restore | open/read/getattr; ioctl 0x1272 only | open/read/write/getattr; ioctl 0x1272 only | open/read/getattr; ioctl 0x1272 only | no permissions |

All six inspected reachable actors lack DATA ioctl authority. Init/ueventd have node metadata/creation authority but no DATA content open/read/write. For p10 and whole-disk types they likewise lack content write; shell/adbd have none. Init has inherited read/ioctl access to **generic** block_device, with no xperm whitelist for that pair; it has no generic block write. Therefore “BLKGETSIZE64 only” must be scoped to the daemon/helper pairs, not asserted globally for every stock actor/type. The source graph must still prevent relabeling/manufacturing a writable alternative path.

`os_rescue`, `p10_restore` and the specific rescue block types have only self membership, no type bounds and no permissive bit. The native query confirms os_rescue→helper process transition permission, helper executable entrypoint permission, and the existing FD-use relationships. The older native tool does not implement its source file's later `--transition` CLI extension (probe exit 2); no new transition-result evaluation pass is claimed here. The unchanged transition declaration and prior transition receipt remain public source/evidence, with final execution acceptance pending.

## Other requested design boundaries

These are source/contract observations, not implementation or acceptance passes:

- **Binding graph:** no hash cycle was found. Actual admitted install records plus exact frozen original records define the manifest digest used by both terminal gates. The core contains the daemon/manifest/policy; normalized header/wrapper, kernel and actual core determine core_binding; helper consumes both bindings; capsule compares with the read-only RAM helper; the host externally pins actual full padded p10 and helper. Full-image hashes stay external to the bytes that determine them. New policy identity belongs before core assembly. Actual fit/headroom remains unknown.
- **Exact profile:** the three-file text proposal uses one exact count-5/digest predicate at handoff and helper entry. It preserves both `verify_image(0)`/`verify_image(1)` calls at both boundaries. It does not broaden the frozen source to two-or-five roles. No generated binding header exists. Original record byte preservation and exact parse-to-end generation are necessary because generic rescue.c does not hard-code original SYSTEM independently. Arithmetic checks confirm 576,340 manifest bytes, DATA tail 355,840 bytes and final p10 stage 1,011,712 bytes.
- **Order/inverse:** existing prerequisite code enforces SYSTEM2 before DATA4 and SYSTEM2+DATA4 before install BOOT3, at reconciliation and activation. Original BOOT1 requires original SYSTEM0. Keep explicit original 0 then 1 inverse/commit receipts and actual full proof, with no DATA rollback role. The terminal helper does not verify pristine DATA or install roles: exact original SYSTEM/BOOT can retire p10 when userdata is unbootable. No DATA-only shortcut qualifies installation.
- **Fixed restoration:** the text delta leaves prior_container.h, restore_core.h, direct-node/alias/CID/GPT/geometry guards, authenticated UID/domain peer, Enforcing/no-swap, lock/FD exec handoff and terminal-only service unchanged. Original p10 remains the sole fixed 16,740,352-byte payload/destination. Sealed-payload rehash, actual prior capture, stock SKIP without writable open, full prior-container/capsule checks, UNKNOWN before writable open, every full-prefix/unchanged-suffix p10 scan after write+fsync, close/reopen/full readback and no second attempt remain required. No scan removal is proposed.
- **Sources:** new install SYSTEM/BOOT source profiles remain unbound/refused. Preserve fixed admission/metadata/chunk/full hashes, same held-FD preflight before target work, response index/offset/length and source mutation poisoning, source inventory consistency and independent local original inverse. An admission JSON is not a runtime arbitrary-path/hash override or execution approval.
- **Host:** corrected host.py records durable UNKNOWN before requesting handoff, keeps disk receipts UNKNOWN/unaccepted and accepts only the successful live return after publication and directory fsync. Lost return, later device DONE, disk visibility or replay cannot authorize recovery/reset. Whole-phase deadlines and hard 600 seconds remain provisional; socket inactivity, full original-pair reads and p10 scans remain qualification work. No flags or deadlines were changed or measured.
- **p20/reset:** the design keeps p20 untouched through install, original pair rollback and independent p10 restoration. Only after accepted p10 completion may the parent separately choose qualified direct original recovery entry and OEM reset. Stock normal boot against Android17 p26/stale p20 is not an entry route. Reset changes p20 legitimately; error/log, stock FDE/backing/mount, writable data, two-boot sentinel and parent factory acceptance remain separate gates. Stock baseline reset cannot substitute for genuine post-A17 rollback/reset acceptance.

## Separate phase-proof claims and hold

I independently inspected the supplied init/default.prop/ueventd graph, fixed proxy, daemon handoff, helper terminal loop, proposed guard and patch, effective policy and parent resolution. The configured graph has no ordinary concurrent p10 content writer among the six reachable actors: only the helper can write p10, entered by replacing the daemon, retaining the lifetime lock, with no helper init service or return to ordinary serving. Init/ueventd's real metadata/node authority remains relevant; fixed actions and per-operation path/FD/label/geometry guards cannot be discarded. Stock executable behavior/authentication and source-to-binary provenance remain inherited public evidence, not newly executed or reverse-engineered qualifications.

The parent addendum's qualifications are necessary and consistent with the source. A full hash detects a mutation only if it reads changed bytes. Mutation after the relevant final read, or restored before observation, can escape; commit can succeed outside the no-writer premise. Metadata is not continuous content observation. Stat/path checks cannot prove open-file-description identity or access flags/CLOEXEC, and equivalent same-node descriptor replacement can pass. Production source has no concurrent descriptor-table rebinder; that assumption must hold through receipt. No witness or host fixture was rerun in this design review.

The proposal under review explicitly does **not** adopt this optimization. Preserve the parent addendum, fixed-graph scope and final integration hold. A future DATA policy/core/helper change requires a fresh exact-graph review before any independent optimization adoption; the existing source-only finding cannot certify final5role bytes. No timing, throughput, durability, deployment, Android17 readiness or physical GO follows.

## Missing admissions, evidence and integrity

Actual qualified full SYSTEM/BOOT records, build/kernel/DATA qualification and fixed source admission are genuinely missing inputs, not bugs repaired by policy permission. The final manifest/digest/header, daemon/core/helper/capsule/image/padded-p10 pins, new policy hash, fit, independent parse/reproduction and final adapter contract remain unavailable. Direct-entry/fallback, timing, physical SELinux/lock/I/O/durability, actual A17 operation and post-A17 OEM reset/FDE/two-boot/factory evidence remain parent work. Do not supply fixture pins, guessed hashes, approval flags or placeholder headers to cross these gates.

Integrity evidence:

- All **69/69** pinned public inputs match both SHA256 and length; all **8/8** design-document handoff pins match.
- An additional **23/23** stock-only frozen receipt entries match, including source, flags, helper, policy, core and compact image. Existing compact image hashes to `5a61d3d65a7ba6b29745a965d9911ab4483c951a0327339839a0541bcb9ab30f`. Streaming its documented zero tail into SHA256 gives `3f99c785cca60bf56c2505711e2d26b72623daf28180515d44c5ba2abf03a44a`; no padded image file was created.
- Exact original manifest/table/identity values and patch gate structure were inspected. No reviewed input was edited; all writes are in this dated review spike.
- The existing native query ran serially, single-threaded, with 10-second CPU/wall limits per invocation and a 60-second overall bound. Observed child high-water RSS was **3,440,640 bytes**, below 1 GiB. Darwin rejected attempted DATA/RSS/AS memory setrlimits before the first query; a hard Linux/cgroup/affinity envelope is **not** claimed. The first memory-setup failure and unsupported transition probe are retained in `evidence/inspection-limitations.json`. No compiler, build, VM or target executable ran.

Primary receipts: `evidence/input-verification.json`, `effective-policy.json`, `policy-xperms.json`, `review-verification.json`. Scripts are local read-only queries/hashes. Continue by correcting the parent design/QA plan, obtaining actual admissions, then separately reviewing the exact future fork and artifacts. Integration remains held.
