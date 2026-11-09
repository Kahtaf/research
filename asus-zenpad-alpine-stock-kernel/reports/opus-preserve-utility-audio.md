# Opus 5.5 review: keep the utility audio sandbox and remove post-sandbox TLS — 2026-11-08

Scope: source and offline review only. No tablet SSH, ADB or UI was used. No private profile, credential or capture was read. No live or source helper was edited, nothing was built and nothing was delegated. I read README.md, MEMORY.md, UPSTREAM.md, PROMPT.md, the parent AGENTS.md, reports/media-preserve-utility-question.md, media-second-result.md, opus-media-utility.md, evidence/rejected-rdd-policy.json and evidence/media-utility-loader-tail.txt. New public sources are listed at the end.

**Verdict: the browser-private FFmpeg 7.1.5 bundle is credible.** It needs:

- no Firefox rebuild;
- no preference change;
- no loader trick beyond Firefox's own library-search rules.

It is also a discriminating test of the TLS hypothesis. The Firefox preload patch is therefore the fallback, not the next step.

## 1. Correction: the guard that the previous Opus report missed

The earlier report (`opus-media-utility.md`) read only `RemoteDecoderManagerChild::GetTrackSupport` (`RemoteDecoderManagerChild.cpp:690-696`). There, RDD gains `TrackSupport::Audio` when `media.utility-process.enabled=false`. It then claimed that `media.allow-audio-non-utility` "does not move audio into content", and treated that preference as irrelevant to the RDD route.

That was wrong. Decoder creation itself, in `RemoteDecoderManagerChild.cpp:335-353`, takes a different path:

- **Utility enabled:** if `media.utility-process.enabled` is true and the location is a utility location, the utility process launches.
- **Otherwise:** for any other location, including RDD, the code requires `media.allow-audio-non-utility`. If that preference is false, it rejects with `NS_ERROR_DOM_MEDIA_DENIED_IN_NON_UTILITY` and the message "%s is not allowed to perform audio decoding".

So with utility disabled and the default `allow-audio-non-utility=false` (`StaticPrefList.yaml:11597`, `@IS_IOS@`), RDD audio is rejected unconditionally. That is exactly the physical result. The same preference also gates `InitContentPDMs` (`PDMFactory.cpp`, `if (StaticPrefs::media_allow_audio_non_utility())`), which links FFVPX and FFmpeg into the **content** process. The RDD fallback could therefore only work by also enabling content-process decoding. It was never viable under this project's constraints and must stay rejected.

**Proven** (pinned source plus the physical NS_ERROR text). The earlier "smallest fix" claim is withdrawn.

## 2. What the system FFmpeg actually serves (proven, ESR140.12 source)

- **Audio codecs:** `FFmpegAudioDecoder::GetCodecId` returns AAC (`audio/mp4a-latm`) unconditionally. MP3, FLAC, Vorbis, Opus and all PCM/WAV mappings are inside `#ifdef FFVPX_VERSION`, so they belong only to Firefox's bundled ffvpx. In the system-FFmpeg build, **AAC is the only audio codec it is ever asked for.**
- **Video codecs:** `FFmpegVideoDecoder::GetCodecId` maps H264, HEVC (gated by `media.hevc.enabled`), VP6F, VP8 and VP9. AV1 is mapped only with `FFMPEG_AV1_DECODE`.
- **ffvpx has no AAC and no H.264.** Its pinned `media/ffvpx/libavcodec/codec_list.c` contains VP8, VP9, FLAC, MP3, AV1/libdav1d, libvorbis, libopus, PCM, and AAC/H264 only as Android `mediacodec`.
- **Decoder order:** ffvpx is tried before system FFmpeg in RDD (`PDMFactory.cpp:572-576`) and in the generic utility process (`:601-608`). VP8, VP9, AV1, Opus, Vorbis, FLAC and MP3 are therefore already answered first by ffvpx. Bundle contents beyond AAC and H.264 only preserve parity.
- **Rejected alternative: `media.utility-ffmpeg.enabled=false`.** It would keep the utility sandbox and avoid loading system FFmpeg there, but it removes AAC entirely. It violates the AAC requirement and is not recommended.
- **No VA-API in the utility process.** `FFmpegDecoderModule<V>::Init` returns early on GTK unless the process is RDD.
- **Required symbols are always exported.** `FFmpegLibWrapper::Link()` resolves every symbol from the libavcodec handle (`mAVUtilLib = mAVCodecLib`). All mandatory v61 symbols exist regardless of configuration, including the encoder lookup functions (`avcodec_find_encoder*`, `avcodec_send_frame`, `avcodec_receive_packet`). libswresample is never used.
- **Version and dlopen behaviour:** the version gate is `avcodec_version()` major 61 with micro ≥100. Firefox dlopens bare sonames in the order `libavcodec.so.62`, then `.61`, and so on, with `PR_LD_NOW|PR_LD_LOCAL`.

## 3. Why the current closure installs TLS, and why a minimal build would not

**Proven (offline ELF scan of the Alpine 3.24 aarch64 packages).**

- **Alpine libavcodec.so.61.19.101 NEEDED list:** swresample, avutil, vpx, webpmux, dav1d, aom, jxl, jxl_threads, mp3lame, opus, rav1e, SvtAv1Enc, theora, vorbis, webp, x264, x265, xvidcore, z and va.
- **Alpine libavutil.so.59.39.100 NEEDED list:** va-drm, va, va-x11, vdpau, X11, drm and crypto.
- **TLS sources:** the PT_TLS segments come from libgomp (via soxr ← swresample), libnuma (via x265) and libjxl_cms. Core avcodec, avutil and swresample have none; libvpx, libdav1d, libva and libxcb have none either.
- **Upstream FFmpeg 7.1.5 source:** no `_Thread_local`, `__thread` or `thread_local` anywhere in libavutil, libavcodec or compat. The only `__attribute__((constructor))` is in `libavutil/riscv`.
- **Configure dependencies:**
  - `avcodec_deps="avutil"`; libswresample is not an avcodec dependency.
  - `opus_decoder_deps="swresample"`, so the native Opus decoder must be left out. This is harmless, because Firefox never asks system FFmpeg for Opus.
  - `--disable-autodetect` also drops `THREADS_LIST`, so `--enable-pthreads` must be passed explicitly.
- **musl 1.2.6** `dlopen` calls `install_new_tls()` only when `tls_cnt != orig_tls_cnt` (`dynlink.c:2208-2210`). With a closure of {libavcodec, libavutil, libc}, all TLS-free, the block-signals → membarrier ENOSYS → trapped `tkill` path is never entered.

**Inferred:**

- **ffvpx already loads safely.** ffvpx (`libmozavutil`/`libmozavcodec`, linked first in `InitUtilityPDMs`) is already loaded after the sandbox starts without killing the process: pid 1887 lived on into the system-FFmpeg dependency search. The bundle therefore leaves no other new TLS load on this path. That is inferred from the source order plus survival; the Firefox APK was not ELF-scanned.

## 4. Browser-local selection already exists (proven)

- **Children get the Firefox directory first.** `GeckoChildProcessHost.cpp:1213-1228` prepends the GRE directory to `LD_LIBRARY_PATH` for every Linux child.
- **The parent does too.** Alpine links Firefox with `-Wl,-rpath,$_mozappdir` (`/usr/lib/firefox-esr`, APKBUILD). musl searches `LD_LIBRARY_PATH`, then the rpath chain, then `/lib:/usr/local/lib:/usr/lib` (`dynlink.c` `load_library`).
- **The loader tail shows exactly that order for pid 1887:** `/usr/lib/firefox-esr` twice (ENOENT), then `/lib` (ENOENT), then `/usr/local/lib` (broker-denied, EACCES), then `/usr/lib`. GRE-directory lookups returned ENOENT, not a denial, so the broker already permits them.
- **The broker already allows it.** `SandboxBrokerPolicyFactory::GetUtilityProcessPolicy` adds the GRE directory as an rdonly tree, plus `/usr/lib` and the `LD_LIBRARY_PATH` directories.
- **Mechanism:** place exactly `libavcodec.so.61` and `libavutil.so.59` as regular files in `/usr/lib/firefox-esr/`. Firefox's own rpath, its own child `LD_LIBRARY_PATH` and its own broker rule then select them in parent, RDD and utility alike.
- **What this does not involve:**
  - no environment change, wrapper, preload, pref or profile write;
  - no change to `/usr/lib/libav*`;
  - no change to the seccomp filter, kernel or membarrier handling.
- **Rollback:** delete the two files plus a small ownership manifest. One side effect: if Alpine later ships `libavcodec.so.62`, Firefox picks it from `/usr/lib` first and the bundle goes inert (safe failure).
- **Not recommended:** an `LD_LIBRARY_PATH` variant in the desktop helper. It is also source-supported, but it leaks into processes Firefox spawns and depends on every launch path.

## 5. Exact build, ABI, dependency and ELF gates (do not run yet)

**Builder:** the existing local Docker aarch64 engine with a pinned `alpine:3.24` image (record its digest). Install `build-base` and `pkgconf` only. No new VM or cloud resource is needed.

**Source:**

- Use `https://ffmpeg.org/releases/ffmpeg-7.1.5.tar.xz`. The retained copy has SHA512 `c0649ef9…d965`, equal to Alpine ffmpeg7 7.1.5-r0's pin, and SHA256 `de668509caf9e35e3cd162473441fdb29538c6d96ed080292b3cf9e6fc5d558f`.
- Apply **no** patches. Alpine's handbrake patch inserts `AV_FRAME_DATA_DOVI_RPU_BUFFER_T35` mid-enum, shifting later side-data values away from the upstream headers Firefox compiles against. The other three patches touch only avformat, avdevice and v4l2.

**Configure** (LGPL-2.1+, decoder-only, no external libraries):

```
./configure --prefix=/opt/asus-ffmpeg61 --enable-shared --disable-static --enable-pic \
  --disable-autodetect --enable-pthreads --disable-programs --disable-doc \
  --disable-avdevice --disable-avformat --disable-avfilter --disable-swresample \
  --disable-swscale --disable-postproc --disable-network --disable-iconv \
  --disable-everything \
  --enable-decoder=aac,h264,hevc,vp8,vp9,vp6f \
  --enable-parser=aac,h264,hevc,vp8,vp9 \
  --extra-ldflags='-Wl,--as-needed -Wl,-z,now -Wl,-z,relro'
make -j10
```

`--disable-everything` still auto-selects the internal dependencies (for example `vp9_superframe_split_bsf` and `null_bsf`). This is a parity-minimal build, not indiscriminate removal:

- **Kept:** every codec ID Firefox's system-FFmpeg PDM maps, using the same native AAC and H.264 decoder code Alpine's library uses. Alpine's x264 is an encoder.
- **Dropped:**
  - encoders: WebCodecs/MediaRecorder encoding via FFmpeg on Linux would lose these, which is acceptable for decoding scope;
  - hwaccels and VA-API: there is no DRM device on this tablet;
  - external libraries;
  - native Opus: never requested from system FFmpeg;
  - AV1: ffvpx and dav1d answer it first.

**Static gates.** All must pass on the two output files:

1. **ELF closure.** `pt_tls.py` on both files must show no PT_TLS. The NEEDED lists must be exactly:
   - libavcodec: {`libavutil.so.59`, `libc.musl-aarch64.so.1`};
   - libavutil: {`libc.musl-aarch64.so.1`}.

   SONAMEs must be `libavcodec.so.61` and `libavutil.so.59`. There must be no TEXTREL, ELF class 64 with machine AArch64, and no DT_RPATH or DT_RUNPATH. Any extra NEEDED entry is a failure, not something to waive.
2. **ABI.** Every mandatory v61 `AV_FUNC` symbol in `FFmpegLibWrapper.cpp`, plus `avcodec_version`, must be present in the private dynsym. Version nodes must be `LIBAVCODEC_61` and `LIBAVUTIL_59`, matching the system library.
3. **Runtime harness in the same container.** A small C program dlopens bare `libavcodec.so.61` with `LD_LIBRARY_PATH` set to the output directory and `RTLD_NOW|RTLD_LOCAL`. It must find:
   - `avcodec_version()==0x3D1365` (61.19.101);
   - non-null decoders for AAC, H264, HEVC, VP8, VP9 and VP6F;
   - `/proc/self/maps` containing no system libav* or any library beyond the two files.

   It then decodes regenerated synthetic fixture elementary streams with the private libraries only. Those streams are ADTS AAC 48 kHz from the 440 Hz tone and Annex-B H.264 640×360 from testsrc2, extracted by the container's own `ffmpeg`. Sample and frame counts must equal those from the system ffmpeg.

**Build cost:** a few minutes at most on 10 CPUs, with negligible memory and disk use. This is an estimate.

## 6. One on-tablet positive/negative gate (after explicit approval)

**Setup:**

- Copy the two gated files plus a manifest of their SHA256s into `/usr/lib/firefox-esr/`, as root-owned 0644.
- Back up nothing else; no pref or profile change.
- Do a **fresh** Firefox parent start through the normal desktop path, not a reload: retries were already exhausted last time.
- Enable the existing diagnostic sandbox and PDM logging for that one start only.
- Load the existing muted H.264+AAC 48 kHz fixture once.

**Positive (all required):**

- `currentTime` reaches at least 9 s with `error==null` and no `…CRASHED_UTILITY_ERR` or `…CRASHED_RDD_OR_GPU_ERR`.
- Total video frames are at least about 230, matching the 240-frame baseline.
- The decoder-debug info shows the audio decoder remote in the **Utility** process, not RDD or content.
- The utility pid stays alive after playback.
- The sandbox log shows that pid opening `/usr/lib/firefox-esr/libavcodec.so.61` and `libavutil.so.59`. It shows no opens of `/usr/lib/libavcodec.so.61`, x265, soxr, gomp, numa or jxl_cms.
- Profile quick_check stays ok.

This confirms the TLS mechanism by intervention. Unmuted audibility through cubeb/ALSA is a separate, later gate.

**Negative or rollback:**

- **Log shows the system `/usr/lib/libavcodec.so.61`:** selection failed. This is not a hypothesis result. Remove and stop.
- **Private files confirmed loaded and the utility still dies by SIGSYS:** the TLS hypothesis is falsified for this path. Remove the files. The next evidence is the previously specified fresh-start `membarrier,tkill,tgkill` trace, not another variant.

In every case, finish by deleting the two files and the manifest, then closing Firefox normally. Run profile quick_check, restore the normal dashboard, and confirm both speaker gates are off.

## 7. Fallback only if the bundle fails: the proper Firefox patch

**The patch** is about 15 lines. In `UtilityProcessChild::RecvInit`, under `XP_LINUX`, before `SetUtilitySandbox(fd, mSandbox)`, and only when `GetCurrentSandboxingKind()==GENERIC_UTILITY`, call `PDMFactory::Supported()` (or `FFVPXRuntimeLinker::Init()` plus `FFmpegRuntimeLinker::Init()`). This mirrors `RDDParent.cpp:143-159`.

**Why it is safe to link early:** `PDMInitializer::InitPDMs` is once-per-process, and the linkers cache `sLinkStatus`. Later `InitUtilityPDMs` calls therefore reuse the already-loaded libraries.

**It is upstreamable** against Bug 1657849's failure class.

**Cost (inferred):**

- It needs a full Alpine `firefox-esr` 140.12 APKBUILD rebuild plus this patch: clang/lld, rust and cbindgen, nodejs, and about 15–25 GB of disk.
- The default aarch64 recipe does PGO instrumented build, then xvfb profiling, then a thin-LTO build. libxul's LTO link is unlikely to fit in an 8 GiB VM.
- Realistically it would use the APKBUILD's non-PGO "regular" path with LTO off. Estimate roughly 1.5–3 hours on 10 CPUs if the memory holds, with OOM risk at link.
- The result is a replacement browser package that must be re-carried on every ESR update.

That is why it is second.

## Proven vs inferred summary

**Proven:**

- the missed guard and its content-PDM coupling;
- AAC is the only system-FFmpeg audio codec;
- ffvpx lacks AAC and H.264;
- the decoder order;
- the symbol requirements;
- the musl TLS install condition and search order;
- the child `LD_LIBRARY_PATH` and the build rpath;
- the broker GRE/`/usr/lib` trees;
- the observed search order;
- Alpine closure TLS sources;
- no TLS keywords in FFmpeg 7.1.5;
- the tarball identity;
- the mid-enum insertion by Alpine's patch.

**Inferred, not observed:**

- the kernel lacks membarrier;
- the fatal call is musl's barrier fallback;
- ffvpx's load is TLS-free;
- the build time and the Firefox build cost;
- that the dropped encoder and VA-API capabilities matter nowhere on this tablet.

## Next step

**ONE next step:** in the existing local Docker aarch64 builder, build the exact decoder-only FFmpeg 7.1.5 configuration in §5 and run its three static and runtime gates. Do not touch the tablet. Install on the tablet only after those gates pass and the owner approves the single §6 gate.

## Sources added in this review

`sources/media-preserve-utility/`:

- ESR140.12 `FFVPXRuntimeLinker.cpp`, `FFmpegDecoderModule.{h,cpp}`, `FFmpegAudioDecoder.cpp`, `FFmpegVideoDecoder.cpp`, `FFmpegDataDecoder.cpp`, `SandboxBrokerPolicyFactory.cpp`, `GeckoChildProcessHost.cpp` and `media/ffvpx/libavcodec/codec_list.c`;
- Alpine 3.24-stable ffmpeg7 APKBUILD and its four patches.

`downloads/ffmpeg-7.1.5-src/`:

- the upstream tarball, its signature and an extracted tree. It is untrusted input, read-only, and nothing in it was executed.
