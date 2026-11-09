# Opus review: automatic speaker lifecycle (one design, challenged)

2026-11-08. Offline source review only. I did not touch the tablet, ADB, SSH or USB, ran no mixer or hardware commands, and changed no helper, config, profile or package. Public sources are in the ignored `sources/speaker-lifecycle-opus/` folder (see SOURCES.txt and SHA256SUMS). The vendor kernel paths below are relative to `../2026-11-05-asus-latest-android-feasibility/sources/asus-original/kernel-3.18/sound/soc/mediatek/mt_soc_audio_8163/`; `codec` means `mt_soc_codec_63xx.c`.

## Verdict

**Keep the proposed observer, with four required corrections.** No standard component gives these ordered transitions with these ownership and failure semantics:

- UCM DisableSequence runs only on explicit route or profile changes. Idle suspend does not run it.
- The ALSA ctl hook restores controls in forward order.
- Neither of them has a death or hang guardian.

So a small controller is justified. Sink RUNNING is the right trigger for turning the amps on, and leaving RUNNING is the right trigger for turning them off. The four corrections:

1. **Ownership.** Replace the "lease with PID, start time and heartbeat expiry" with a kernel-held exclusive lock. The guardian is the controller's parent, and the lock's open file description is shared by fork. This makes the stale-guardian case impossible by construction instead of something a protocol has to detect.
2. **Stray writers.** The guardian must be a child subreaper and must reap every descendant before its cleanup writes. Otherwise an orphaned `amixer` started by a killed controller could set Ext=On after the guardian has set it Off.
3. **Event handling.** Treat subscription events as level-triggered wakeups only, filtered to `on sink`. Events are coalesced and carry no state. Re-query the sink after every relevant event and on a 1 s timer. Ignore client events, except for the one-time handshake in step 3 below; otherwise each re-query's own `pactl` connection would retrigger the loop.
4. **Latency budget.** Every off path must complete in under the 5 s idle-suspend timeout, so the amps go off while the DAC still receives digital silence. Server loss is the one path where this cannot be guaranteed, because PCM closes in the same instant. That path is covered, but not ordered.

## Source facts that decide the design

**The vendor amp order is a functional requirement, not just a pop preference.**
- `GetDLStatus()` returns true if any analog device-power flag below `AUDIO_ANALOG_DEVICE_2IN1_SPK` (11) is set (codec:175–184). That range includes SPEAKERL (5) and EXTSPKAMP (10) (`mt_soc_analog_type.h:108,113–114`).
- `Speaker_Amp_Change(true)` calls `TurnOnDacPower()` only if `GetDLStatus()` is false (codec:1298–1299). `Speaker_Amp_Change(false)` calls `TurnOffDacPower()` only if it is still false at the end (codec:1379–1380).
- So **Ext on before Speaker would skip DAC power-up**, and **Speaker off before Ext would leave DAC, clock buffer and NVREG powered** (`TurnOffDacPower`, codec:983–994). The only correct order is Speaker→Ext for on and Ext→Speaker for off.

**Class must not change while Speaker is on.**
- `Audio_Speaker_class_Switch` only stores `Speaker_mode` (codec:1812–1819).
- The close path picks ClassD_close or ClassAB_close from the *current* `Speaker_mode` (codec:1360–1365).
- Restoring the saved class (default CLASSD, codec:127) before Speaker is Off would run the wrong close sequence. "Restore class only after a confirmed Off" is therefore mandatory.

**The gain setter writes SPK_CON9 even when the amps are off** (codec:1828–1857). The saved gain is already index 1 (0Db), so this write is a no-op, but it is still a register write. The setter clamps index 0 (`Mute`) to 1.

**Writes are not fully idempotent.**
- `Speaker_Amp_Set` changes state only if the value differs (codec:1392–1407).
- `Ext_Speaker_Amp_Set` toggles the GPIO on every write (codec:1602–1615). This is harmless but means the guardian's forced Off is a real write.
- Both setters return 0. ALSA therefore emits no control-change event, so nothing can watch these controls for writes by others. Readback must be explicit.

**PCM close does not touch the amps.**
- `mtk_soc_pcm_dl1_close` (`mt_soc_pcm_dl1.c:349–374`) stops the I2S DAC memory path, AFE and clocks. It never clears the analog device-power flags.
- Speaker_Amp powers the DAC itself when needed. So amps-on with PCM closed is a powered analog path with no data, not an undefined state.
- This confirms from the kernel side that idle suspend can never turn the amps off.

**What RUNNING means in PulseAudio 17.**
- `pa_sink_update_status` sets RUNNING iff `pa_sink_used_by() > 0` (sink.c:910–919). `pa_sink_used_by` counts linked sink inputs minus corked ones. It explicitly ignores monitor-source streams (sink.c:2503–2517).
- The cork count is kept by `update_n_corked` on put, cork, unlink and move (sink-input.c:685–754, 797–816, 896–924, 1890–1902, 2203–2209).
- **RUNNING therefore means at least one uncorked playback stream exists.** A `pactl` query or subscriber has no stream. A recorder on the monitor source keeps the sink IDLE: it blocks suspend (`pa_sink_check_suspend`, sink.c:2520–2555) but does not make the sink RUNNING. A corked stream gives IDLE.
- Firefox ESR140 cubeb-pulse creates streams `START_CORKED` (stream.rs:459,502), uncorks on start (640) and corks on stop (669) and on destroy (585). Pause and teardown therefore leave RUNNING.

**RUNNING implies the PCM is already open.**
- `sink_set_state` synchronously sends SET_STATE to the IO thread (`pa_asyncmsgq_send`, sink.c:465). There, `alsa-sink.c:1399–1450` calls `unsuspend()` (it opens the PCM) before the main thread updates `s->state` and posts the CHANGE event (sink.c:498–507).
- If resume fails, the state stays SUSPENDED (sink.c:440–486).
- So "amps on after RUNNING is seen" preserves the PCM-before-route order that was used in the heard direct tone.

**Limit of RUNNING:** it means demand, not audibility. An uncorked stream playing digital silence keeps the amps on. A muted `<video>` stream also counts. The cost is power and possible hiss, not a safety violation. The gate below measures that pause reaches IDLE. I did not source-review whether Firefox keeps silent WebAudio graphs uncorked, so do not claim that either way.

**Event semantics.**
- Sink CHANGE events are posted for state changes and also for volume, mute, port and similar changes (sink.c:506,558,579,605,626).
- Events are dropped as duplicates while an event for the same object is still queued (core-subscribe.c:206–246). They carry no new state.
- `pactl subscribe` subscribes with no completion callback (pactl.c:2483–2497), so it gives no "subscription active" signal. It prints one line per event and flushes (2205–2225). It exits on TERMINATED or FAILED (2516–2523), so server loss shows up as EOF.
- Every new client posts CLIENT new and remove events (client.c:75,97).

**Server exit order.**
- Modules unload in reverse load order (module.c:351–362, called at daemon main.c:1378). The order is: suspend-on-idle first, then native-protocol-unix (clients disconnect), then alsa-sink (PCM closes).
- On unload, suspend-on-idle *resumes* a suspended sink (module-suspend-on-idle.c:490–494), so the PCM briefly reopens during a stop.
- The observer is disconnected only microseconds before the PCM closes. **An ordinary stop must therefore turn the amps off and confirm Off before PulseAudio receives TERM.** It cannot rely on reacting to its own disconnect.

## Recommended design (the one route)

### Processes

- **Guardian G** is a small, single-purpose process started by `asus-goodix-audio start` after `verify_sink` passes and the amps are confirmed Off.
  - It calls `setsid` (as PulseAudio does) and `prctl(PR_SET_CHILD_SUBREAPER, 1)` (available since Linux 3.4).
  - It opens `/run/asus-goodix-audio/route.lock` and takes `flock(LOCK_EX|LOCK_NB)`. If that fails, it reports busy and exits; no route writes happen.
  - Holding the lock, it handles any leftover preimage (recovery rule below).
  - It reads Ext, Speaker, class and gain. It requires Ext=0 and Speaker=0.
  - It writes `route-preimage.json` atomically: class and gain values, PulseAudio pid/start/boot, its own pid/start.
  - It creates a heartbeat pipe, then forks controller C. C inherits the locked descriptor and the pipe's write end.
- **Controller C** calls `setpgid(0,0)` and `prctl(PR_SET_PDEATHSIG, SIGKILL)`, then checks `getppid()==G`. If G is gone, C exits without writing.
  - C spawns `pactl subscribe` (same environment, same process group) and reads its stdout with `select`, using a 1 s timeout.
  - All `amixer` and `pactl` subprocesses run with timeout ≤1 s, in C's process group.
  - C writes one heartbeat byte after every wakeup and after every subprocess call.

### Ownership rule (replaces the PID/heartbeat lease)

- The route lock is held by one open file description shared by G and C. The kernel releases it only when **both** have exited. Every route writer is G or a descendant of C. A new episode cannot exist while any process of the old one is alive, so a stale guardian can never act on a later owner's route.
- The parent/child relationship also removes PID reuse without pidfds, which the 3.18 kernel lacks. G's `waitpid` targets a zombie it owns. The subreaper makes orphaned `amixer` processes G's children, and G reaps them.
- No epoch numbers or monotonic lease files are needed.
- **Recovery rule:** if a new G obtains the lock and finds a leftover preimage, every previous owner is dead (SIGKILL of both, OOM, desktop killed before cleanup).
  - G writes Ext Off, then Speaker Off, verifies both, restores class and gain from the preimage, verifies them, deletes the preimage, and only then proceeds.
  - If the amps are on and there is *no* preimage, G forces both gates Off, leaves class and gain untouched, logs the event and refuses the route. This fails closed and makes no unknown-state class or gain mutation.
  - `/run` is RAM, and the driver initialises all power flags false at boot, so a reboot needs no recovery.

### Controller loop (level-triggered)

1. Startup handshake to close the subscribe race: start `pactl subscribe`, then run `pactl list sinks short` until the subscriber has printed a `client` event for that query's connection. That proves the subscription was registered before the query connected. Bound this to 3 attempts, then fail closed. After that, ignore client events.
2. Desired state is `on` only if all of these hold:
   - The exact sink is RUNNING.
   - The owned PulseAudio identity matches the preimage.
   - `serial.pa` is exact.
   - `hw_params` shows RW_INTERLEAVED, S16_LE, 48000 Hz, 2 channels, and the PCM owner's Tgid is the PulseAudio PID.
   - No data-buffer map exists.

   Reuse `verify_sink()` exactly. Any exception means `off`.
3. Re-query on every `on sink` event and on every 1 s timeout. Transition only on a difference.
   - **On:** set gain 0Db, then class CLASSAB, and read both back. Then Speaker On, read back; Ext On, read back. Then a 25 ms settle.
   - **Off:** Ext Off, read back; Speaker Off, read back. Class and gain are *not* restored on every IDLE (they have no effect while Off and would only add register writes). They are restored once at episode end, by whichever process ends it.
4. On `pactl subscribe` EOF (server loss), any validation failure or SIGTERM: run Off, restore class and gain, verify, delete the preimage, exit 0. On an amixer readback mismatch: retry Off once, then exit nonzero and leave the cleanup to G.

### Guardian behaviour

G blocks on the heartbeat pipe with a 2.5 s timeout. That is above C's worst legal gap of about 1 s plus one subprocess, and below the 5 s suspend timeout.

- **On EOF** (C died) or **heartbeat expiry** (C hung): `killpg(C, SIGKILL)`, then `waitpid(-1)` until ECHILD, so that no descendant can still write. Then:
  - Ext Off, Speaker Off; read back both.
  - If the readback shows Off, restore class and gain; otherwise leave them as they are.
  - Delete the preimage only after full verification, then exit.
- **On C's clean exit 0** with the preimage already deleted, G just reaps and exits.
- G never writes On and never restarts C: there is no restart loop. After a failure the amps stay Off until the next desktop start.
- **Prototype only:** G also enforces an absolute episode cap and treats it like expiry. Do not run G as a permanent daemon until this gate passes.

### Ordering

**Start:** `asus-goodix-audio start` (PulseAudio validated, amps Off) → start G/C and wait for the handshake → Firefox. No amp writes at start.

**Ordinary stop.** The current `cleanup()` in `asus-goodix-desktop` (lines 37–59) kills the GUI and then calls `audio stop`. Keep that order, and change only `audio stop`:
1. Send SIGTERM to C (located through G).
2. Wait up to 2 s for G to exit with the lock released. Treat "lock acquirable" as proof that both are gone.
3. If either is still present, kill G's session and use the recovery rule.
4. Assert Ext=Speaker=0 and class/gain equal to the preimage.
5. Only then TERM PulseAudio.
6. The existing `amps_off()` assertion stays as the final check.

The ALSA fallback guard (`/etc/asound.conf`) is never touched.

## Which failure paths are truly coverable in userspace

| Failure | Detection | Covered? |
|---|---|---|
| Stream pause or end | RUNNING→IDLE event, or 1 s re-query | Yes, ordered, PCM still open |
| Missed or coalesced event | 1 s re-query | Yes, ≤1 s |
| C crash or SIGKILL | Pipe EOF in G | Yes |
| C hang (stuck subprocess, deadlock, SIGSTOP) | Heartbeat expiry in G (2.5 s) | Yes, <5 s |
| Orphaned amixer writing late | Subreaper reap before cleanup | Yes |
| PulseAudio crash or kill | Subscribe EOF in C | Amps go Off, but *after* PCM closes. Covered, not ordered (possible pop). |
| G and C both killed | Next G acquisition | Deferred to the next start. Amps may stay on until then. |
| Kernel oops/hang, power loss | none | Not coverable in userspace. Power loss and reboot reset the analog state. |
| System suspend | Driver's own analog suspend path (codec:200–258) | Out of scope. Suspend is unqualified. |

## Single highest-value failure gate: SIGSTOP the controller while the amps are on

This is the most informative single injection:
- It exercises the path no other test reaches: heartbeat expiry, then a group kill of a live but stopped process, then the subreaper reap, then ordered Off, then class/gain restore.
- The crash path (EOF) shares the same reap and cleanup code, only with faster detection.
- Server loss uses C's ordinary Off function, which the normal IDLE leg already exercises.
- Killing PulseAudio would deliberately cause the one unordered close and disrupt the qualified daemon.
- SIGSTOP needs no code fault injection and is fully reversible: the kill wakes the stopped process.

## Next bounded experiment (parent runs it; not run here)

Implement G/C as a separate prototype helper. Change no existing helper or config. Use one run with two consecutive episodes, each capped at 6 s, on the same PulseAudio daemon. Firefox stays a PulseAudio client, and PulseAudio holds the PCM.

Use the existing fixture: `artifacts/browser-sound-trial/sound.m4a`, SHA256 `2b304ffa302593d2bd2df9f0164f59ceba408f777247ce78a7d41a3cd0fe8888`, decoded peak −39.89 dBFS. Keep the page volume as in experiment 52 or lower.

**Precondition:** SUSPENDED, PCM closed, Ext=Speaker=0, class and gain recorded, no route.lock holder, no preimage.

**Episode A, normal leg:**
- Start G/C, wait for the handshake, play the fixture once.
- Required:
  - RUNNING is seen, with `verify_sink` passing.
  - The On sequence order and readback are logged.
  - After the media ends: IDLE, then Ext Off, then Speaker Off, logged ≤1.5 s after the IDLE transition and **while `hw_params` is still open**.
  - Then a clean SIGTERM to C: class and gain restored, preimage deleted, lock acquirable before the 6 s cap.

**Episode B, failure leg.** Its successful lock acquisition is also the handoff test.
- Start a new G/C and play again.
- Once the On readback is logged, `kill -STOP` C.
- Required:
  - G logs expiry within 2.5–3.5 s and kills and reaps all descendants.
  - Ext Off, then Speaker Off, read back 0/0; class and gain restored; preimage deleted; lock released; no surviving process in C's group.
  - Firefox keeps playing into a sink whose amps are Off, which is the expected fail-closed result. After the stream ends, the sink reaches SUSPENDED with PCM closed.

**Afterwards:** the same PulseAudio PID, no Firefox PCM fd or map, no new oops or ALSA errors in bounded dmesg, amps 0/0, PCM closed.

**Any deviation ends the run.** Do not add gain changes, retries or variants. Physical audibility of both legs remains deferred to the owner.

## Remaining blocker

None for a software design. The design is safe within the coverage table above. Three items remain open:
- **Server loss** cannot be made ordered.
- **Physical browser audibility** needs the owner.
- **Permanent enablement** (G/C as part of the desktop) should wait until the gate above passes and the owner confirms audibility.
