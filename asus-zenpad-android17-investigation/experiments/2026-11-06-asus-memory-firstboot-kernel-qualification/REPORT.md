# Existing memory Image: scoped firstboot reuse accepted

The existing memory-qualified virtual Image may be used in a later fresh genuine services fixture while preserving the **exact selected firstboot correspondence and the already qualified memory correspondence, with its explicit exceptions**. No source patch or kernel build is required for that scope. This is pre-runtime input acceptance: no new fixture was built or booted, no fullkernel equivalence is established, and physical GO is false.

The Image is `c59e030cdfc3e752eeddbbf62d091ae9760c94d5fbf780a22824e004ec872080` (5,922,824 bytes); its resolved config is `0426746d90db074dd026ae5d383e1cde27d587020699d5dc9af4faac0b54489f`. Both actual remote files match the frozen memory export and successful historical resume receipt. `CONFIG_IKCONFIG=n` on this virtual kernel: the config association is supported by the terminal build/run provenance and exact artifact hashes, not a claimed extraction of embedded config.

The actual physical BMC Image.gz-dtb is still `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1` (7,716,897 bytes), and actual config is `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`. Both independently rehashed successfully. This kernel has no physical execution acceptance.

The machine decision is [acceptance.json](acceptance.json); future inputs are governed by [next-fixture-contract.json](next-fixture-contract.json). The local verifier passed 27 assertions, including all 510 frozen memory payload hashes/sizes.

## Exact selections and authority

All 290 firstboot source paths byte-match both frozen pins and actual physical BMC sources. All 134 firstboot options match the physical values exactly. All 210 memory source paths likewise match their frozen and physical pins. All 72 memory options preserve the frozen memory selection; 67 are literally equal to physical, four are disabled with different representation, and one is the real DEBUG_PREEMPT difference below. It would be incorrect to call this strict 72/72 literal equality.

The authoritative firstboot path/option list is `firstboot-parity-continuation/artifacts/frozen-r3/evidence/combined-parity.json`, SHA256 `9b165061348fdc6be1112533e10341f720c45f4cdccc097991635cb4100ee403`. Its older r5 Image/config identity is deliberately retained. The later BMC parent receipt, SHA256 `bfa6a78c97f02a6b7a57551b588938a3b3c1f0759a6d7d7c34439fbe19acc7fa`, extends those exact selections to e9cde06e/10b212ca. We rechecked actual BMC files rather than treating the older r5 artifact identity as the current physical identity.

The authoritative memory source manifest is SHA256 `dc61bcb0fbd04e0682827276354c5db3c41a7a3ff3d2e6c9a6d01d316ae14002`; the 72-option manifest is `1bd55945a7babb446cb32aef51926610a13248318a9f241035e7bf998f168057`. Exact path lists, per-path hashes, option values, manifest bytes and original filenames are retained in [authorities.json](evidence/authorities.json) and [remote-inspection.json](evidence/remote-inspection.json).

Source roots resolve to `/srv/android/asus-sdk37-lmkd-functional/kernel-memory-r1/source` and `/srv/android/asus-bmc156-full-kernel-r1/kernel`. In particular, the physical root is **kernel**, not a guessed `source` directory. The 498 unique selected paths were also tied to the BMC full postimage manifest reconstructed from the pinned complete r5 map plus exact nine-path BMC overlay. The parent manifest canonical SHA256 is `c636d9abad7de61e242268372a3b6e3e0cc0ff23f1926274db21f17a6dd81124`. The fetched remote map and reconstructed local map agree. The supplement's compact-JSON digest `20898a59…` uses different serialization from the parent's default-spaced JSON; it is not source drift. Both conventions are explicit in [verification.json](evidence/verification.json).

Compact selected source map hashes use sorted compact JSON with no trailing newline:

- Firstboot: `f0d25098a23b705a9baf65180f3b3777d438ce927c7925180d73fcf00bc213dc`.
- Memory: `d8545cb3df6673c9c2257cdf5c5e4f23672b35c1dd1e3a93165df4abdecb427a`.
- Union: `a15a26c8415ea2cbd19f39c53d2b3cf3684fc611a964540a6ea24eb8de379d7e`.

Both sides produce the same source map hashes. [selected-source-pins.json](evidence/selected-source-pins.json) contains the complete map and config selection digests.

## Differences and their consequences

Every literal whole-config difference is enumerated with virtual and physical values in [whole-config-differences.tsv](evidence/whole-config-differences.tsv): 2,515 rows, comprising 1,597 absent-versus-disabled rows and 918 other value differences. The [71 differing non-disabled virtual values](evidence/virtual-non-disabled-differences.json) are separately enumerated. These exact listings retain missing symbols rather than silently replacing every absence with `n`. They are a complete comparison of these two resolved config files, not a full source-tree equivalence claim.

The five selected memory nonmatches are:

- `CONFIG_DEBUG_PREEMPT`: virtual `y`, physical `n`. The inspected Kconfig explicitly enables debug smp_processor_id checks and preemption-count-underflow detection. This changes checks/overhead and is a real limitation, retained from memory acceptance. No tablet timing or identical scheduler behavior follows.
- `CONFIG_CMA_DEBUGFS`: virtual absent, physical `n`; the option depends on CMA and DEBUG_FS. DEBUG_FS is disabled virtually, enabled physically; this CMA debug interface is enabled in neither.
- `CONFIG_PREEMPTIRQ_EVENTS`: virtual absent, physical `n`; tracing dependency suppresses the virtual entry. No preempt/IRQ event tracing is enabled on either side.
- `CONFIG_PREEMPT_TRACER`: virtual absent, physical `n`; no preemption-off tracer is enabled on either side.
- `CONFIG_ZRAM_MEMORY_TRACKING`: virtual absent, physical `n`; it depends on ZRAM and DEBUG_FS. Neither side enables this zRAM debug tracking.

Relevant unselected differences also remain visible and restrict interpretation:

- `SCHED_DEBUG=y/n`, `SCHEDSTATS=n/y`, `SCHED_INFO=n/y`, `SCHED_MC=n/y`, and `MTK_SCHED_RQAVG_KS=n/y`, `MTK_SCHED_RQAVG_US=n/y` (virtual/physical). Source equality does not turn these different compiled selections into vendor scheduler, topology or accounting parity.
- CMA, compaction, preemption, VM counters, PSI, zRAM/zsmalloc, SWAP and the selected timer settings preserve the memory selection. CMA is enabled on both but the virtual guest has no physical board CMA reservation. The tablet's driver allocations, reserved memory and protected Android/GMS working set are not reproduced. `MTK_SSMR=y` in config is not evidence that a physical reservation exists in the guest.
- Crypto selections are materially different outside the selected gates. Examples include HMAC/DRBG/AEAD/RNG as virtual modules versus physical builtins; SHA512/RSA/GCM and asymmetric-key support are disabled/absent virtually but enabled physically. No module installation/loading was qualified here. Selected DM/verity configuration matching does not establish the entire crypto/trust path. Later genuine APEX/Keymaster/keystore tests must establish their own functional closure; this audit found no evidence that an arbitrary kernel rebuild is needed to pass those future tests.
- Hardening and failure behavior differ: virtual stack protector disabled versus physical strong, LSM mmap minimum 65536 versus 32768, panic-on-oops disabled versus enabled, panic timeout 0 versus 1, RCU stall timeout 21 versus 60. These preclude wider security/failure/timing equivalence claims.
- Virtual VExpress/PL011/virtio block/MMIO and console support, devtmpfs, different command-line defaults and board/driver selections are fixture adaptations. Physical MediaTek display, input, storage, radio, thermal and power drivers remain outside this result. No virtual VETH/NET_NS or other board configuration was copied onto the tablet; VETH is absent virtually versus `n` physically, and NET_NS is absent in both inspected configs.

The separately inspected virtual source adaptation is `drivers/irqchip/irq-gic-v3.c`, outside both selected source lists. Its only shown hunk changes `#ifndef CONFIG_MTK_SYSIRQ` to `#if defined(CONFIG_MTK_GIC) && !defined(CONFIG_MTK_SYSIRQ)` around MediaTek polarity setup. Virtual hash is `143c973f9d37e5956826a3ad6fc4e914e3dc2e9f3eb5b194307b3fce9ef7debc`; physical is `fa3149e3904beca728187c2bad4efb34d041e014ec17358f55e4e68372f1af42`. The exact diff is retained. This audit exhausts selected source nonmatches (none) and records that known virtual GIC change; it does not enumerate all unselected source-tree differences.

No later patch/build is required for the requested selected-scope reuse. If **strict enabled-debug-option equality** is newly required, the smallest later change is `CONFIG_DEBUG_PREEMPT=n` in a new owned virtual stage, followed by config resolution, a serial Image build, new exact pins and repeat relevant memory/firstboot runtime qualification. Do not modify the physical config or merely add disabled lines to a generated config. That optional replacement would not inherit c59e's binary identity or tests automatically. Wholekernel parity would require a different, substantially broader task and is not proposed.

## Future genuine runtime

The old `95a62a8b…` firstboot kernel lacks PSI/zRAM and remains unsuitable for positive lmkd qualification. Its firstboot runtime observations are historical evidence; adopting c59e requires actual firstboot runtime requalification in a new fixture. Four eligible memory pressure/recovery cycles passed in the accepted c59e fixture. The protected incompressible overload failed with swap write errors and no recovery. Those facts are preserved separately; neither native fixture proves a full Android/GMS/root working set.

The prior genuine services fixture established enforcing init and both manager IPC responses, then stopped at the mandatory missing platform BoringSSL self-test; signed runtime APEX activation/trust, Keymaster, keystore and downstream readiness remain unproved. Its 872,703-byte policy is a different coherent capture from the memory fixture's 872,537-byte policy. Do not mix those policy/CIL/context/property/ELF groups.

The separate official coherent capture is not yet admitted or consumed here. After its owner supplies a terminal qualified build receipt and exact reviewed r8 profile, create a fresh fixture revision and validate every complete input group with before/copy/after hashes. Require real implementation ELF dependencies, official platform 32/64-bit self-tests, signed runtime/bootstrap APEX contents and trust metadata, generated properties/apexkeys, and coherent policy/context/VINTF/init outputs. Preserve genuine crypto/APEX waits; readiness remains owned by the actual services. A small [NEXT-RUNTIME-CHECKLIST.md](NEXT-RUNTIME-CHECKLIST.md) and the machine contract specify the handoff.

For future lmkd inclusion, independently review the exact `/dev/block/zram0 u:object_r:swap_block_device:s0` context candidate (SHA256 `3c9be94080cd5d2b146bd52e325545bc7b27e86395413e16ae650d3895c2426c`), with no allow-rule expansion. Verify actual consumed low-RAM properties, lz4, mkswap/swapon, PSI descriptors/EPOLLPRI and genuine lmkd SID. A changed official daemon or policy requires its own functional checks. One CPU/1GiB services execution would not reproduce the prior approximately-stock-RAM memory test.

## Execution boundary and continuation

Only the authorized product-input-build-kit SSH wrapper performed remote inspection. New remote writes are confined to `/srv/android/asus-memory-firstboot-kernel-qualification-20261106/{inspection.json,supplement.json}`. Each remote Python inspection ran on one CPU with a 1GiB address-space cap and 120-second CPU cap; all calls are terminal. No subprocess build/runtime, lifecycle control, supervisor/lock read, active source/out write, device/ADB/root/private calibration/key-content operation occurred. The original full product r8 supervisor was not inspected or modified.

Local continuation: read acceptance and contract, obtain the separately owned future capture, then perform the future fixture work under its own authorization. `scripts/finalize.py` can reverify the existing local evidence without SSH. The SSH scripts deliberately reject reusing their remote receipt paths; do not rerun them against those paths. Reference hashes and remote source/Kconfig excerpts are retained in `evidence/`.
