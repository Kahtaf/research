# Opus 5.5 consultation: stock-kernel ALSA mmap oops from Firefox cubeb

2026-11-08. Read-only work from source and saved evidence only. No tablet, ADB, SSH or USB access; no live commands, builds, helper/config edits, SD-root or package changes. Public sources fetched for this report are in `sources/alsa-mmap-opus/`; `SOURCES.txt` there lists their URLs, pins and SHA-256 sums. Only the last 250 lines of `private/live/access-return-last_kmsg.txt` were read, and only for the call trace and panic tail; no identifiers from that log are reproduced here.

## Answer in one paragraph

No ALSA-config-only route exists. Firefox's cubeb ALSA backend already asks for `RW_INTERLEAVED`, but it sends FLOAT_LE samples. The default `plug:hw` chain therefore inserts a format converter, and alsa-lib converters always write to their slave through mmap areas. `plug` picks the slave access with `set_access_first`, so it selects `MMAP_INTERLEAVED` because the hardware falsely advertises MMAP. `mmap_emul` does **not** help: it tries the slave in MMAP mode first, the kernel accepts, and emulation never engages. The hw plugin has no option to turn off mmap. The smallest proven route is therefore a userspace PCM bridge that does its own conversion and calls `snd_pcm_writei` on the exact native hardware format.

That bridge is **PulseAudio 17 `module-alsa-sink device=hw:0,0 mmap=0 tsched=0` at s16le/48000/2**, with no mixer control. Pair it with a one-file ALSA guard that makes `default` a plain `hw` PCM, so any float client that reaches ALSA fails at `set_format` instead of mapping the buffer. Firefox then uses its first-choice `pulse-rust` backend, so the sandbox and prefs are unchanged.

## 1. Kernel mechanism (proven from source plus retained oops)

Paths are relative to `../2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/`.

* **Vendor `.page` callback.** `sound/soc/mediatek/mt_soc_audio_8163/mt_soc_pcm_dl1.c:616-621` declares `static void *dummy_page[2];` and returns `virt_to_page(dummy_page[substream->stream])`. Nothing in the file, or in any of the 22 sibling MT8163 PCM files using the same pattern, ever assigns `dummy_page`, so it is NULL. `virt_to_page(NULL)` is not NULL: it is a computed `struct page *` (`arch/arm64/include/asm/memory.h:72,147`). Lines 624-636 register this as `.page`; ASoC copies it straight into the PCM ops (`sound/soc/soc-pcm.c:2546`).
* **The advertised MMAP is false.** Lines 147-148 set `SNDRV_PCM_INFO_MMAP | SNDRV_PCM_INFO_MMAP_VALID`. The kernel then adds `MMAP_INTERLEAVED` to the access mask next to `RW_INTERLEAVED` (`sound/core/pcm_native.c:2071-2083`). The working RW path is the vendor `.copy` callback (`mt_soc_pcm_dl1.c:469-606`), which is what tinyalsa/Android and our `aplay` tests use.
* **Generic code is forced onto the bad path.** `snd_pcm_lib_default_mmap` (`pcm_native.c:3322-3349`) uses `dma_mmap_coherent` only `if (!substream->ops->page && ...)`. Because `.page` is set, it installs the fault handler instead. `snd_pcm_mmap_data_fault` (3274-3299) rejects only a NULL page, then calls `get_page(page)`. Without a `.page` callback, `snd_pcm_default_page_ops` would have mapped the real `dma_area`. The vendor override replaces that with a bogus page.
* **The retained oops matches instruction for instruction.** The dumped code at `snd_pcm_mmap_data_fault` reads: `blr x2` (ops->page) → `mov x20,x0` → `cbz x0` (NULL check passes) → **`ldr x0,[x20]` at +0x68**, the faulting PC. That load is `get_page` reading `page->flags`, with `x20 = ffffffbee0000000`. The same function encodes the vmemmap base as an immediate, `movz x20,#0xffbe,lsl#32; movk x20,#0xffff,lsl#48` = `ffffffbe00000000`, which is consistent with a 56-byte `struct page` and a 7 GiB VMEMMAP_SIZE. The bad pointer is therefore vmemmap entry `0x4000000`, far outside RAM, in an unpopulated memmap slot.
* **The trigger was a userspace write.** The call trace runs `do_page_fault → handle_mm_fault → do_shared_fault → (vm_ops->fault)` with ESR `0x92000047`: a data abort from EL0, write, level-3 translation fault on the shared PCM data mapping. The cubeb thread wrote into an mmapped PCM data buffer.
* **Residual detail, not affecting the conclusion.** The generic `__pa(0)` formula with `memstart_addr=0x40000000` predicts entry `0x4040000`, not `0x4000000`. The difference is exactly `memstart_addr>>12`, which is unreconciled. Either way, `.page` returned a non-NULL pointer to an unbacked vmemmap slot, and NULL `dummy_page` is the only input visible in source.

**Consequence:** on this kernel, any touch of an mmapped data buffer on these vendor PCMs oopses. Status/control mmaps (`0x80000000`/`0x81000000` offsets) are separate kernel pages and are safe; `aplay` already used them. The only safe data path is RW (`.copy`).

## 2. Firefox: exact backend and access path (pinned source/build)

* The Alpine 3.24 `firefox-esr` 140.12.0-r0 mozconfig (`sources/alsa-mmap-opus/alpine/firefox-esr-mozconfig`) has both `--enable-alsa` and `--enable-pulseaudio`. In `media/libcubeb/src/moz.build` those become `USE_ALSA` (`cubeb_alsa.c`) and `USE_PULSE_RUST`.
* `cubeb.c:216-240` tries backends in order: `pulse_rust_init`, then (no JACK or sndio built) `alsa_init`. PulseAudio is absent, so pulse-rust fails and **ALSA is selected**.
* `cubeb_alsa.c` opens PCM `"default"` (`CUBEB_ALSA_PCM_NAME`, :76) in non-blocking mode. It calls `snd_pcm_set_params(..., SND_PCM_ACCESS_RW_INTERLEAVED, ...)` (:1071) and writes with `snd_pcm_writei` (:469). Gecko sends `CUBEB_SAMPLE_FLOAT32NE`, which maps to `SND_PCM_FORMAT_FLOAT_LE` (:1012-1013, :1198). The rendering thread registers as **"cubeb rendering thread"** (:586); the kernel `comm` truncates that to `cubeb r~ thread`, matching the oops.
* `media.cubeb.sandbox` is `true` on Linux (StaticPrefList, :11019-11026), so cubeb runs remoted through AudioIPC. Which process hosted the thread is not shown in the log; check it during the test.
* **Why the experiment 49 muted pass never exercised output:** `dom/media/mediasink/AudioSinkWrapper.cpp:84-198` treats volume 0 as muted. A muted sink uses the system clock and shuts down or never creates the AudioStream, so the 9.86 s muted H264+AAC pass opened no cubeb stream. The kernel crash is the first real output attempt. **Any output qualification must be unmuted** (volume > 0), with the amps keeping it physically silent.

## 3. Why the default chain mmaps the hardware (alsa-lib 1.2.15.3)

* `src/conf/pcm/default.conf`: with no card-specific definition, `default` = `type empty` → `type plug` → `type hw card 0` (device 0 = DL1, per the existing inventory `00-00 MultiMedia1_PLayback`).
* `pcm_plug.c:1047-1066`: if the client's format, rate and channels already match the slave, and the slave accepts the client access, no plugin is inserted and `hw` receives RW. That is why `aplay -f S16_LE -r48000 -c2` on `default` works. FLOAT_LE does not match: the hardware formats are S16/U16/S24/U24/S32/U32 only (`mt_soc_pcm_common.h:142-154`). So plug runs `set_access_first(slave)` (:1062). `check_access_change` (:770-786) keeps the mask unchanged whenever the slave offers any MMAP access. The first access in enum order is `MMAP_INTERLEAVED`, so the slave hw is configured for MMAP.
* `snd_pcm_plug_change_mmap` (:630-657) would insert `mmap_emul` only when the slave access is RW, which never happens here.
* The converter plugins (`lfloat`, `linear`, `rate`, `route`) all go through `pcm_plugin.c:233-265`: `snd_pcm_mmap_begin(slave)` → write → `snd_pcm_mmap_commit(slave)`. `pcm_params.c:2455-2459` calls `snd_pcm_mmap()` for MMAP access. `pcm_hw.c:586-604` returns `SND_PCM_AREA_MMAP` with the device fd and offset, so the data area is mmapped from `/dev/snd/pcmC0D0p`, and the converter's first write takes the fault above.

## 4. Does `mmap_emul` bypass a hardware PCM that falsely advertises MMAP? No.

`pcm_mmap_emul.c`, `snd_pcm_mmap_emul_hw_refine` and `snd_pcm_mmap_emul_hw_params`:

* `hw_refine` first refines the slave with the original mask. It falls back to RW only `if (err < 0)`, and returns early when the result contains any MMAP access.
* `hw_params` calls `_snd_pcm_hw_params_internal(slave, params)` first. If that succeeds, it sets `map->mmap_emul = 0` and passes through. Emulation (`mmap_emul = 1`, writing to the slave with `snd_pcm_write_mmap` → `writei`) happens only when the slave **rejects** MMAP. This kernel accepts the MMAP hw_params; the failure comes later, at the first page touch. So `mmap_emul` over `hw` passes MMAP straight through and still oopses.

**Other standard plugin routes were checked and none of them work:**

* **hw plugin options.** Only `card`, `device`, `subdevice`, `sync_ptr_ioctl`, `nonblock`, `rate`, `min_rate`, `max_rate`, `format`, `channels`, `chmap` and `drain_silence` exist (`pcm_hw.c:1912-2040`). The `mmap_emulation` argument is "Obsoleted" and `ATTRIBUTE_UNUSED` (:1750-1760). No hw access-mask or environment override exists; only `LIBASOUND_COMPAT`, `THREAD_SAFE` and `DEBUG` are read.
* **`dmix`/`dshare`/`dsnoop`** mmap the hardware by design.
* **`softvol`, `route`, `rate`, `plug`-in-`plug`** use the same generic plugin mmap path.
* **`file`→`null` FIFO into `aplay`** would avoid the hw mmap, but `null` has no real clock or delay. That breaks cubeb's latency, position and A/V sync, and leaves cubeb's poll loop with no backpressure, so it was rejected as a hack.

## 5. Recommended route: PulseAudio serial sink plus a fail-closed ALSA default

PulseAudio 17.0 source (`sources/alsa-mmap-opus/pulseaudio/`, matching Alpine `pulseaudio` 17.0-r7):

* **RW access.** With `mmap=0`, `pa_alsa_set_hw_params` sets `SND_PCM_ACCESS_RW_INTERLEAVED` (`alsa-util.c:251-257`) and forces tsched off. The sink writes with `snd_pcm_writei` (`alsa-sink.c:908`), and its access mode is published as `"serial"` (:2653).
* **No plug in the way.** It opens with `SND_PCM_NO_AUTO_RESAMPLE|NO_AUTO_CHANNELS|NO_AUTO_FORMAT` (`alsa-util.c:715-725`), converts in software, and hands `hw` its exact native format.
* **Hazard:** if the native spec is refused, it retries with `"plug:"` + device (`alsa-util.c:~752`). With RW access and a matching spec, plug still inserts nothing. Pin `format=s16le rate=48000 channels=2`, which the existing silence preflight already proved on this PCM, and fail the test if the log shows `plug:`.
* **Amps untouched.** `device=` with no `control=` and no mapping makes `find_mixer` return at once (`alsa-sink.c:2181-2188`). PulseAudio never touches mixer controls, so the speaker amps stay under the existing guarded helper.
* **Reopen stays RW.** Unsuspend reopens with the stored `use_mmap=false` and refuses a mode change (`alsa-sink.c:1244-1252`).
* **Firefox needs no change.** It picks `pulse-rust` automatically (§2): no sandbox change, no prefs, no Firefox rebuild. Its process maps `libpulse.so.0` and never opens `/dev/snd/pcm*`.

**ALSA guard** (`/etc/asound.conf`; it is loaded by `alsa.conf` hooks, :14):

```
# asus-alsa-rw-guard-v1: no plug on DL1; float/MMAP-converting clients fail closed
pcm.!default { type hw card 0 device 0 }
ctl.!default { type hw card 0 }
```

`snd_pcm_set_params` applies access, then format, before any commit (`pcm.c:8844-8868`). A FLOAT_LE client such as cubeb's fallback therefore fails at `set_format` and gets `CUBEB_ERROR_INVALID_FORMAT`, with no hw_params and no mmap. Native S16/48k/2 RW clients such as `aplay` still work. The guard does not protect against clients that explicitly ask for MMAP access (`aplay -M`, a default PulseAudio with mmap on, dmix); keep those off DL1. Revert by deleting the file.

**PulseAudio lifecycle implications:**

1. **Never use `default.pa`.** It falls back to `module-detect` when there is no udev (`default.pa.in:57-68`), and that loads `module-alsa-sink` with its default `use_mmap = true` (`alsa-sink.c:2339`), which means an immediate oops. Always run `-n -F <own script>` with `--disallow-module-loading`.
2. **No autospawn as root.** libpulse does not autospawn when uid 0 (`context.c:1052-1058`), so a daemon that is down is simply missing. Firefox then falls through to ALSA, and that is why the guard is required. PulseAudio as root without `--system` only logs a warning (`main.c:816-817`). The desktop and Firefox run as root (`asus-goodix-desktop:104-105`), and the default socket `/run/user/0/pulse/native` matches Firefox's `XDG_RUNTIME_DIR`.
3. **Start order.** cubeb picks its backend once per context. Start PulseAudio first, then start or restart Firefox.
4. **PCM ownership.** In the trial, without `module-suspend-on-idle`, PulseAudio holds DL1 open and writes zeros continuously. That costs a little CPU and IRQ load and makes `hw:0,0` busy for the speaker fixture and diagnostics, so stop PulseAudio before using them. Suspend-on-idle can be considered later; reopen stays RW.
5. **Shutdown order.** Firefox, then PulseAudio with TERM, then confirm the PCM is closed and the amps are off.
6. **Packages.** `pulseaudio`, `pulseaudio-alsa` (module-alsa-sink lives there), `libpulse`, `pulseaudio-utils` (pactl). Do **not** install `alsa-plugins-pulse` during this experiment, because it changes ALSA defaults.

## 6. One bounded test: silence, amps off, unmuted browser

These are preconditions for the parent, after guarded re-entry with the GUI held (§7). Verify read-only that both amp switches are Off and that `/proc/asound/card0/pcm0p/sub0/status` reads `closed`. Install the four packages above. Write the guard. Confirm the chain without any float probe: `aplay -v -D default -f S16_LE -r 48000 -c 2 -d 1 /dev/zero` must print `Hardware PCM card 0` and **no** `Plug PCM`.

**Step A: PulseAudio under strace** (RAM directory `/run/asus-audio-trial/`, script `pa-rw.pa`):

```
.fail
load-module module-alsa-sink device=hw:0,0 sink_name=asus_dl1_rw mmap=0 tsched=0 format=s16le rate=48000 channels=2
load-module module-native-protocol-unix
set-default-sink asus_dl1_rw
```

Start it with: `strace -f -tt -e trace=openat,mmap,ioctl -o /run/asus-audio-trial/pa.strace pulseaudio -n -F /run/asus-audio-trial/pa-rw.pa --daemonize=no --exit-idle-time=-1 --disallow-exit --disallow-module-loading --use-pid-file=no --realtime=no --high-priority=no --default-sample-rate=48000 --alternate-sample-rate=48000 --log-target=file:/run/asus-audio-trial/pa.log --log-level=info &`.

Within 10 s, all of the following must pass:

* (a) `/proc/asound/card0/pcm0p/sub0/hw_params` shows `access: RW_INTERLEAVED`, `S16_LE`, 48000, 2 channels. This is the kernel's own view.
* (b) Every `mmap` in strace on the `pcmC0D0p` fd uses offset `0x80000000` or `0x81000000`; there are **none at 0**.
* (c) `/proc/<pa>/maps` has no `pcmC0D0p` line at offset `00000000`.
* (d) The log names `hw:0,0` (not `plug:`), and `pactl list sinks` shows `device.access_mode = "serial"`.
* (e) Both amps are still Off.

If anything fails, stop PulseAudio with TERM and go no further. strace records evidence; it does not guard. The guard is the source proof that `mmap=0` never maps data.

**Step B: browser, unmuted and inaudible.** Restart Firefox (normal profile, dashboard). Open the existing local H264+AAC fixture and play it with `volume=0.05` (non-zero, so an AudioSink is created) for about 10 s. Pass requires:

* `currentTime` advances and `error=null`.
* `pactl list sink-inputs` shows a Firefox stream.
* Every Firefox PID maps `libpulse.so.0`, and none has `/dev/snd/pcm*` in its fds or maps.
* `hw_params` is still RW_INTERLEAVED, amps are still Off, and the dmesg tail has no new oops.
* Seccomp is still 2 on the utility process.

Then pause, close the fixture, and keep PulseAudio running. Audible speaker tests come only after this, with the existing guarded amp helper and PulseAudio still serial.

## 7. Reversible startup plan (stop Firefox restoring a crash-producing tab)

On the first boot after re-entry, Firefox would see an unclean shutdown and restore the session automatically. `browser.startup.page=0` does not stop crash resume.

1. **Before re-entry, hold the GUI** by renaming only the outer VFAT marker `GUI.ENABLE` to `GUI.ENABLE.held` in the SD folder; leave the ext4 image alone. `recovery-init.sh:187` deletes the stale `enable-gui` on every boot and recreates it only from that marker (:198-203). `recovery-sysinit.sh:99` starts the desktop only when it is present. Alpine then boots with Wi-Fi, persistence and SSH but no Xorg or Firefox. First confirm that the reinstalled capsule's init is this source.
2. **Over SSH**, with Firefox closed, append these to `/etc/asus-goodix/firefox-user.js` (copied into the profile on every launch, `asus-goodix-browser:54`):
   * `user_pref("browser.sessionstore.resume_from_crash", false);`
   * `user_pref("media.autoplay.default", 5);`

   Then write the guard and run §6 step A.
3. Start the desktop with the existing `scripts/recovery-start-desktop.sh` path, run §6 step B, then rename the marker back after checking that its content is exactly `asus-alpine-desktop-v1`.
4. **Reverting:** values set in user.js persist in `prefs.js`. Remove the lines **and** set them back once to the defaults (`true`, `1`) while Firefox is closed. Do not delete session files or the profile.

## 8. Proven versus unproven: panic versus Android selection

* **Proven:** a userspace write by the Firefox cubeb thread to the mmapped DL1 data buffer caused a kernel paging oops in `get_page` through the vendor `.page`. MTK `ipanic_die`/mrdump ran, then a nested panic followed. This fully explains the lost Alpine SSH.
* **Not proven:** why the next boot came up in stock Android from BOOT while the BCB still held `boot-recovery` (SHA `7b3d5382…`). The kernel log ends before any reset decision, and the LK source is not among the original sources (`asus-original/` holds only external, hardware, kernel, ndk, prebuilts and vendor). Ordinary reboots with this BCB reached Alpine; this panic or watchdog-type reset did not. The bootloader branch is unidentified. Do not depend on this as a failsafe, and do not clear or rewrite the BCB because of it.

## Recommended next action

The parent performs the guarded recovery-only re-entry with `GUI.ENABLE` held (§7.1). Over SSH, it installs the four PulseAudio packages, the ALSA guard and the two user.js prefs, then runs §6 step A (PulseAudio serial, under strace, amps off), then step B (unmuted, inaudible Firefox playback). Persist PulseAudio startup in the desktop only after both pass; audible and YouTube tests come after that.

## Remaining unknowns

* Whether the Alpine 3.24 `pulseaudio` and `libpulse` packages install cleanly and run on 3.18 (syscalls: memfd and shm fallback). Check their log on first start.
* That `media.autoplay.default=5` and `resume_from_crash=false` behave as expected on ESR 140 in this profile. They are standard prefs, but this report did not verify them against source.
* Which Firefox process hosts the cubeb/AudioIPC context. Record it in step B.
* The `memstart_addr` arithmetic residual in §1.
* The LK selection branch after a panic (§8).
* No physical audibility of browser audio yet.
* `.gitignore` does not list `sources/alsa-mmap-opus/`. It holds public sources only, but the parent may want to add it to match the other source directories.
