# Android 17 / Linux 4.9 networking runtime qualification

Status: **targeted networking repairs qualified; Android 17 network/security readiness is not complete.** A real cross-profile loopback policy failure remains. No tablet, ADB, root, flashing, active AOSP tree or active product kernel was changed.

## Qualified repair

The frozen active Connectivity source already includes legacy patches 04/05. Its APEX31 NetBpfLoad translation unit defines `__ANDROID_APEX__`, so the runtime kernel checks evaluate the genuine Linux 4.9.337 kernel. Tests use SDK full 3701 through real Bionic property storage; no kernel version override or readiness-property forgery was used.

The original SDK37 `netd.o` loaded maps and allowed `BpfHandler::init()` to succeed, but the absent cgroup programs silently bypassed UID doze/standby policy. The staged repair restores real cgroup programs, requires their attachment, rejects required object failures, validates actual map metadata, and supplies real LPM-trie behavior instead of HASH substitution.

A donor relative-header helper initially blocked local-network responses while allowing the outgoing packet to escape. Tightened tests caught this. The series includes upstream [0f5d82f187e1beda3fe7295dfc500af266a5bd80](https://github.com/torvalds/linux/commit/0f5d82f187e1beda3fe7295dfc500af266a5bd80), which allows network-header reads when an outgoing skb has no MAC header. Local-prefix denials now require `send()` to fail with `EPERM`.

`run-r14`, against Image SHA256 `f48955e15b0210d0b14c9d8036b6655e353a02c9e46ae5fc015b252b9bd8eac6`, passed:

- 60 map-info/LPM/relative-helper API checks, plus the separate unprivileged-BPF denial check. Coverage includes malformed lengths/pointers/FDs, error-buffer zeroing, concurrent FD replacement, reference release, longest-prefix lookup, capacity replacement, existence flags, enumeration and concurrent updates/deletes.
- All five Connectivity objects: offload, test, clatd, dscpPolicy and netd. Fifty map metadata checks and 49 map read/write/restore checks passed. The one skipped CRUD case is `socket_policy_cache_map`, a PERCPU_ARRAY; its metadata was checked.
- Actual `BpfHandler` source initialization, TCP startup self-test, tag/untag and unauthorized tagging rejection.
- Ten loopback UID policy cases and 60 routed packet cases over isolated veth and TUN. Positive traffic includes IPv4/IPv6 TCP, UDP and DNS A/AAAA wire queries. Denial checks cover UID policy, VPN lockdown/interface filtering, local prefixes and exceptions, and real xt_bpf iptables penalty rules. Eight iptables rule add/remove operations passed.

These are targeted real-source/ELF tests with actual Linux syscalls and packets, not an Android framework boot. DNS wire tests do not establish DnsResolver service integration. WiFi hardware, Google services, interface-accounting totals and all higher-kernel accelerators are not qualified by this fixture.

## Remaining concrete security blocker

`run-r18` sets the real `loopback_checks_enabled` map to true. A socket created under UID 110002 (its inode owner verified after FD transfer) still receives UDP from UID 10001, on both IPv4 and IPv6, although the actual Android17 loopback policy should deny this cross-profile access. Same-profile and checks-disabled controls pass. The ordinary Android INTERNET-group restriction also passes: UID10001 without group3003 cannot create IPv4/IPv6 sockets (`EACCES`).

The generated platform `FeatureFlagsImpl` defaults `useLoopbackInterfacePermissionEnabled` to true; the runtime flag store can override it. The generated Connectivity UID-permission migration accessor also defaults true. This is not permission to disable either flag. The 4.9 branch lacks the real socket-lookup/socket-storage and associated verifier support used by the newer loopback program. Full cross-profile enforcement needs those properly qualified backports or a sound alternative design. SDK37 permission-migration integration still needs real service/process lifecycle testing.

**The passing core networking cases must not be represented as complete Android17 policy enforcement.**

## Whole loader follow-up

The rebuilt complete NetBpfLoad executable loads Connectivity, writes its normal `mainline_done` marker and executes the captured SDK37 Rust platform BPF loader. With the genuine `bpfRingbufProg.bpf` present, `run-r15` aborts on its debug-only ring-buffer self-test (`EINVAL` on 4.9).

Separate patch12 gives only that debug self-test its real minimum kernel version, 5.8. It preserves critical failure handling on supported kernels and does not suppress mandatory networking failures. An isolated Rust rebuild used the actual Ninja compiler command and dependencies, with all outputs redirected to this spike and compilation limited to one thread.

`run-r16` then executes the real chain through the vendor loader and back to `netbpfload done`. It exits125 at the actual `SetProperty(bpf.progs_loaded=1)` because this minimal fixture has no property service. No ready property was supplied manually. Some optional platform BPF files were not captured; this does not qualify platform metrics or a full Android boot.

The strict BpfHandler negative test rejects a missing required cgroup egress pin. Failed fixture attempts and their logs are retained.

## Integration and equivalence

Immutable core handoff: [artifacts/handoff-r1/manifest.json](artifacts/handoff-r1/manifest.json), also `/srv/android/asus-network-runtime/handoff-r1`. Manifest SHA256: `d6790e2efde8ddb11102f561b5c58129660be09d41f1bbfb66402f3865ef13dd`.

Apply the kernel patches in order: 01 map-info, 02 LPM trie, 03 relative-header helper and dispatch, 04 unset-MAC egress fix. Apply Connectivity patch11 against the frozen active source; it supersedes experimental patch10, so do not apply both. The platform patch12 is a separate supplement against `system/bpf`.

The four kernel patches applied with fuzz0 to isolated files from physical baseline `717bb3c9e13ce573cfdd2dda856debd27a0fa17f`; resulting files exactly match the runtime-tested source. The baseline physical and virtual commits agree across 1,719 relevant source files. Sixteen core configuration checks match. Manifest files contain exact before/after source hashes, patch hashes, config hashes, test inputs and logs.

No new physical config option is required by this BPF series. Preserve physical `CONFIG_FILE_LOCKING=y`; it was missing in the original virtual fixture. `DUMMY`, `VETH`, `NAMESPACES` and `NET_NS` are virtual-test options only. Do not copy `network.config` onto hardware.

Coordinate the separate first-boot requirement `CONFIG_BLK_CGROUP=y`. The first-boot owner supplied Image `12c7ce00abe2a4a3adeadf87cda09a30479d61379f2b5bebf5534e1cd9238c27` with that sole enabled delta and unchanged SDK37 cgroups.json `ab2ed667ff45958843fb0c6ee953a5512def0ae87470c4358aa9576a6a4b2e22`. This networking fixture did not modify that owner's inputs or active build.

## Continue

Have the parent/main owner review and serialize integration. Recheck final combined-source hashes against the manifest and repeat the relevant tests on the integrated virtual kernel before hardware use. For full loader completion, use genuine Android init/property service and the final images; do not replace readiness with a fixture value. Treat cross-profile enforcement as a failed release gate.

All fixture scripts are under `source/`; all remote writes stay under `/srv/android/asus-network-runtime`. `run_fixture.py` requires a new run label and records the exact Image, initrd input hashes and QEMU command. Runs use one CPU, 1536MiB and `-nic none`; veth/TUN peers are inside the guest, with no external network exposure. Preserve previous attempts and immutable handoffs.
