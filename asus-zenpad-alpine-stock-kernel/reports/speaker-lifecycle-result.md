# Experiment53: bounded automatic speaker shutdown on the real tablet

PASS, prototype only. A separate guardian/controller implementation and quiet browser fixture ran two consecutive episodes on the SAME qualified PulseAudio daemon. Nothing was added to normal desktop startup. No existing helper/config/profile preferences, package, boot/recovery/BCB/kernel/firmware or calibration changes. Device stayed stationary and control used pinned Wi-Fi SSH.

Preconditions: PCM closed/SUSPENDED, all analog gates off, saved class0/gain1, exact original kernel/SD-root/loaded codecGPIO28, safe serial PulseAudio, no held route lock or preimage. Immutable3s AAC SHA2b304ffa… contains1s faded440Hz tone, decoded peak-39.886dBFS between silence; browser volume0.05, unmuted. Two actual browser media end events reached3.021333s with no decoder error.

Episode A: proper gain/class then Speaker→Ext enable order and readbacks. After IDLE was observed, Ext→Speaker shutdown completed in0.145209s while PCM was still open,3.620681s after READY, within the6s cap. Controller terminated cleanly; class/gain restored0/1, preimage removed, lock released, no member of its process group survived. A subsequent PCM idle close passed.

Episode B: a fresh guardian/controller acquired the same lock, proving handoff. After both amps read On, parent injected SIGSTOP into ONLY the exact stamped controller. Guardian heartbeat expiry was2.496649s after injection (2.5s since last heartbeat), then whole-group kill and child-subreaper reap preceded ordered Ext→Speaker Off. Off completed2.987318s after READY while PCM still open. Class/gain restored, preimage removed, lock released, no surviving group member. Same PulseAudio stayed alive and later suspended with PCM closed.

Final gates0/0, PCM closed, Firefox no hardware PCM fd/map, no new kernel oops. Physical browser audibility remains UNCONFIRMED because owner is away. Do not turn this into a persistent desktop route until that physical gate is available. Keep existing daily desktop silent with the safe serial output path and idle suspend.

The root review also corrected two details beyond the initial Opus proposal: every mixer WRITER inherits the shared lock fd (so it survives both controller/guardian death), and no holder calls LOCK_UN (only last close releases the shared description). Ext must be confirmed Off before Speaker Off even on error. Actual root guard uses the mounted block alias/st_dev and ignores the old rootfs mount record. Offline actual Linux process-contract tests also passed in the existing network-disabled disposable builder; see speaker-route-prototype.md.

Prototype: scripts/speaker-route-prototype.py. One-run harness: scripts/verify-speaker-lifecycle.py. Fixture: scripts/speaker-lifecycle-fixture.py. Sanitized receipt: evidence/speaker-lifecycle-result.json. Raw protected RAM logs are under /run/asus-speaker-lifecycle and will be archived to ignored private/live. Detailed source recommendation is opus-speaker-lifecycle.md.

Hard caps assume a responsive kernel/scheduler and killable mixer commands. If Off cannot be verified, the prototype retains ownership in ERROR and never writes On again. Simultaneous guardian/controller death and kernel failures remain outside immediate cleanup coverage. No such fault occurred. No physical handling or USB action was requested.
