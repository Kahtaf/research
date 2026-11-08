Reference files confirmed at `2026-11-06-asus-linux49-probe-review/.../asus_p00a/`. Decision:

## Pick A — with one addition. Not B, not C yet.

**Why not B:** entry-40 / no-return-41 already proves the stall is *inside* the batt_vol property call. A control that skips batt_vol re-answers an answered question and localizes nothing. It is ambiguous (batt_temp, channel 5, same ADC+pwrap, likely stalls next; disabling voltage+temp together is the undesirable broad form), and as a permanent state it trades honest voltage data for a workaround. Even a "loop completes" outcome leaves you needing A to fix the real path.

**Why not C:** no blocking primitive is proven from verified source. The reference shows every loop bounded (`ADC_COUNT_TIMEOUT` polls, 5 samples, ms sleeps) — a bounded path returns in seconds and would have produced an out/return marker. A permanent hang therefore lives in an **unbounded primitive** (mutex_lock, regmap/pwrap serialization) or in a compiled base that differs from this reference. Both demand proof first; any timeout/enable patch now is a blind-guess variant. The stock reset-PC at adc+340 (immediately after the udelay BL) stays corroborating only — epoch unestablished.

**A is the unique unit whose every outcome is terminal:** each stage either names the blocked primitive or exonerates the adc path, so one physical run ends the breadcrumb phase.

## Gate (step 0, before any edit)

Byte-verify `asus_p00a_pmic_adc`, `p00a_pmic_prepare_adc`, `asus_p00a_pmic_present`, and the batt_vol case in `battery_diag.c` against the exact compiled base ELF of the current trials. **If any mismatch: stop and report** — the mismatch itself is root-cause evidence (e.g., an unbounded ready-bit poll in the shipped base is an immediate C candidate) and no instrumented run is needed.

## The one strictly-better tweak (same file, same discipline)

Add `present_enter` / `present_exit(ret)`. batt_vol calls `asus_p00a_pmic_present` **before** `asus_p00a_pmic_adc`; if the pwrap read inside present blocks, A-as-written shows only "no adc markers" and forks into a second run. Two fixed records (present result is 0/1/error — no CHR_CON7 raw) close that fork in the same candidate. Keep pwrap itself uninstrumented — we only need to *name* it as the blocked primitive, per the "pwrap only if source proves blocking" rule.

## Scope — one file: pmic_battery.inc (existing power_supply hooks retained)

Markers around existing calls; ops/locking unchanged. Fixed small records carrying PID/comm, work/body/property tokens (joins to 119/66/61/89), stage id, sample/poll index, ret. No raw ADC values, no new timekeeper/printk in the recorder, raw MRS unchanged.

1. `present_enter` / `present_exit(ret)`
2. `adc_enter(channel, samples)` / `adc_out(ret)`
3. `awake+mutex_after`
4. `prepare_enter` / `prepare_exit(ret)`
5. `trigger_after(ret, first sample)`
6. `udelay_after`
7. `read_after(ret)`; poll index at ready/timeout exit
8. `unlock/relax` at out

## Stopping criteria — one run, same protocol (fresh kernel UUID, full hash readback, BOOT/SYSTEM/DATA untouched, verified normal Android return, same anchors)

- No `present_enter` after property entry-40 → blocker before present (SOC-invalidate wrapper) → re-scope C there.
- `present_enter`, no `present_exit` → pwrap/regmap read blocked → C: source-proven bounded pwrap/serialization fix.
- Present ok, no `adc_enter` → switch dispatch between → re-scope.
- No `mutex_after` → `pmic_adc_mutex` held by another context → one bounded follow-up joins the owner (blocked-task list), then fix the holder.
- No `prepare_exit` → decimation wait or pwrap-in-prepare.
- No `udelay_after` → delay class (unlikely: timer IRQ counts progressed).
- Poll exit with `-ETIMEDOUT` recorded → adc completes bounded; blocker is after adc return (soc_invalidate / unwind), or reveals intermittency (contention, not dead hardware) → C there.
- All markers exit, still no returned-41 → blocker after adc in `battery_get_property` → C there.

Each row names exactly one fix-class. After the mapping, stop probing: no stage variants, no extra channels, no new clock/display/timekeeper work, no charging/DT/thermal writes, no raw/private values, no generic class/notifier/uevent hooks — those phases already returned or reached the named callback.

**Direct answer:** yes, A first — but the strictly better form is **A plus the present pair**, so the single run is decisive whichever side of `asus_p00a_pmic_adc` the block sits on.