# One candidate: phase-ladder breadcrumbs inside the named work

**Pick: instrumentation, not isolation.** Same single physical boot, same retained-area readback, zero semantic change to battery/charging/thermal. A skip-variant yields at most one bit ("hang gone"), loses psy/property identity, and a negative run is uninterpretable — the ambiguity you banned. Isolation stays in reserve as the RDMA-style single confirmation control *after* breadcrumbs name the blocker. Byte-verify each hooked body against the exact base first (System.map already fixed `power_supply_changed_work`).

## Hooks (one build, four groups)

**A — `power_supply_changed_work` body checkpoints**
- W1 body entry, before `dev_dbg`/first lock: work pointer (token66 linkage), `psy->desc->name` (≤16B memcpy), `psy->changed` value, preempt/CNTVCT/pid/comm. Closes the "dispatch ≠ body entry" gap.
- W2 after the changed_lock branch decision; W3 after `class_for_each_device`; W4 after `power_supply_update_leds`; W5 after `atomic_notifier_call_chain`; W6 after `kobject_uevent`; W7 at both exit paths before final unlock.

**B — `__power_supply_changed_work`** (runs under class mutex): C1 entry with `dev_name`; C2 `supplied_by` result + will-call-external flag; C3 after `external_power_changed` returns. Names the psy whose driver callback runs; no hooks inside driver callbacks.

**C — `power_supply_uevent`**: U1 entry (psy name, num_properties); U2 after `get_zeroed_page` (ok/-ENOMEM); U3 at return with ret. Brackets env build vs netlink/helper inside `kobject_uevent`.

**D — `power_supply_show_property`** (generic dispatch, all psy drivers): P1 before `psy->desc->get_property` with property enum + psy name; P2 after with ret. Names psy+property without touching the driver. (`update_leds`' STATUS read bypasses show_property; W3/W4 bracket it — phase-level naming suffices there.)

**Data discipline**: fixed 40B slots, enum phase, no ktime/printk/sleep/alloc (names are bounded memcpy), writer trylock + short irqsave, raw CNTVCT, generation/guard/loss/chronology identical to admitted recorder. Ring 128 slots (worst case ≈60 records), loss must be 0 for a decisive decode; loss>0 = admitted limited observation (token58 precedent). Breadcrumbs fire for **all** invocations — tokens 59–65 log their psy names free, so you learn whether token66's psy previously completed: per-psy vs environment discriminator at zero extra cost.

## Predictions

Positive (boundary recurs) — first missing breadcrumb names one of:
- R1: W1, silence before W3 with last C3 pending → `external_power_changed` of the named psy's driver.
- R2: W3+W4, no W5 → notifier chain.
- R3: W5, no U1 → `kobject_uevent` core (env/seq/netlink/usermodehelper).
- R4: U2, P pairs stop at property N → `get_property` of named psy — corroborates the aed PC at `asus_p00a_pmic_adc+340` without assuming it.
- R5: U1, no U2 → `get_zeroed_page` block (memory pressure).
- R6: full W7 but no token66 postcall → body completes; worker-core/postcall-recorder issue. Admit, redirect.

Negative (no boundary this run): all W7/P2 pairs complete. Report only, no automatic retry; parent decides rerun.

Unknown: perturbation shifts timing (mitigated by identical recorder discipline); property-enum set in this base must be verified, not assumed from reference source.

## Stopping point and fix path

One physical run, one decode, STOP. Each case maps to a small fix with no blanket disable: R1 → that driver's callback; R2 → one registered notifier (follow-up control only if needed); R3 → uevent emission only; R4 → that single property read path (ADC/pwrap serialization or timeout — the old source's bounded workaround is the shape, not the assumption). If causal proof is demanded after R4: one RDMA-style control returning -ENODATA for property N only — uevent already tolerates it — then revert.

## Alternatives this one run rules out

Class iteration vs LEDs vs notifier vs uevent-build vs property dispatch vs worker-core post-return; battery vs charger/usb psy identity; per-psy vs environment cause; the body-entry doubt. Not covered: internals of a named driver callback or notifier — that is the fix target once named, not now. No new clock/IRQ/scheduler captures.

Scope link: sustained PID1 execution remains the only active goal; naming this blocker unblocks helper completion → readonly MMC trial → Android17. BOOT/SYSTEM/DATA untouched, normal-Android-return check unchanged, charging optin and thermal protections untouched.