# Final-byte Connectivity/netd qualification

**PASS for the scoped Connectivity/netd runtime tests. Whole-platform/boot/physical/flash approval remains false.** Exact final `netd.o` (`863f3d2e79e804559c90ec145f23210d48f841777bb646a5f3f4b45952aad4b8`) and `netd@funcs.o` (`b5f8f4bf79dfbd6403405163b768a3307b43fd30d90b19ac3fd2260d746ff9c4`) were present with genuine installed Connectivity loader `2bf5e22c967a3e2ab38ef0699056616346fd3dceae230f5950e9f4de82839985`. Every one of the frozen 26-object closure hashes matches the actual and map-test initramfs inputs.

The genuine loader loaded netd's seven selected programs and created its maps, then marked mainline loading complete. Its subsequent unchanged platform/vendor chain failed critically on final `filterPowerSupplyEvents.o`, exit121. This is **not a whole-chain pass**. Neither the vendor repair candidate nor its worker was consulted. Genuine SetProperty exit125 remains historical; this run never reaches it.

Results:

- 31 selected netd map metadata checks and 31 CRUD/restore checks passed in a fresh guest using the immutable genuine loader helper; exit0.
- Genuine BpfHandler initialization/tag/forbidden-tag/untag passed; exit0.
- 10 IPv4/IPv6 doze/standby allow/deny packets passed; exit0.
- 60 routed packet cases passed over veth and tun, covering IPv4/IPv6 TCP, UDP, DNS wire answers, doze, VPN lockdown, wrong/allowed IIF, local-prefix denial/host exception/removal, and xt_bpf user/admin penalty policies; network probe exit0.
- All four local-prefix denials returned `tx=-1`, `errno=EPERM` before transmission. VPN ingress denials instead allow outgoing transmission and prevent delivery, as expected.
- Separately replacing mandatory netd.o with 29 malformed bytes made the **genuine final installed loader** log `netd.o too small: 29`, abort with SIGABRT (harness exit134), and leave mainline_done absent. This qualifies malformed-file rejection, not graceful recovery or a valid-ELF verifier negative. Downstream failed probes in that negative guest are expected, not positive qualifications.

Actual final SYSTEM `/system/build.prop` SHA `985595ce4c8c20600ca942c8d3475f92bea8d1f2199bec74aa21abc16a16f5ce` supplies SDK37, sdk_full37.0, codename **Baklava**, and userdebug. Its existing `ro.bpf.allow_legacy_kernel=true` is retained exactly; no new policy relaxation. `ro.board.first_api_level` is absent and is not invented from vendor `ro.product.first_api_level=23`. The genuine loader default applies. Captured `/system/etc/init/netbpfload.rc` and the actual source_apex_version symlink `373399999` yield API3705 through the real probe code. Property names/values/source hashes and read sites are exported. No readiness property is seeded; no kernel-version override is set.

The exact funcs object remains in the closure. Genuine Linux4.9 selection uses netd.o. Captured loader source gates funcs on Linux6.6.118; no execution claim is made for the unselected variant, ring buffers, or sk_storage. See `evidence/genuine-loader-netd-selection.txt` for actual selected maps/programs and skips. The final installed loader is byte-bound through the APEX; independent full C++ source/compiler provenance is not claimed.

The minimal fixture has no Android property service or complete linker configuration/SELinux property labeling. Bionic property-area creation reports an xattr failure on devtmpfs; the area remains usable and all five actual product values are added and read back successfully. Generic captured property_info and immutable qualified dynamic libraries/probes are retained. No namespace owner's Android-init fixture was duplicated. Missing platform aconfig storage remains a disclosed pre-existing whole-platform boundary; it did not block these Connectivity checks. Cross-profile loopback and UID permission migration remain **OPEN/FAILED**; flags and hooks were not changed.

Earlier attempts are preserved: property-area return handling stopped the first guests; r2 exposed the captured loader's explicit abort on map reuse plus absent firewall binaries; r3 metadata lacked BPFFS pin directories. The final packet guest includes genuine immutable iptables/ip6tables, and map tests run in a fresh guest with required directories. These are owned fixture corrections. Versioned init sources were recompiled at the original source pathname and reproduced both final guest init hashes exactly.

All QEMU runs use one vCPU,384MiB,TCG single thread,no external NIC,one host CPU affinity,1GiB address-space limit,and a finite90-second timeout. All completed without timeout/manual host signals. Final acceptance runs:

- run-r3-actual: 0:51.07, peak RSS 189452 KiB
- run-r4-metadata-crud: 0:01.83, peak RSS 186632 KiB
- run-r2-mandatory-malformed: 0:02.22, peak RSS 124136 KiB

Owned remote allocation at final audit: 56139776 bytes (<512MiB). Only tiny fixture init/property-seed code was compiled; no Ninja/Soong/kernel/native product build or active source/output write occurred. Existing guest network harness internally terminates its own virtual peer/relay processes; no external/device/worker process was signalled.

Raw SYSTEM was neither copied nor rehashed: frozen pre/post capture/runtime SHA04b4 receipts were reused, its0444 size/inode/mtime rechecked, and every small extracted object/loader rehashed. Original frozen receipts are byte-identical. No credentials were copied.

Parent acceptance boundary: accept these exact-byte scoped netd behavior results and the malformed negative. Whole-platform loading still requires the separate vendor-filter repair and future authorized exact-final-byte retest. Android init/property-service/linker namespace integration and the known cross-profile/UID-migration failures remain with their owners. No boot, physical-device, flash, or service-ready GO follows.

Reproduction: review `scripts/`, `evidence/final-report.json`, and final run command/input/resource/log receipts under `evidence/remote/`. Existing run paths are immutable; choose a new owned run name before rerunning. Never substitute historical c523/25ccea netd bytes or seed guessed build values.
