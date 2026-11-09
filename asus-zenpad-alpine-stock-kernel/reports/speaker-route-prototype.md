# Bounded speaker route prototype

2026-11-08. Implemented only `scripts/speaker-route-prototype.py`. No hardware, SSH, ADB, USB, mixer, PCM playback, helper/config/profile/image/package changes were performed by the implementation agent. No persistent integration. Parent must review before staging or actuation.

## Interface

Parent creates a fresh, empty, root-owned 0700 tmpfs directory for each episode, preloads the browser fixture page, then launches:

```sh
python3 /path/to/speaker-route-prototype.py --episode-dir /run/PARENT-FRESH-EPISODE --route-root /run/asus-goodix-audio --cap-seconds 6
```

The launcher becomes guardian G and creates its own session if needed. There is no daemonization/restart or stdin command channel. The shared route root must already exist and remain `/run/asus-goodix-audio`, matching the installed owned-audio helper. The existing PulseAudio server must initially be SUSPENDED with PCM closed. This prototype does not start or stop it.

Wait for episode `status.json` with `phase: "READY"` and `ready: true`; immediately trigger the preloaded browser fixture. Stable status keys:

- `guardian_pid`, `guardian_start`, `controller_pid`, `controller_start`, `boot_id`.
- `phase`: STARTING, READY, ON, OFF, DONE, ERROR.
- `ready_monotonic`, `cap_monotonic`, `cleanup_monotonic`.
- Final `outcome`, or `error` / `lock_retained` on failure.

The cap begins at C's readiness timestamp after the bounded subscribe handshake and never renews on heartbeats. For cap 6, G begins forced cleanup at READY+4.9 s, reserving 1.1 s for Ext write/readback then Speaker write/readback; the absolute gate-Off target is READY+6 s. Class/gain restoration can follow that deadline. Commands time out after 250 ms, including the installed helper's original longer pactl query. Cap accepts 3.5–6 s, never more than 6.

For normal A, observe `sink_state` IDLE followed by `off_verified` (reason IDLE), then SIGTERM the exact stamped controller, not PulseAudio. Wait for G exit, DONE, preimage absent and lock acquirable before cap cleanup. For B, start a fresh episode on the same PulseAudio, trigger playback at READY, then SIGSTOP C immediately after `on_verified`. Expect `heartbeat_expired`, `descendants_reaped`, Ext/Speaker Off readbacks, `restore_verified`, `preimage_deleted`, `cleanup_verified`, DONE. Confirm lock reacquisition and C group gone. OFF persists after ordinary idle until C stops or playback resumes; class/gain are not restored on every idle.

## Evidence and ownership

`events.jsonl` uses one append per JSON record with monotonic/wall timestamps and writing PID. Events include `control_write`, `control_read` (public raw mixer response), `sink_state`, `on_begin`, `on_verified`, `off_begin`, `off_verified`, `restore_verified`, `preimage_deleted`, `controller_exit`, guardian termination reason, `descendants_reaped`, `cleanup_verified`. Off begin/end include hardware PCM open state. Runtime data stays in protected RAM; shared root contains `route.lock` and `route-preimage.json`. No network/profile identifiers are emitted.

G takes O_NOFOLLOW/nonblocking exclusive flock on the fixed lock before recovery or mutation. G and forked C share its open file description. Every amixer writer inherits that same descriptor via `pass_fds`; readers do not. If both G and C die, an orphan writer still excludes the next owner until it dies. No explicit LOCK_UN exists: that would unlock all holders' shared description. G normally closes only after reap and verified cleanup.

G becomes Linux child-subreaper before fork. C uses a separate process group, real PR_SET_PDEATHSIG(SIGKILL), then checks G's PID. All C subprocesses retain C's group. Timed-out commands are killed and waited before returning. On failure/expiry G kills C's entire group, reaps all descendants to ECHILD, then writes Off/restoration; G never writes On. Clean EOF after preimage deletion gets up to 50 ms to let C become an owned zombie via waitid(WNOWAIT), retaining PID identity through kill/reap and avoiding false SIGKILL classification.

Subprocess and wakeup heartbeats feed the 2.5 s guardian timeout. Startup has three subscription/query attempts and an independent 3 s guardian deadline. Client events are used only to establish subscription registration, then only exact `on sink #` lines wake requery; a 1 s poll covers coalesced/missed events. The actual installed helper's verify_sink/owned functions load as Python source from `/usr/local/bin/asus-goodix-audio`; its subprocess interface is privately adapted to 250 ms without modifying the helper or global subprocess module. On revalidates RUNNING/native Pulse-owned RW PCM. This script never opens native PCM.

Startup verifies exact root marker/kernel/card, loaded codec compatible/GPIO28, root loop marker, root st_dev/block alias st_rdev/sysfs major:minor/ext4 mountinfo/exact backing file, ALSA guard and helper-owned PulseAudio metadata/config. It reads route gates and other analog amps Off, verifies gain index1=0Db/class index1=CLASSAB, and saves class/gain without startup analog writes. Old rootfs mount entries are ignored. On: gain1, class1, Speaker1, Ext1, each read back. Off requires confirmed Ext0 before Speaker0. Restoration requires both gates0, then class/gain with readbacks.

Leftover preimages require exact schema/version, same boot, matching owned PulseAudio identity, previous guardian PID/start no longer alive, and saved class/gain present in actual enums. Gain0 is refused because the vendor setter clamps it to1. With lock acquired, valid leftovers shut down/restore before SUSPENDED/closed is required for the new episode. Invalid/stale preimages trigger gate shutdown/refusal without class/gain restoration. Powered gates without a preimage likewise cause gate-only shutdown/refusal. Audio-validation failure shuts down powered route gates and refuses startup.

## Local verification

Host Python syntax compilation passed. Actual Linux process tests ran offline in the already present `asus-rom-audit:2026-11-05` builder image with disposable `docker run --rm --network=none --read-only`, tmpfs and read-only prototype bind. No pulls, installs, persistent container or cloud resources. Tests imported the real primitives; no fake audio backend or macOS prctl substitution:

1. Actual Episode.run(writer=True) spawned a writer in C's pgid holding its shared lock. SIGSTOP C, wait 2.5 s, actual kill_and_reap: 2.501 s, C+writer reaped, group gone, fresh flock only after closing original owner.
2. Kill C/close G descriptor while writer survives: fresh flock refused. Kill/reap writer: flock succeeded.
3. Real PR_SET_PDEATHSIG plus parent check: killing G killed C, outer subreaper reaped C with SIGKILL.

This proves process/lock primitives, not tablet timing, subscription behavior, ALSA latency, physical audibility or real route cleanup. Parent owns actual A/B gates. Root/PulseAudio checks are deliberately strict.

## Limits

Six-second target assumes a responsive scheduler/kernel and killable/reapable subprocesses. Uninterruptible kernel operations cannot have a userspace completion guarantee. After two failed forced-cleanup attempts, G writes ERROR/lock_retained=true and waits holding the lock; no new On writes occur. This exceptional hardware-failure state can outlive six seconds and needs parent-directed recovery. Startup gate-verification failures get the same lock retention. Do not kill such G and restart without examining the failure.

Killing G and C together defers physical shutdown to the next validated owner; a surviving writer retains exclusion. Server loss may close PCM before Off, as Opus described. Kernel failure, power loss and suspend remain outside coverage. No permanent enablement or physical success is claimed.
