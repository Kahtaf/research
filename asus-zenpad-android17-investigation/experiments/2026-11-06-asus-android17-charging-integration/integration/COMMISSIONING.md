# Ordered physical gates — parent only

There has been no physical 4.9 boot. Original stock recovery was restored by
the parent. Keep its independently verified restore procedure, known stock
images and separately reviewed new-kernel diagnostic transport. This work
neither authorizes a flash nor changes data/storage. Internal storage preference
does not require touching any user data for charger commissioning.

1. **Target build, still inhibited.** Apply in the documented order, compile and
   link on Linux ARM64, check actual output config and compiled DT. The first
   new-kernel test has no charging permission. Review reset/default-mode risk:
   a chip reset can turn charging on before software detects it, and a dead
   I2C bus cannot be made physically safe by returning an errno. Have an
   independent way to remove the input source immediately.
2. **Observe the inhibited board.** Capture existing main battery properties
   and the new read-only `charge_guard` attribute under the bound
   `asus-p00a-bq25896` I2C device. Verify CHG_CONFIG=0/OTG_CONFIG=0, input ceiling,
   actual safety/termination/watchdog fields, ID 0x06 and no unexpected enabled
   interval. Validate main PMIC VBAT, battery NTC and BATON, with stock and an
   independent instrument where available. Stock reported 87%, 29.0 C,
   VBAT 4132 mV and charger 4976 mV; that is a sanity reference, not a calibration
   constant or required new-kernel result. The early ~0.54 s register dump is
   explicitly not the operating policy; later stock writes changed limits.
3. **Exercise attach, detach and PM while inhibited.** Verify both a USB host
   and a qualified dedicated adapter; include rapid unplug/replug. Capture
   source callback execution, classification, 100 mA reset and fresh sample
   generations. Prove USB PHY BC1.2 clock/mux and DCP/CDP classification on this
   board before trusting the corresponding 1000/1500 mA ceilings. Confirm
   unqualified SDP/nonstandard sources stay at 100 mA. Suspend/resume must leave
   charge off until fresh checked SOC and source classification return. Observe
   actual worker cadence and BQ busy-to-done conversions within their bounds.
4. **Review error and thermal behavior.** Use parent-reviewed fault-injection
   facilities or controlled instrumented test builds, never arbitrary public
   register writers. Reproduce absent battery, PMIC read errors/timeouts, BQ
   read/write/readback errors, stale SOC, TS faults, thermal conditions, reset
   and watchdog faults. Do not physically disconnect or heat a pack merely to
   satisfy a checklist; use a qualified test arrangement. Verify the first
   fault latch survives a second-read failure and telemetry reads, and that
   commands cannot enable on invalid data. Establish the board's actual TS
   wiring, temperature cutoffs, timer duration, hardware disable behavior,
   fault latency and source IRQ delivery. A failed disable is an unverified
   hardware state requiring input removal, not a passed test.
5. **Review a separate bounded enablement candidate.** Only after the preceding
   measurements are accepted may the parent add permission to a separate,
   explicitly reviewed candidate. This delivery does not contain that property
   or a software register writer. Keep the staged conservative 4.208 V / 512 mA
   request, the original upper ceilings, hardware NTC/termination/timer, and
   source-qualified input cap. Start on a physically validated dedicated
   adapter, attended, with external input removal available and a pre-agreed
   short session duration. Unknown/SDP 100 mA is a diagnostic compatibility
   limit and may not sustain this tablet; do not mistake its net discharge for
   a reason to raise the cap without source qualification.
6. **Prove charge gain.** Record before/during/after voltage, actual battery
   temperature, initialized SOC, source input and elapsed time. Readbacks must
   show the expected CV/current/input limits and CHG_CONFIG, with no fault.
   `ichg_limit_ma` is a programmed ceiling. The optional
   `charger_branch_current_ma` is usable only when its validity flag is 1; it
   is a completed BQ ADC sample of charge-path current, NOT measured net pack
   current and not Android CURRENT_NOW. Use independent measurement and
   sustained charge gain to establish that power entering exceeds tablet load.
   Verify stop on source loss, error, stale data and thermal boundaries; check
   a fresh recovery sequence rather than reusing pre-fault SOC or input caps.
7. **Prove the screen-off/runtime behavior.** In this staged runtime policy an
   enabled session holds a wake source, allowing the display to sleep while
   keeping sampling/guard work alive. Verify positive charge gain and thermal
   stability with the display off, plus normal tablet use and heavy load.
   Confirm wake-source release after verified off/unplug. Forced system
   suspend still disables charging, and resume starts from invalid state.
8. **Finish the daily-use policy.** Measure standby power, charge completion,
   top-up behavior, long-session temperature and SOC accuracy. This policy
   keeps the CPU awake even at hardware termination while the approved session
   remains active, so it is not the final efficient overnight policy. Charging
   across real suspend needs a separate design and physical proof: correct
   hardware TS cutoffs compatible with the stricter 0/50 C software envelope,
   valid charge/timer/voltage limits, fault/reset behavior, an effective wake
   route and explicit handling of unavailable SOC during sleep. Do not mark
   stale SOC fresh, delete suspend guards, or rely on watchdog expiry to turn
   charging off. TI documents that expiry restores default charging behavior.

Successful compilation, a set CHG_CONFIG bit, a Charging status, or an ADC
charge-path reading alone is not a complete functional/daily-use charging claim.
The completion evidence is controlled charge gain alongside genuine Android 17,
correct stops/recovery and a validated long-term power policy.
