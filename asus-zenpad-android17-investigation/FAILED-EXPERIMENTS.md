# Failed and inconclusive experiments

Failure is part of the investigation record. “No output” is usually an unknown observation, not proof a specific instruction never ran. Offline/static passes are reported separately from actual physical results. The ledger links each independent spike; these are grouped hypotheses, not a claim of exact within-day ordering.

## Reporting and entry controls

- **Stock scalar checkpoint:** a before-reset read observed 167 while the saved field read 0. The writer/getter pair did not qualify a cross-reset channel. Adding speculative cache flushing was not supported by the inspected Device mapping/barrier path.
- **USB configfs reporter on stock:** no report appeared. Stock used a legacy gadget contract, so this negative could not diagnose 4.9.
- **Strict entry guards:** whole-DT equality and a minimum Linux-record offset 0x200 rejected legitimate firmware/OEM layouts. Stock controls and exact observed geometry corrected these assumptions; an older missing marker remained unknown.
- **Blanket 2MiB initrd theory:** exact LK/kernel analysis refuted the static premise for the inspected successful path. It did not retroactively establish the failed trial's actual bounds.
- **Cached LASTPC/reset32:** numeric values existed, but firmware capture/normalization was absent from the inspected source. Decimal 32 was never established as raw RGU bit 5, watchdog timeout or thermal reset.

## Liveness and timer hypotheses

The full kernel reached small userspace and occasional bounded progress, including a correct shorter computation. A complete 2M computation plus independent timer growth was not demonstrated.

- Idle polling/nohlt, direct clock syscalls instead of vDSO, a runnable timer observer and a headless RDMA registration-skip each changed an exposure without producing the required complete physical liveness result. None became a shipping fix.
- Scheduler and work-dispatch captures placed a runnable PID1 next to worker activity, including `power_supply_changed_work`, battery voltage and ADC paths. They did not prove an eternal deadlock or name an exclusive culprit.
- A selected PMIC delay switched to raw CNTPCT. That delay returned with a matched later record, but the baseline sample also returned and subsequent ADC/PID1 completion remained absent. The result did not establish a virtual-counter root cause.
- A finite PMIC poll backstop retained its normal deadline/recovery behavior but produced no qualifying exhaustion/resolution evidence. Missing records could have been undrained.
- Sparse recording, a temporary FIFO control, normal-priority pure computation, final-only computation and devkmsg return-boundary controls reduced or moved instrumentation. Partial retained output did not qualify stable execution. A kernel-side return stamp occurs before actual EL0 resumption.
- Omitting one battery-notification ADC readout allowed that notification to return, yet the desired helper sequence remained incomplete. Another channel 6 reader remained; the tested omission was not a causal cure.

## Minimal-platform build failures

These were three make invocations for one coarse experiment, not three physical experiments:

1. Removing the in-house TEE branch while keeping DEVAPC exposed undefined types and warnings-as-errors. The build stopped.
2. Restoring the ancestor TEE closure let DEVAPC compile, but linking exposed missing tracing, netdevice-notifier and display-cooler symbols. The build stopped again.
3. A bounded dependency correction retained nop/core tracing and generic NET infrastructure, and removed the already absent-display-specific cooler. The kernel linked and packaged. Protection-related BAT/SOC/PMIC/thermal/CPU-frequency/SPM/HPS closures stayed; this was never bare-core.

No stubs, warning suppression or repeated clean builds were used to pretend those dependencies had disappeared.

## The final two trials

**Reduced platform:** full-p10 SHA256 `9939e802ab349dd01fe5ab9c643f2ce0d3219846e3f54513a9b1e9982146965c`. Fresh entry/PID1/uname and normal scheduler were present. Last helper record was `compute-begin`; two thermal deferred-probe records followed. No completion or timer stage. Stock returned.

**Global delay budget:** full-p10 SHA256 `b3ff63a119f791e8d38ab75d2586aba52cf77086026cdfb7ff3fab706d1474c1`. The new kernel identity was present; the intentionally reused helper was bound through the exact package. Same helper boundary, no exhaustion/panic. New stock return verified. Missing exhaustion cannot rule out a stuck read instruction, repeated shorter calls, failure to publish, starvation or another obstacle. Neither result authorizes a chain of further variants.

Both complete retained logs were 16,737 bytes; their SHA256 values are respectively `d8875e65366c8bf6e8a7ddffe0c1d05edea5f11b2cf3210a28cd85163cdc5096` and `e22ab1b87d2e61e20edc6a09b7f6779739f4c4a4b261a08dab6d4093d4abd99a`. Private raw bytes are not published.

## Product/runtime failures that must not be mistaken for this hardware stall

- A literal WebView LFS pointer failed the genuine manifest checker; materializing the pinned object solved that input problem.
- A launcher added an unrequested 56GiB address-space cap and Soong failed allocation. Removing it did not constitute a product fix; a later supervisor stop also did not constitute a successful build. Subsequent successful builds have separate receipts.
- Host validators had path/dependency/sensor-manifest mistakes; fixes preserved the failed original runs instead of rewriting them as success.
- Guest linkerconfig duplicate providers, missing BPF map-info support and unsupported BPF attributes were independently diagnosed. Fixture source/config parity mattered. Their resolutions do not prove physical kernel stability.
- Full low-RAM Android/Google usability stayed unproved despite lmkd surrogate tests. An incompressible overload case failed. High assertion counts were not a measure of tablet readiness.

## Stop condition reached

After successive ambiguous physical results, the port was parked. The missing information was execution context/caller or same-thread userspace resumption, not another guessed timer constant. A future restart needs a genuinely distinguishing observation and a bounded decision, not continuation of this experiment count.
