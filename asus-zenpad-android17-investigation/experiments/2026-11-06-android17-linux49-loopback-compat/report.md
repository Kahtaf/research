# SDK37 loopback isolation: bounded compatibility decision

**Status: BLOCKED, baseline failure preserved. No kernel fix or integration patch is staged.** The unchanged SDK37 policy cannot run through the existing Linux 4.9 BPF interfaces. A compatible implementation needs connected changes to the verifier, socket lookup, socket storage, socket lifecycle, BTF and loader selection. This spike supplies pinned source, an executable policy/ABI test unit and an ordered next implementation unit. It does not qualify Android networking or authorize hardware work.

## Evidence and pins

Only selective reads of `/srv/android/asus-network-runtime` were made through the existing SSH wrapper. There were **no remote writes**, guest runs, process polls, device operations, Android builds or kernel builds. The new remote prefix `/srv/android/asus-loopback-compat-20261106` remains unused. The original scripts were read as evidence, never run against their old prefix. Separately owned R9-exec and final3changedBPF mutable directories were not read. No active product, probes, source, out or cache was changed.

The local snapshots are enumerated with SHA256 and byte counts in `evidence/frozen-selection.json` and `evidence/frozen-extra.json`. These are selective source copies, not a source-tree archive. Missing `include/linux/bpf_types.h` and `include/net/ipv6_stubs.h` are recorded, not synthesized. The inherited handoff manifest is copied verbatim under `inputs/frozen/handoff-r1/manifest.json`.

| Identity | Pin |
|---|---|
| Physical source baseline | `717bb3c9e13ce573cfdd2dda856debd27a0fa17f` |
| Virtual source baseline | `fcb1b6c2de6348e2724981dcd520dec631ed5255` |
| Frozen Connectivity HEAD | `7c04d866538e6f689823b769fb5c1e614ca0e295` plus captured local changes; file hashes are authoritative |
| Original SDK37 netd.c | `7dc4fa02952c0268737dc9aad20a0571b55df255f878506a4db91c1d962713b6` |
| Qualified core netd.c | `0ecc7f0895df51ccfa2316115a148fd1fbc6c5a3797607035f51a889911571d1` |
| Original captured SDK37 netd.o | `c5232afa1ae316a42008983b99aec58332a073dd95a57a63a6033fe96763c2bc` |
| run-r18/core netd.o | `25ccea3b8043240238381ee19d950ebc51629f06688b3a1af9d97e8a6e11ad6f` |
| run-r18 kernel Image (inherited result, not rehashed) | `f48955e15b0210d0b14c9d8036b6655e353a02c9e46ae5fc015b252b9bd8eac6` |
| Qualified virtual config | `8323724c579329c40f33aa15531320e2fdefc7e8d190703d56a555eac890ba01` |
| Physical config | `0a79503b82ed5980a3b3e0ffb288cdadc49abb67969221960c1295cd7bae03df` |
| Core handoff manifest | `d6790e2efde8ddb11102f561b5c58129660be09d41f1bbfb66402f3865ef13dd` |
| Upstream reference source | Linux v5.10 tag resolves to `2c85ebc57b3e1817b6ce1a6b703928e113a90442`; tag response retained |

Frozen build provenance records Android `clang-r584948b`, target BPF, `-mcpu=v1 -O2`, exact include paths and successful source/object section comparison. This audit did not read or hash an active compiler binary. Its inherited remote tool identity is therefore a version/path/build-command pin, **not** a newly verified binary digest. New host compiler version, resolved binary digest and commands are in `evidence/tool-pins.json` and `evidence/host-tests.json`.

The run-r18 serial log lines 725–734 record SDK full 3701 / Linux 4.9.337. With checks enabled, UID10001 delivered 19-byte UDP payloads to sockets created by UID110002 for IPv4 and IPv6, where denial was expected. Same-profile UID10002 and checks-disabled cross-profile cases delivered as expected; lack of INTERNET group rejected socket creation. The copied probe verifies the receiver FD's inode UID after SCM_RIGHTS transfer and child exit. `CROSS_PROFILE_RESULT failures=2` is authoritative for this gate. QEMU exit0 / `complete=true` only describe fixture completion. The old run used 1536MiB; it was not rerun under this task's 1GiB ceiling.

Frozen generated-flag evidence records `useLoopbackInterfacePermissionEnabled=true`, and the existing report records default UID-permission migration enabled. Runtime stores may override defaults; this work neither changes nor claims to have booted those stores. The migration excerpt alone is truncated before its default argument; retain the owner's reported qualification boundary rather than inventing further flag provenance.

## Exact policy being preserved

References below are to `inputs/frozen/inputs/Connectivity/bpf/progs/netd.c` and `.h` unless stated otherwise.

* `bpf_traffic_account`, lines 909–914: the loopback check runs on parsed egress packets, after other policy permits, when interface index is **1**, and API level is at least 25Q4. This is the actual source condition; replacing it with a different address/interface definition would change behavior.
* `should_block_loopback_access_cached`, lines 667–709: both switches off returns allow; TCP packets without SYN bypass lookup; UDP reuses a per-sender-socket decision for **less than 10ms**, keyed by destination address and destination port. It uses BOOTTIME. Permission changes can therefore leave an existing UDP result usable until expiry. Preserve this behavior rather than promising stronger immediate revocation.
* `should_block_loopback_access`, lines 605–665: build a 12-byte IPv4 or 36-byte IPv6 tuple in network byte order; call helper84 or85 with `BPF_F_CURRENT_NETNS=-1` and flags0; read `SkStorageValue.uid` through helper107; release through helper86. Missing lookup or missing storage allows the packet. Other IP versions/protocols also allow. Sender equal to receiver bypasses metrics and permission checks.
* `uids_have_loopback_permissions`, lines 496–519: a system appId at either end, or same user/profile, allows. Otherwise either endpoint with **both** FORCE_USE_LOOPBACK_INTERFACE and INTERACT_ACROSS_USERS_FULL allows. For the same appId in different profiles, sender INTERACT_ACROSS_USERS_OR_PROFILES or FULL allows. For different appIds, sender FULL is required. USE_LOOPBACK_INTERFACE alone is not checked in this pinned body: its TODO is not license to implement a stricter or simpler substitute.
* `get_chunk_permissions`, lines 365–376: full UID, seven bits/UID, nine UIDs/u64, 128 u64/chunk, 1152 UIDs/chunk; missing chunk means zero permissions. AppId-only maps cannot replace this map.
* `inet_socket_create`, lines 1176–1208: helper15 captures current UID/GID; helper107 CREATE initializes cookie, creator UID/GID and TCP state. Migration uses full-UID NO_INTERNET policy. Legacy branch uses appId INTERNET plus owner firewall policy. Storage allocation failure is not itself a create denial in the original body; changing this is a separate policy decision, not a compatibility shortcut.
* `.h`: SkStorageValue is128 bytes, uid offset12, loopback_cache offset96. LoopbackCache is32 bytes; result offset26. Allocation, FD transfer, owner mutation and close must not substitute a different identity for the stored creator UID.

The preserved core handoff's additional 4.9 ingress/egress wrappers call `bpf_traffic_account(..., KVER_4_9, API(25Q2))`, even on SDK3701. That removes the 25Q4 loopback path at compile time. The real checks-enabled map cannot restore code absent from the selected program. Merely changing this API argument exposes missing kernel facilities; it is not a fix.

## Dependency graph and Linux 4.9 gaps

`evidence/original-elf-calls.json` scans the actual original ELF, not inferred names. SDK37's `egress/stats$5_10_26q2` directly calls helper IDs **1,2,46,47,68,84,85,86,95,107,125,131,132,133**. All code is inlined: no BPF-to-BPF calls exist in that section; the2221 instructions fit the old4096 instruction limit. Thus BPF subprogram support and a raised instruction limit are **not demonstrated prerequisites** for this object.

| Node | Needs | Concrete implementation surface / gap |
|---|---|---|
| E: original egress policy | L,V,S,T,M,A | SDK37/API routing plus real required pins and attachments. Do not claim kernel5.10 to make gates pass. |
| L: lookup84/85 and release86 | V,N,R | `net/core/filter.c`, TCP/UDP v4/v6 lookup APIs; preserve tuple validation, byte order, bound-device/reuseport selection, fullsock handling and no-match semantics. |
| V: safe typed socket values | pointer type, nullable refinement, aliases/spills, acquired-reference states, context conversion | `include/linux/bpf*.h`, `kernel/bpf/verifier.c`, `net/core/filter.c`; none of PTR_TO_SOCKET/OR_NULL, reference IDs, or skb->sk typed access exists in this baseline. Never mark a kernel socket pointer as an integer or ordinary unrestricted map value. |
| R: lookup lifetime | TCP held refs versus RCU sockets; release/invalidation on all paths | Existing4.9 TCP established lookup increments an atomic ref; listener lookup reports `refcounted=false`; UDP lookup returns RCU-protected sockets. v5.10 uses refcount_t and more recent lookup signatures. Blind donor calls/puts are unsafe. |
| N: namespaces/interfaces | context-derived net namespace, relative-ID lookup, put_net, interface identity | Existing4.9 lookup APIs take `struct net*`; choose skb device namespace when present, otherwise socket namespace, matching upstream helper. Preserve CURRENT_NETNS=-1, invalid-ID/flag/size behavior and IPv6/config guards. Never use global init_net or a tuple-only global cache. |
| S: socket storage map24/helper107 | B,V,C,R | New map allocation/FD-based syscall operations, value bounds, NO_PREALLOC, map/storage dual membership, memory charging, RCU unlink/free and lock order. `net/core/bpf_sk_storage.c` absent. HASH keyed by UID, FD, tuple, pointer or cookie is not a lifecycle-equivalent replacement. |
| B: BTF metadata | BPF_BTF_LOAD, attr fields, validated BTF IDs, map metadata lifetime | `kernel/bpf/btf.c`, syscall/UAPI/map ops; absent4.9. Original storage map requires key/value BTF IDs. NetBpfLoad skips BTF below4.19 and storage below5.10; both true-capability gates need explicit adaptation, not version spoofing. |
| C: creation/destruction | cgroup sock program type9/create attach2; storage-get context prototype; socket cookies; credentials | `af_inet.c`, `af_inet6.c`, cgroup attach validation/effective programs, sock context validation/conversion/helper dispatch; hook must run before socket publication and propagate original permission verdict. Helper46 must accept sock context in create, not reinterpret it as skb. |
| C continued: clones/free | initialized storage pointer, clone policy, final destructor cleanup | `include/net/sock.h`, `net/core/sock.c`; reset copied pointer before **any** clone failure path, clone only when map requests it, unwind partially cloned storage, free once at final sock destruction. cgroupsockrelease for cookie cleanup is separate from storage destructor. |
| T: BOOTTIME helper125 | timekeeping implementation and dispatch | Do not replace with MONOTONIC across suspend. Upstream donor uses `ktime_get_boot_fast_ns`; its availability/NMI safety must be audited before exposing it to every program type. This spike does not certify that timekeeping backport. |
| M: metrics/other reachable calls | ringbuf map27/helpers131–133, LRU_HASH9, reserve-reference verification | Even runtime metrics=false leaves these calls in the original loaded ELF. Ring buffer needs mmap/poll/wakeup/memory ordering and verifier reserve/submit/discard lifetime; LRU eviction semantics must survive. Existing core HASH substitutes are not qualification for these enabled paths. |
| A: existing accounting/local network | 1,2,46,47,68,95 plus original maps | 1/2/46/47/68 have prior targeted qualification. Helper95 fullsock and typed field accesses are additional gaps in original5.10 egress. Retain separately qualified core LPM and relative-header fixes. |

For unchanged full SDK37 program behavior, also retain the create/release, bind, sockopt and permission-migration consumers selected by the loader/handler. Adding every modern bind/sockopt/L4S feature is **not** established as necessary merely to deny the run-r18 UDP cases. Conversely, a successful UDP microtest cannot qualify those Android integration paths.

This is a functional dependency graph, **not an apply-ready transitive upstream commit series**. The earliest donors' surrounding verifier representations differ from4.9. A complete minimal commit closure or broad subsystem backport has not been compiled or certified here. The concrete connected prerequisite set above is enough to rule out the proposed small helper-only fix without pretending all of Linux5.10 is unavoidable.

## Primary upstream implementation sources

Actual source/patch bytes are retained under `inputs/upstream/`, with hashes in `evidence/handoff-manifest.json`; these are reference inputs, **not staged patches for this4.9 tree**.

* [6acc9b432e67: socket lookup helpers](https://github.com/torvalds/linux/commit/6acc9b432e6714d72d7d77ec7c27f6f8358d0c71), paired with [fd978bf7fd31: verifier reference tracking](https://github.com/torvalds/linux/commit/fd978bf7fd312581a7ca454a991f0ffb34c4204b). Original donor netns semantics differ from the current negative CURRENT_NETNS convention, so use the captured v5.10 implementation as the contract reference.
* [6ac99e8f23d4: socket local storage](https://github.com/torvalds/linux/commit/6ac99e8f23d4b10258406ca0dd7bffca5f31da9d), captured v5.2 monolithic storage and v5.10 split storage/local-storage bodies. A backport can retain early typed-socket prototypes; copying the entire modern BTF-ID pointer conversion framework is not inherently necessary. Map BTF metadata remains required by the original map ABI.
* [f7c6cb1d9728: storage in cgroup socket programs](https://github.com/torvalds/linux/commit/f7c6cb1d9728dea9d9f131ef57303d6821afb0f8), plus [610236587600: cgroup sock create surface](https://github.com/torvalds/linux/commit/61023658760032e97869b07d54be9681d2529e77). Neither is a standalone4.9 application.
* [71d19214776e: BOOTTIME helper](https://github.com/torvalds/linux/commit/71d19214776e61b33da48f7c1b46e522c7f78221), actual helper and dispatch diff retained.
* [7cbd0c4cebe4: clone early-failure UAF fix](https://github.com/torvalds/linux/commit/7cbd0c4cebe4c9f678d15e6b9ba975e1155a107f), with [f12dd75959b0](https://github.com/torvalds/linux/commit/f12dd75959b0138f94da8ddcf43f2f3cf277216d). This demonstrates why resetting storage only late in the clone helper is insufficient. Apply the invariant to4.9's `sk_clone_lock`, not modern hunk offsets.
* [v5.10 filter](https://github.com/torvalds/linux/blob/2c85ebc57b3e1817b6ce1a6b703928e113a90442/net/core/filter.c), [storage](https://github.com/torvalds/linux/blob/2c85ebc57b3e1817b6ce1a6b703928e113a90442/net/core/bpf_sk_storage.c), [verifier](https://github.com/torvalds/linux/blob/2c85ebc57b3e1817b6ce1a6b703928e113a90442/kernel/bpf/verifier.c), [ringbuf](https://github.com/torvalds/linux/blob/2c85ebc57b3e1817b6ce1a6b703928e113a90442/kernel/bpf/ringbuf.c), and [BTF](https://github.com/torvalds/linux/blob/2c85ebc57b3e1817b6ce1a6b703928e113a90442/kernel/bpf/btf.c) bodies anchor the later contract, not a proposal to import every facility they contain.

## Existing-hook alternatives

Existing cgroup egress is the correct verdict location and already maps drop to EPERM, but exposes only the packet's associated sender socket through helper47. It has no destination lookup or creator-storage API. Existing ingress changes `skb->sk` to its supplied socket before running the program (`kernel/bpf/cgroup.c:401`); it does not expose both required identities together, and dropping there changes sender-visible send behavior. A userspace tuple registry misses pre-registration packets, UID changes and FD/port reuse and cannot reproduce kernel reuseport selection atomically.

`sk_uid`/inode UID is not creator identity: frozen `net/socket.c:537–548` updates `sk_uid` during `sockfs_setattr`. Permissioned owner changes after creation can therefore diverge from `SkStorageValue.uid`. Current task credentials are also wrong after SCM_RIGHTS, fork/exec or setuid. xt_owner/xt_bpf has the same missing receiver identity. Per-socket filters are not a mandatory global create-time policy and do not reproduce the original egress verdict. Kprobe/perf return values do not install a packet-policy verdict or a safe destination-socket API.

A **new private kernel helper** returning a UID snapshot could keep references entirely inside the kernel and avoid exporting socket pointers. That is a possible alternate design, not disproven by this audit. It would still require creator capture/free/clone rules, namespace-correct destination selection, per-sender cache semantics, metrics and Android map/loader ABI changes. It is neither an existing-hook solution nor the original SDK37 helper/storage interface. No implementation or equivalence proof has been established, so it is not presented as a minimal sound fix. Further design would need an explicit behavioral comparison against the contract tests and real sockets, not just the run-r18 pair.

## Work implemented and verification limits

Run `python3 tests/run.py` from this spike (or its absolute path). It extracts ten unchanged production function bodies and seven unchanged struct definitions, recording source lines and hashes, then compiles a native harness with ASan/UBSan and a freestanding **AArch64 ELF object** for ABI assertions. Helper doubles are explicit in `tests/doubles.h`; no production policy body is rewritten.

Passing checks:147456 permission combinations over nine UID/profile relationships;230400 full-UID chunk edge reads across the representable UID range; IPv4/IPv6 tuple contents and sizes; lookup-missing/storage-missing original allow paths; receiver release-call balance; same-UID and same-profile controls; TCP SYN versus established bypass; UDP cache expiry at10ms and destination-port change; switch-off controls; creator UID/GID/cookie capture, storage allocation failure and both permission migration branches. Exact compiler commands/stdout are in `evidence/host-tests.json`.

These tests validate production logic and selected scalar/struct ABI. They do **not** validate Linux syscalls, FD transfer, skb layouts, reference counts, verifier acceptance, RCU, map destruction, cache data races or network namespaces. The generated target object is not a compiled kernel translation unit. No new networking runtime success is claimed.

Local host: Darwin arm64 / Apple clang21. Each child is limited to30 CPU seconds and45 wall seconds, one job. Static mocked state is under2MiB; Darwin's RLIMIT_AS is not a reliable physical-memory limit and is not claimed as a1GiB cgroup cap. Remote read actions used60-or-less CPU seconds and1GiB virtual-address limits. No remote compute fixture ran.

## Implementable next unit

Take **V+L+R+N: typed socket references and lookup/release**, before socket storage or enabling the Android wrapper. Adapt the actual fd978/6acc code to the single-frame4.9 verifier; retain public IDs84/85/86, 12/36-byte tuple ABI and modern CURRENT_NETNS convention. Keep public dispatch unavailable until nullable refinement, alias/spill invalidation, branch-state equivalence, exit/tail-call leak rejection, helper argument validation and read bounds all pass. No BPF subprogram backport is required by this captured ELF.

The reviewable unit should change `include/uapi/linux/bpf.h`, `include/linux/bpf.h`, `include/linux/bpf_verifier.h`, `kernel/bpf/verifier.c`, `net/core/filter.c`, plus only the lookup declarations/adapters required by the real4.9 TCP/UDP namespace APIs. Derive reference handling separately for held TCP established sockets and RCU listener/UDP sockets; use4.9 atomic APIs rather than casting atomic_t to refcount_t. Do not put a borrowed RCU socket as though it were an acquired ordinary reference. Verify IPv6-disabled compilation and namespace teardown. Compile only changed kernel objects against a new isolated minimal overlay/generated-header set under the allowed new prefix, one job; no full kernel build or reuse of mutable owner outputs.

Acceptance must include actual verifier negative programs from the retained upstream `ref_tracking.c`: null dereference, release-null, leaked lookup at exit/tail call, double release, use after release through a register alias and a spilled alias, pointer arithmetic/casts, invalid tuple lengths/flags and misuse of unrelated map values. Positive cases acquire/check/release exactly once on every branch and preserve alias state across joins. A kernel object compile alone is not verifier execution. Running these programs later requires a separately reviewed kernel/runtime action; this task did not do it.

Only after this unit passes should BTF+socket-storage allocation/free/clone and creator initialization be integrated, followed by boottime/metrics and explicit loader capability selection. Keep the old qualified core handoff independent throughout. `runtime-test-plan.md` defines the final socket gate. Until it passes, cross-profile isolation remains a failed release gate; physical/flash/WiFi/Google/Android-services GO remains absent.
