# Vendor BPF load compatibility

Question: Which exact syscall condition rejects the installed critical healthd filter, and what smallest supported change resolves it?

Status: BPF rejection reproduced and resolved by a staged two-line loader guard. One candidate final-SYSTEM startup passed genuine bpfloader exit 0 and bpf.progs_loaded=1, then started both zygotes. HWC status-1 exits triggered SurfaceFlinger/zygote restart cycles. No completed framework or hardware result. Stop detection was delayed about 81.6 guest seconds after the first HWC exit; the first-boundary stopping requirement was not met.

Outputs:

- [report.md](report.md): precise cause, physical-source comparison, staged change, actual runtime and limitations.
- [HANDOFF.json](HANDOFF.json): exact source/patch/ELF/kernel/config/SYSTEM/BOOT identities and outcome.
- [source/loader-prog-name.patch](source/loader-prog-name.patch): measured-kernel >=4.15 guard; active product untouched.
- [evidence/focused-replay.json](evidence/focused-replay.json): actual installed-loader captures, minimal replay and boundary evidence.
- [evidence/boot-boundary-lines.txt](evidence/boot-boundary-lines.txt): genuine startup progress and next failure.

Continuation: No additional startup or automatic patch is authorized by this packet. Parent may review the staged product-loader change and separately isolate the first HWC exit. Preserve original failures and enforcing policy. Kernel/config and immutable SYSTEM/BOOT were unchanged; candidate runtime used an explicit owned one-file library overlay. No full-OS/hardware/flash GO.

Remote owner: /srv/android/asus-vendor-bpf-load-compat-20261107. DATA, keys, entropy, binaries, COW and full logs stay there. The VM scheduled stop remains unchanged. No subagents, broad suites, full product/kernel builds, physical operations or active product/source/out mutations occurred. Two leaf compile/link attempts and three small syscall fixtures are preserved.
