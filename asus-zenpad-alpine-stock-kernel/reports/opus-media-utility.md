# Opus 5.5 consultation: Firefox utility audio decoder SIGSYS — 2026-11-08

**Parent runtime correction:** the proposed one-preference RDD fallback was tested and rejected. It returns `NS_ERROR_DOM_MEDIA_DENIED_IN_NON_UTILITY`, “RDD is not allowed to perform audio decoding.” The same pinned `RemoteDecoderManagerChild.cpp:343` independently requires `media.allow-audio-non-utility`, even with utility disabled. That preference was not enabled because it also admits content decoding. The exact policy was removed; profile integrity and normal startup passed. The TLS hypothesis remains plausible, but the compatibility recommendation below is historical and must not be reapplied. See `media-second-result.md` and `evidence/rejected-rdd-policy.json`.

Scope: read-only research. No tablet, SSH, ADB, UI, profile, credential or live-helper access. Inputs: README.md, MEMORY.md, UPSTREAM.md, PROMPT.md, reports/media-utility-question.md, reports/media-first-split.md, evidence/media-first-split.json, evidence/media-utility-loader-tail.txt. Primary public sources were fetched into this spike (paths at the end). **YouTube is not solved and was not retested.**

## Answer in one paragraph

The most likely root cause is **musl's dynamic-TLS barrier fallback running under the utility seccomp filter on a kernel that has no `membarrier` syscall.** It is not a constructor failure, not a missing library and not cubeb/ALSA. The utility process `dlopen`s system FFmpeg61 *after* its sandbox is active. Three libraries in that dependency closure carry a `PT_TLS` segment. musl therefore calls `install_new_tls()`. That function blocks every application signal, SIGSYS included, and calls `membarrier(PRIVATE_EXPEDITED)`. Linux 3.18 returns ENOSYS. musl falls back to sending `tkill(other_tid, SIGSYNCCALL)` to each thread. Firefox's policy traps `tkill` so it can rewrite the call as `tgkill`. That trap delivers SIGSYS, and SIGSYS is blocked at that moment. The kernel's `force_sig_info()` then resets SIGSYS to SIG_DFL and the process dies by SIGSYS. Firefox's own handler never runs, so it logs nothing. RDD is unaffected because it loads the same FFmpeg before its sandbox starts. The smallest credible fix that uses a route Firefox already provides is **`media.utility-process.enabled=false`**. Upstream code then routes audio decoding to the sandboxed RDD process, not to content.

## Proven from primary source (versions pinned)

1. **Firefox ESR 140.12 (`FIREFOX_140_12_0esr_RELEASE`)**
   - `security/sandbox/linux/SandboxFilter.cpp:229-236, 1180-1182`: `tkill` is always `Trap(TKillCompatTrap)`, which re-issues it as `tgkill(getpid(), tid, sig)`. The comment cites "Bug 1376653: musl also needs this". So **every** musl `tkill` in a sandboxed process becomes a SIGSYS trap first.
   - `SandboxFilter.cpp:1163-1165`: `membarrier` is `Allow()`ed ("musl libc will set this up"). A kernel without the syscall therefore returns ENOSYS to musl. The sandbox does not intervene.
   - `SandboxFilter.cpp:2297-2346` (`UtilitySandboxPolicy`): includes explicit allowances "Required by libnuma for FFmpeg" (`get_mempolicy`, `sched_getaffinity(0)`, `set_mempolicy`→ENOSYS). Mozilla itself expects FFmpeg's dependency constructors to run *inside* the utility sandbox.
   - `Sandbox.cpp:137-177`: a genuinely disallowed syscall is reported by `SigSysHandler` as `seccomp sandbox violation: … syscall N`. That only happens if the handler actually runs.
   - `SandboxHooks.cpp:42-79`: Firefox interposes `sigprocmask`/`pthread_sigmask`/`sigaction` to strip SIGSYS from masks (Bug 1176099). musl's internal `__block_app_sigs()`/`__block_all_sigs()` issue raw `rt_sigprocmask` syscalls and bypass this hook.
   - `dom/media/ipc/RDDParent.cpp:143-159`: RDD calls `PDMFactory::Supported()` (constructs a PDMFactory → `InitRddPDMs()` → `FFmpegRuntimeLinker::Init()`, `PDMFactory.cpp:99-111, 302-304, 824-840`) **before** `SetRemoteDataDecoderSandbox()`. `ipc/glue/UtilityProcessChild.cpp:175-190` starts the utility sandbox in `RecvInit`. `InitUtilityPDMs()` (`PDMFactory.cpp:114-145`) links FFmpeg later. The brokered `open` lines in the loader tail independently confirm that FFmpeg61 dependencies were loaded post-sandbox in pid 1887.
   - `dom/media/ipc/RemoteDecoderManagerChild.cpp:690-696`: "Only use RDD for audio decoding if we don't have the utility process". RDD gains `TrackSupport::Audio` exactly when `media.utility-process.enabled` is false. `media.allow-audio-non-utility` defaults to `@IS_IOS@` (false here; `StaticPrefList.yaml:11597`), so this does **not** move audio into content.
2. **musl 1.2.6 (Alpine 3.24 `main/musl` pkgver 1.2.6-r3; none of its patches touch these files)**
   - `ldso/dynlink.c:2208-2210`: `dlopen` calls `install_new_tls()` whenever the new load raised `tls_cnt`.
   - `dynlink.c:1647-1695`: `install_new_tls()` calls `__block_app_sigs()` and then `__membarrier(MEMBARRIER_CMD_PRIVATE_EXPEDITED, 0)`. It runs after mapping/relocation and **before** `do_init_fini` (constructors).
   - `src/linux/membarrier.c`: if the syscall fails, the fallback blocks app signals again, installs a SIGSYNCCALL handler, and issues `__syscall(SYS_tkill, td->tid, SIGSYNCCALL)` for every other thread.
   - `src/signal/block.c`: `app_mask` = `0xfffffffc7fffffff`, which covers signals 1–31 and so includes SIGSYS (31).
   - `raise()` and `pthread_kill()` follow the same "block then tkill" pattern. That makes *any* musl raise/abort/pthread_kill in a Firefox sandbox die by SIGSYS too. This is relevant to the semantics below.
3. **Linux v3.18**: `kernel/seccomp.c:539-550` sends seccomp TRAP via `force_sig_info(SIGSYS)`. `kernel/signal.c:1211-1234`: if the signal is blocked or ignored, the kernel sets the handler to **SIG_DFL** and unblocks it. The result is death by SIGSYS with no user handler.
4. **Alpine 3.24 aarch64 packages (offline ELF scan, `artifacts/media-utility-opus-tools/pt_tls.py`)**: libgomp.so.1 (15.2.0-r5; pulled by libsoxr ← libswresample.so.5), libnuma.so.1 (numactl 2.0.19-r0; pulled by libx265.so.215) and libjxl_cms.so.0.11 (libjxl 0.11.2-r1) all have `PT_TLS`. All three appear in the loader tail's dependency search, and a utility process does not normally have them loaded beforehand. libavcodec61/libavutil59/libswresample5 (ffmpeg7 7.1.5-r0) themselves have no TLS.
5. **Alpine firefox-esr 140.12.0-r0 APKBUILD**: `--disable-crashreporter`, patch set includes only `sandbox-sched_setscheduler.patch` for the sandbox. Nothing addresses this path. No Breakpad handler sits in the signal path.
6. **Mozilla Bug 1657849** (open, last touched 2026-11-03) documents this class of failure for a different musl call site: "the seccomp 'trap' mechanism is broken in that if sigsys is blocked then the process crashes instead of handling the signal". Alpine works around that sched_setscheduler instance only.

## Inferred (fits all evidence, not yet observed on the tablet)

- **Kernel lacks membarrier.** Upstream `membarrier` arrived in Linux 4.3 and `PRIVATE_EXPEDITED` in 4.14. The fixed vendor 3.18.35 almost certainly has neither (not checked; `/proc/config.gz` absent). On ≥4.14 kernels musl takes no fallback, which explains why ordinary Alpine desktops do not hit this.
- **The fatal sequence in pid 1887** would be: the last dependency open (`libxcb-dri3`) completes, then `install_new_tls` runs (no log line), then `membarrier` returns ENOSYS, then `tkill(other_tid, 34)` is trapped while SIGSYS is blocked, then the process is killed by SIGSYS and the broker reports `EOF from pid 1887`. This matches four facts:
  - the tail ends immediately after dependency loading;
  - there are no `PlatformDecoderModule`/`FFmpeg` link-result lines;
  - the signal trace ends with a `tkill` trap followed by "killed by SIGSYS";
  - there is no `seccomp sandbox violation` line.
- **Muting cannot help**, because the crash happens at PDM initialisation, before any sample is decoded. **Any** utility-decoded audio (AAC, Opus, Vorbis, MP3) should fail the same way, because `InitUtilityPDMs` links FFmpeg regardless of codec. YouTube audio is therefore expected to fail for this same reason, but that has not been tested.

## tkill trap semantics: symptom vs. root cause

- The `openat` traps are the normal broker mechanism: the trap runs, the broker answers, and the process continues.
- In this Firefox build, a `tkill` trap is *also* normally benign: the trap runs and is rewritten to `tgkill`. It is fatal only when SIGSYS is blocked at the moment of the trap. musl blocks it in exactly three paths: `raise`/`abort`, `pthread_kill`/`pthread_cancel`, and the membarrier fallback.
- So "tkill trap → killed by SIGSYS" **is a signal-mask artefact. It is not a policy denial.** The question that matters is *who* called tkill:
  - **Membarrier fallback (predicted):** `tkill(tid ≠ caller, 34 = SIGSYNCCALL)`, immediately preceded by `membarrier(…PRIVATE_EXPEDITED…) = -1 ENOSYS`.
  - **abort/assert or C++ terminate:** `tkill(caller_tid, 6 = SIGABRT)`. The real cause would then be a library or constructor failure that printed to stderr first (`Assertion failed: …`, libstdc++ `terminate called…`, `hwy` abort text).
  - **pthread_cancel:** `tkill(other_tid, 33)`. Unlikely in this path.
- The three questions distinguish as follows:
  - **Missing library:** would be a dlopen error and an FFmpeg `LinkStatus` log line, not a signal. This is ruled out: the deps resolve, and the ENOENT/EACCES lines are the normal search order.
  - **Constructor failure:** constructors run *after* `install_new_tls`, so with this mechanism they never run.
  - **Sandbox policy denial:** would show `seccomp sandbox violation`. It is absent.
  - **cubeb/ALSA output:** is not in the utility process at all. The utility process only decodes. Output starts later in the content/parent audio path, and only after decoded samples exist. It is a separate, later gate. The direct `hw:0,0` PCM success does not bear on this crash, and this crash does not bear on speaker output.

## Recommended single next step (compatibility fix using an existing route)

Set **`media.utility-process.enabled = false`** as a *default* pref through an OS-level, removable mechanism that does not write the owner's profile. For example, an enterprise `policies.json` under the Firefox ESR `distribution/` directory with `"Preferences": {"media.utility-process.enabled": {"Value": false, "Status": "default"}}`. Verify that ESR140's policy pref allow-list accepts the `media.` prefix before relying on it. Back up and restore by deleting the file. Restart the same desktop/browser session and rerun the existing AV-muted fixture once.

- Why: audio then uses the RDD process, which already links FFmpeg61 pre-sandbox (proven ordering), so no post-sandbox TLS install occurs. The sandbox stays on. Content still does not decode audio. There is no LD_PRELOAD, no kernel change and no package change.
- Isolation cost, which the owner/parent must accept or reject: audio and video decoders share the RDD process. RDD's seccomp policy is somewhat broader than the utility policy (GPU ioctls, sched_*). This is less compartmentalisation than upstream's default. It is still not a sandbox disable and not content-process decoding.
- **Positive gate:**
  - the AV-muted fixture advances `currentTime` ≥ 9 s with `totalFrames > 0`, `error=null`, and no `…CRASHED_UTILITY_ERR`/`…CRASHED_RDD_OR_GPU_ERR`;
  - no new utility-process audio decoder is spawned;
  - the profile quick_check stays ok.
  - Only after that, run an unmuted repeat at the existing quiet level. That separately tests cubeb→ALSA output, which is also a separate audibility question.
- **Negative gate:**
  - If RDD now crashes on AAC, the load-timing inference is wrong. Restore (delete the policy file) and take the diagnostic below.
  - If muted plays but unmuted fails or stays silent, the decoder problem is solved and the remaining problem is cubeb/ALSA output.

## If the parent wants proof before any configuration change: the smallest missing observation

1. **Zero-mutation check against existing evidence.** Confirm that the ignored full private log has **no** `seccomp sandbox violation` line for pid 1887, and no `Assertion failed`/`terminate called` stderr line before `EOF from pid 1887`. The prediction is that both are absent.
2. **Read-only kernel check.** `grep -cw sys_membarrier /proc/kallsyms`. The prediction is 0.
3. **One bounded trace, same fixture, no setting changes.** Use the method already used for the signal trace, narrowed to `-e trace=membarrier,tkill,tgkill -e signal=SIGSYS` on the utility child.
   - Positive (mechanism confirmed): `membarrier(MEMBARRIER_CMD_PRIVATE_EXPEDITED, 0) = -1 ENOSYS` followed directly by `tkill(<tid of another thread>, SIGRT_2)` → `SIGSYS {si_code=SYS_SECCOMP, si_syscall=__NR_tkill}` → killed.
   - Negative: `tkill(<own tid>, SIGABRT)`. Then capture only the utility's stderr lines immediately before it to identify the aborting library.
   - Raw output goes to `private/live/`; only a sanitized summary goes to `evidence/`.

## Not recommended

- Allowing raw `tkill` in BPF: the filter cannot bound the target tid to this process.
- Making the policy return success for `membarrier`: this silently drops the memory barrier musl needs for safe dynamic-TLS publication.
- Global sandbox disable, `media.allow-audio-non-utility`, LD_PRELOAD shims, rebuilding musl or Firefox now, and codec/package swaps.

The proper upstream-quality fix would be a small Firefox patch that links FFmpeg (`PDMFactory::Supported()`/`FFmpegRuntimeLinker::Init()`) in the Linux generic utility process before `SetUtilitySandbox()`, mirroring RDD. Reporting it against Bug 1657849's failure class is also reasonable. Either one requires a full Firefox build and is outside this bounded step.

## Source files retrieved (public, inside this spike)

- `sources/media-utility-opus/`: Firefox ESR140.12 `SandboxFilter.cpp`, `Sandbox.cpp`, `SandboxHooks.cpp`, `SandboxFilterUtil.h`, `RDDParent.cpp`, `RDDProcessImpl.cpp`, `RDDProcessHost.cpp`, `RDDProcessManager.cpp`, `UtilityProcessChild.cpp`, `UtilityProcessImpl.cpp`, `UtilityAudioDecoderParent.cpp`, `PDMFactory.cpp`, `RemoteDecoderManagerChild.cpp`, `RemoteDecoderModule.cpp`, `RemoteMediaDataDecoder.cpp`, `FFmpegRuntimeLinker.cpp`, `FFmpegLibWrapper.cpp` and `StaticPrefList.yaml`; musl v1.2.6 `dynlink.c`, `membarrier.c`, `block.c`, `raise.c`, `abort.c`, `assert.c`, `pthread_kill.c` and `pthread_create.c`; Linux v3.18 `seccomp.c` and `signal.c`; Alpine 3.24 musl and firefox-esr APKBUILDs; BMO 1657849/1883915 JSON.
- `downloads/media-utility-opus-apks/`: Alpine v3.24 aarch64 APKINDEX and candidate library APKs (extracted under `x/`).
- `artifacts/media-utility-opus-tools/pt_tls.py`: read-only ELF64 PT_TLS/DT_NEEDED scanner.

No live system, browser profile, helper script or existing report was modified.
