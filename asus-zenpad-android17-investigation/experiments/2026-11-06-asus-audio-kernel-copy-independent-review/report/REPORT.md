# Independent review: three-file DL1/UL1 PCM repair

Disposition: **request changes**. Five findings remain: R1/R2/R4 are P1, R3/R5 are P2. The repair corrects the central Linux 4.9 callback contract and passes its supplied software tests, but is not ready for parent integration as submitted. No production fix was applied. No physical GO, activation, route qualification, linked repaired kernel, or replacement for the current r3 kit is provided.

Reviewed patch: `7acf16bd5ecad4c2e476fb1faf21c5d704b02e18d2728ad6f76e2818ee66c1fd`. References below use the preserved `../inputs/` tree; `audio/` means `sound/soc/mediatek/mt_soc_audio_8163/`. All modified/new production code is confined to `audio/mt_soc_pcm_dl1.c`, `audio/mt_soc_pcm_capture.c`, and `audio/mt_soc_pcm_transfer.h`. Unmodified callers and IRQ handlers were examined only to assess that delta.

## Findings and smallest parent fixes

### R1 — P1: an unchanged DL1 IRQ cursor can erase a full ring's accounting

Locations: current `audio/mt_soc_pcm_transfer.h:89,129` (new direct pointer refreshes), current `audio/mt_soc_pcm_dl1.c:187` (pointer delta), original `audio/mt_soc_afe_control.c:3441` (IRQ uses strict `>`).

The repaired pointer correctly treats equal hardware/software DMA cursors as zero progress. The unchanged IRQ treats equality as one complete ring. Putting both paths under one lock prevents concurrent writes, but does not reconcile these different delta rules. A copy or ALSA status update can sample hardware progress before its pending IRQ runs. Once a copy refills the ring, that IRQ can subtract the entire ring even though the hardware cursor has not advanced at all.

Executed reproduction `equal_irq()` in `../adversarial/tests/adversarial.c`: stereo S16, 256-byte ring; initial write index 128, DMA index 0, queued 128. Move hardware to offset 64, sample the repaired pointer (queued 64), then write 128 bytes at position 32 frames and 64 bytes at position 0. These are the two legal ALSA chunks at ring wrap. Queued bytes are now 256 and DMA index is 64. Run the exact DL1 IRQ without advancing hardware: queued bytes become **0**, DMA index stays 64. Advancing hardware another 64 bytes makes the repaired pointer return XRUN despite 192 genuinely queued bytes remaining.

This is an inherited IRQ defect left incompatible with the repaired path, whose added pointer refreshes create additional sampling points. It is not an arbitrary missed hardware lap, a simultaneous unsynchronized counter update, or a fitted-board assumption. The condition scales to larger rings.

Smallest parent fix: give IRQ and pointer accounting the same zero-delta rule; the targeted IRQ comparison should treat equality as zero progress, with dedicated equality/wrap tests. The obvious edit is in `mt_soc_afe_control.c`, a **fourth production file**. If the three-file boundary must remain strict, the parent needs an explicit revised accounting design; deleting the lock or pretending the present three-file patch fixes IRQ truth is not sufficient. Full missed laps remain a separate hardware-observation limit even after equality is fixed.

### R2 — P1: copy-detected XRUN leaves ALSA RUNNING and breaks immediate prepare recovery

Locations: current `audio/mt_soc_pcm_transfer.h:89-92,129-132`; original `sound/core/pcm_lib.c:317-320,2078-2082,2310-2314`; original `sound/core/pcm_native.c:1528`; supplied tinyalsa `src/pcm.c:1187,1672`.

The helper invokes `substream->ops->pointer()` directly and translates `SNDRV_PCM_POS_XRUN` to `-EPIPE`. That bypasses the ALSA hardware-pointer update path, which normally calls `xrun()` and `snd_pcm_stop(..., SNDRV_PCM_STATE_XRUN)`. The real read/write loop returns immediately on a negative transfer result; it does not repair ALSA state afterward.

Executed reproduction `recovery()`, both directions: begin RUNNING with a valid ring and valid request; advance mock DMA during the user-copy window until playback underruns or capture overruns. The production callback returns `-EPIPE`, but `runtime->status->state` remains RUNNING. The exact `snd_pcm_pre_prepare()` body then returns **`-EBUSY`**. Supplied tinyalsa responds to EPIPE by immediately issuing PREPARE, so its normal recovery fails unless a separate IRQ/status operation has first moved ALSA into XRUN. The test deliberately controls the legal window before that later operation.

Smallest parent fix: on a genuine pointer-detected XRUN, perform the ALSA stop/XRUN transition while holding the stream lock and **without holding the ring lock**, then return EPIPE. `snd_pcm_stop()` is already declared for this kernel; do not call the self-locking `snd_pcm_stop_xrun()` while holding the stream lock. Distinguish a real XRUN from a stale-generation/position rejection. Add a test extending through the real transfer-loop error exit and immediate tinyalsa PREPARE recovery, including capture user-buffer mutation without acceptance. A raw `.pointer` call is not equivalent to an ALSA hardware-pointer/state update.

### R3 — P2: valid ALSA cursor changes are not reconciled with the new strict position check

Locations: current `audio/mt_soc_pcm_transfer.h:95-100,135-140`; current `audio/mt_soc_pcm_dl1.c:376` (prepare); original `sound/core/pcm_lib.c:1767` (RESET); original `sound/core/pcm_native.c:1540-1555,2456` (prepare/rewind).

The new helper requires ALSA `pos * frame_bytes` to equal the private driver application index. But the platform's unchanged prepare/ioctl paths do not reset or reconcile that index when ALSA changes `appl_ptr`. A supported control operation can succeed and make every following otherwise valid write return EPIPE.

Executed `cursors()`: after a successful 16-frame prepared stereo S16 write, model the real write loop's publication of `appl_ptr=16`. A second PREPARE is legal. The DL1 platform prepare takes its already-prepared path and leaves the ring alone; the exact ALSA RESET/post-prepare bodies reset `appl_ptr` to 0. Driver write index stays at byte 64. A write at ALSA's next position 0 returns **`-EPIPE`**. Separately, the exact playback REWIND body accepts 16 frames and sets `appl_ptr=0`; the next write again returns EPIPE. The harness executes the RESET, post-prepare and REWIND bodies; the platform prepare's no-reset behavior is source-audited, not executed by this focused test.

Smallest parent fixes: reset the private ring/application accounting and invalidate pending copies at prepare/reset under compatible locks; reconcile accepted ALSA rewind/forward changes with the driver application index/count. Use the actual ALSA application pointer as authority, with a defined boundary for a callback whose core-side `appl_ptr` publication is still pending. Simply deleting the equality check would copy into the wrong position. Adding only `.ack` is insufficient: these Linux 4.9 REWIND/FORWARD bodies do not invoke it. Cursor reconciliation needs a focused parent implementation, not a HAL workaround. The inherited driver also had unsound cursor semantics; the new explicit rejection is the observable regression. This finding does not assert that inherited mmap was functional.

### R4 — P1: reboot before first PCM open now dereferences a NULL DL1 context

Locations: current `audio/mt_soc_pcm_dl1.c:98,162,330,529-535,591`.

`pMemControl` is a static NULL pointer until `mtk_pcm_dl1_open()` assigns it. The reboot notifier is registered during probe, and calls `mtk_pcm_dl1_stop(NULL)` regardless of whether any application has opened DL1. The new `spin_lock(&pMemControl->substream_lock)` therefore adds a NULL dereference to this existing caller. The old stop path obtained the ring internally through `ClearMemBlock(MEM_DL1)` and did not dereference the open-only file context.

Executed software-only reproduction: `out/adversarial-tests --never-open-reboot` sets the file context to its startup value NULL and invokes the exact notifier/stop bodies with hardware boundaries stubbed. UBSan exits **1** at the new member access in `mtk_pcm_dl1_stop`, via `mtk_afe_reboot`. See `../evidence/never-open-reboot.log`. This did not invoke a real notifier or reboot anything.

Smallest parent fix: obtain/validate the initialized DL1 memory control independently of PCM open before taking its lock (or initialize the context at the appropriate successful control initialization boundary). Preserve the notifier's ability to disable hardware before any stream has opened. Do not resolve this by assuming that userspace always opens audio before shutdown.

### R5 — P2: the reboot caller violates the generation check's stream-lock assumption

Locations: current `audio/mt_soc_pcm_dl1.c:147-148,529-535`; current `audio/mt_soc_pcm_transfer.h:125-138`.

The stop comment says trigger holds the stream lock, which is true of the ALSA trigger path. The existing reboot notifier is another caller and holds no PCM stream lock. It increments the generation outside the ring lock and can reset the ring after a callback's final generation comparison. The callback does not recheck the generation after acquiring its final ring lock, so a matching wrapped position can still pass validation and publish data after stop.

Executed `reboot_race()`: valid RUNNING DL1 ring, write index 0, DMA index 128, queued 128 of 256 bytes. During user copy, arm a boundary hook. After the callback's final generation comparison, but before its pointer-ring acquisition, another real pthread executes the exact mock reboot notifier without the PCM lock. Stop resets both indices/counts and disables the mock memory path. The pointer returns the stopped index; final validation still accepts offset 0. The callback returns **0**, writes/commits 64 bytes after stop, and generation becomes 2. No sanitizer scheduling luck is needed: the boundary hook enforces a possible interleaving.

Smallest parent fix: put stop's generation invalidation and reset under the common ring lock and revalidate the saved generation under that same lock immediately before committing. Use an IRQ-safe locking form appropriate to the non-trigger caller; audit the notifier separately from the ALSA trigger. Fix R4 at the same boundary. Do not add a sleeping copy mutex to the atomic trigger path or rely on the notifier possessing a nonexistent substream. The reproduction concerns software publication after shutdown stop; it does not claim that a disabled device consumed the republished samples.

## Contract and call-graph conclusions

The central status-contract correction is valid. `soc-pcm.c:2812` installs the platform copy callback directly. The actual interleaved write/read wrappers (`pcm_lib.c:1997,2219`) supply channel -1 and frame positions/counts, check only negative status, and return 0 for any nonnegative callback result. Their outer loops release the stream lock before transfer and reacquire it to publish the **whole** successful chunk to `appl_ptr`. The ioctl/tinyalsa paths can return a short number of frames accepted across earlier successful chunks; a positive callback result is not such a count.

Negotiated `frame_bits` is the correct storage geometry: mono/stereo 16-bit containers occupy 2/4 bytes per frame; mono/stereo S24-in-32 and S32 containers occupy 4/8. The advertised mask has no packed S24_3 format. Endian and signedness do not alter these widths. Count/position multiplication is bounded before conversion; whole-ring wrap splits are bounded; successful copies preserve every requested frame byte rather than flooring length to 64. The exhaustive suite checks these widths but does not establish physical AFE format programming. Existing shared conversion helpers and other PCM devices are unchanged.

The original ARM64 ALSA MMIO helpers return 0 or EFAULT, not a residual count. Partial target mutation can precede an error. The repair's staged playback user fault leaves DMA bytes unchanged. Capture can partially or fully change the user's destination before EFAULT, a stale-generation error or XRUN, while reporting no accepted chunk; that is accurately disclosed. Hardware producer/consumer accounting is a separate change from accepted application bytes.

For the normal atomic DL1/UL1 machine links (`mt_soc_machine.c:864`), the observed ordering is copy mutex, then PCM stream lock, then memory-control `substream_lock`. Pointer and commit use that ring lock. ALSA trigger-stop/suspend arrives with the stream lock and must not wait for the copy mutex. The changed DL1 reset takes the ring lock, and capture's `RemoveMemifSubStream()` already clears under it. Both IRQs release their ring lock before `snd_pcm_period_elapsed()` and reacquire afterward, so this inspected order avoids a direct ring-lock/stream-lock inversion. The supplied shim makes period_elapsed a no-op and leaves `substreamL` NULL in its scenarios; its passing tests do not validate that real callback path.

Buffer setup (`SetDL1Buffer`, `SetVULBuffer`, `AudDrv_Allocate_DL1_Buffer`) changes ring metadata outside the IRQ ring lock. The new copy mutex serializes it with copy callbacks, while normal ALSA state restrictions exclude reconfiguration of a running stream. Capture's fallback free takes the same mutex; DL1 hw_free is a no-op, and close releases SRAM ownership/clocks through existing paths. ASoC uses its separate `pcm_mutex` for lifecycle operations, not ordinary copies. The implementation therefore does **not** establish that every ring writer uses one lock, nor does the harness execute all actual setup/free/close callbacks. I found no additional proven normal-lifecycle use-after-free from these paths; broad claims about concurrent lifecycle safety should remain bounded to the audited caller/state restrictions. R4/R5 demonstrate why those restrictions must be checked for each caller.

The per-direction mutex prevents overlapping CPU copies. There is no reservation that stops DMA while the staged snapshot/user copy is in progress. Post-copy refresh can detect ordinary observed expiry, but real DMA is not blocked by the spinlock. MMIO snapshot consistency, bus completion and scheduling remain outside the CPU mutual-exclusion proof.

## MMIO and hardware ordering limits

The exact ARM64 `__memcpy_{to,from}io` bodies use raw byte/qword operations and handle byte heads/tails. They impose no transfer-length requirement of 64 bytes. The saved `Afe_Get_Reg()` at `audio/AudDrv_Afe.c:154` reads through an ordinary `uint32 *`, rather than an ordered `readl()` accessor. The pinned ARM64 lock code uses acquire/release instructions; the pinned barrier header separately defines outer-shareable DMA barriers. These observations do not prove a DMA visibility/completion relationship for either the SRAM mapping or coherent DRAM branch. The host shim replaces both mappings with ordinary arrays.

The general Linux DMA documentation says coherent allocation still requires appropriate ordering where the protocol depends on it; the memory-barrier documentation distinguishes CPU synchronization and I/O ordering. See [DMA API guide](https://kernel.org/doc/html/next/core-api/dma-api-howto.html) and [kernel memory barriers](https://www.kernel.org/doc/html/latest/core-api/wrappers/memory-barriers.html). Those references support the review boundary, not a claimed hardware failure or a proposed blind barrier insertion. A later parent should establish the actual mapping/shareability and AFE cursor/data ordering contract and use appropriate accessors/barriers at that boundary. No source-only assertion count or x86 sanitizer run proves it.

Other separate limits: modulo hardware cursors cannot expose arbitrary missed full laps; overfull capture accounting can eventually overflow its inherited signed counter if left running indefinitely; 48 KiB staging/copies under IRQ-disabled locks have unmeasured target allocation/latency costs. mmap, silence callbacks, other PCMs, broad advertised format programming, analog routing and calibration were not qualified. These are not substituted for the five reproduced findings.

## Executed evidence, integrity and resource limits

All 144 supplied files were hashed before review and preserved in `../inputs/`. `input-integrity-after.json` and `input-preservation-result.json` record the final comparison. Python import rewrote one copied bytecode cache during review; it was restored from the unchanged original, and that event is recorded in `snapshot-import-note.json`. No reviewed source/report/patch was edited.

`audit_integrity.py` verified the 62,228-entry before manifest equals the saved physical source manifest, the 62,229-entry overlay differs in exactly the declared three paths, all 73 supplied source pins match their files (original sources also match that physical manifest), and all 504 compiler-input archive entries match their size/hash pins. The parent canonical manifest hash is `c636d9abad7de61e242268372a3b6e3e0cc0ff23f1926274db21f17a6dd81124`. `verify_bundle.py` freshly applied the patch to disposable copies and compared exact postimages/object receipts. These are kernel-source artifacts, not a full SYSTEM/data copy or hash.

The physical base pins remain the reviewed inputs: Image `e9cde06e85e752aec0433ea37fa926c31b4f7a72cd55453762ec6870e5bb5bf1`, config `10b212cabd28aad012582e86c64695ccd450650b4e09ec8da30c21e094f377c2`. I did not recopy the Image or build a complete kernel. Independent object compilation read the same base source/generated headers, and verified the 504 input hashes before and after, redirecting every source/object/dependency write to the owned review fixture.

Local generation replay reproduced `tests/generated.c` and `test-production-bodies.json` byte-for-byte. The generator extracts the final header (only Linux include lines removed), exact copy/pointer/stop bodies, original negative bodies, IRQs, ALSA wrappers and ARM64-selected I/O helper bodies. It does not extract the full ALSA read/write loops, lifecycle callbacks or real memory barriers into the supplied test executable. Assertion count is dominated by per-byte comparisons across a synthetic 256-byte ring, not millions of independent schedules.

Owned builder fixture: `/srv/android/asus-audio-kernel-copy-review-20261106-r1`. Supplied implementation fixture was only an input path, never a write destination. No Ninja, full kernel, active AOSP/out mutation, parent build polling, or competing service build was launched. All jobs ran sequentially.

- Supplied ASan/UBSan replay: **6,838,600 assertions, exit 0**. CPU affinity 0, `cpu.max=100000 100000`, `memory.max=1073741824`; scope memory peak 55,078,912 bytes; executable max RSS 19,920 KiB. Compiler RLIMIT_AS was 1 GiB; ASan used the cgroup cap instead of a virtual-address cap.
- Focused adversarial suite: **34 assertions reproducing R1/R2/R3/R5, exit 0**. Same caps; final compile/run scope peak 57,991,168 bytes, executable max RSS 8,228 KiB. Separate never-open reboot case reproduced R4 with expected UBSan exit 1. All hardware, user-copy and MMIO boundaries remain substitutions.
- Independent ARM64 GCC/Werror builds: both **exit 0**, sequential, same CPU/cgroup limits plus compiler RLIMIT_AS 1 GiB. Scope peak 70,356,992 bytes. New object hashes: DL1 `5950e0a8af5bae9951cc21e64d16b3a14a2890f57fff1be1483a4df5a44e506b`; capture `22b8e6da2daac5b1761aa832062e96c12d2dda0dc0daa088e4115e4ff9792394`. ELF headers identify AArch64 relocatable objects. Recompiled outputs use a new absolute source path; no bit-identical object claim is made.

Exact argv, CWD, SSH options, caps, exits and logs are in `../evidence/replay-command.json`, `compile-command.txt`, `independent-compile.json`, `adversarial-command-r4.txt`, `host-tests.*`, `adversarial-tests.*`, and `never-open-reboot.*`. `../scripts/REPLAY.md` describes the executed workflow. The initial added harness compile lacked a `boundary` field in its shim; the failure is retained as `attempt1-*`, corrected only in the review harness. Earlier successful focused runs remain as `r2-*`/`r3-*`.

## Parent handoff boundary

Parent should fix and retest the five findings in a new owned source revision before considering integration. A corrected source/patch requires fresh postimage/manifests, affected-object checks and focused tests, followed by the parent's separate full-kernel build/link and provenance. Do not pair changed-source claims with the old BMC Image. Existing objects are compilation receipts only.

No codec/amp/config/DT/calibration/routes or older HAL workaround was changed. Speaker-amp discrepancy and main-mic routing remain **UNRESOLVED**, both routes remain unqualified, and the existing r3 kit retains its older BMC kernel. No device, ADB, root, USB, fastboot, mixer, sound/mic, GPIO, IPC, cloud resource/lifecycle, private calibration/key content, or physical action was performed. SSH used only the authorized existing builder and its named key path; no credential contents were read or copied. This review ran as gpt-6.1-sol without subagents.
