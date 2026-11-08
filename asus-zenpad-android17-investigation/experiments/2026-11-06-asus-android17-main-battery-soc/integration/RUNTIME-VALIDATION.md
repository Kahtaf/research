# Future parent-owned runtime validation

No step below was executed in this spike. Use only the parent's separately
reviewed image/backup/restore and physical-test procedure. Charging remains
inhibited for every step; enabling it is a separate task.

1. Finish the Linux ARM64 kernel and Android builds from APPLY-AND-BUILD.md.
   Record image/config/DTB hashes. Inspect the compiled DT for the absent charging
   opt-in, unchanged limits and all four complete model tables. Confirm the new
   Health source and both framework startup/error changes are in the image.
2. On the controlled first boot, collect kernel model/PMIC/BQ errors and Health
   logs locally. Observe `battery/present`, `voltage_now`, `temp`, `status`, and
   `capacity`; compare physical units and plausible readings with stock or an
   independent reference. Confirm actual BQ CHG_CONFIG remains clear, including
   plugged/unplugged. No cover supply may contribute a property.
3. Verify startup first. Before a valid initialized model update, capacity must
   fail and Health must wait/report failure, never publish present + default 0.
   After the two real samples, verify a genuine capacity and working framework
   callback. Check a fault between service preflight and first callback: no
   fatal HealthLoop CHECK, uncaught ServiceSpecificException, or null-data startup.
4. Observe a normal discharge interval under several ordinary tablet workloads.
   Compare raw voltage, checked temperature, model SOC and stock behavior where
   practical. Record SOC jumps, low-end behavior and update timing. These are
   model validation measurements, not an invitation to fit a new battery curve
   or upload private per-unit calibration. Do not deliberately exhaust a battery
   to prove the already host-tested genuine-zero branch during a first boot.
5. Exercise short and long suspend/resume and rapid repeated wakeups. Capacity
   must be unavailable during suspension and until the post-resume initialized
   update. No unobserved interval may be integrated using the resumed sample.
   Check wake ordering, uevent delivery, eventual callback recovery and the
   magnitude of VBAT-seed/relaxation jumps. Confirm no stale capacity survives
   the 30-second limit if the worker stops making progress.
6. Under a separately reviewed debug/test-kernel method, inject bounded ADC/I2C
   errors and conversion timeouts at startup and after valid SOC. Do not spoof
   Android properties or replace battery files with constants. Verify kernel
   errno, HAL STATUS_UNKNOWN, retained callback registration, an alive retrying
   service and recovery on genuinely valid samples. Test prolonged failure:
   normal startup remains gated; after startup the framework keeps its last
   delivered sample while HAL calls/dumps/logs expose the failure. Establish the
   product policy for such a prolonged fault before calling the tablet complete.

Current, charge counter and full-charge capacity remain unsupported individual
properties. Numeric optional aggregate defaults are not measurements. Battery
health remains Unknown; no good-health or charging-safety certification is made.
The battery work does not resolve unrelated product, graphics, radio, userdata
or Google integration gates. A successful compile alone is not a runtime pass.
