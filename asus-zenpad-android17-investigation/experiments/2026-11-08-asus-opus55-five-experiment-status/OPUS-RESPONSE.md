# Status: Android 17 port, day 3

**Are we still on 3 of 5?** Mostly yes, with a caveat about numbering. The saved plan has **six** gates, not five. We haven't recovered the exact five-item list you remember, so the grouping below is a reconciled view, not the original document.

| Work package (reconciled) | Original gates | Status |
|---|---|---|
| 1. Reporting | Gate 1 | **Closed.** The USB reporter mismatch and the wrong 0x200 guard were fixed, and stock positive controls check out. |
| 2. Entry + initialization | Gates 2–3 (partly 4) | **Closed for the stages reached:** pre-MMU entry, paging, setup_arch, init IRQ and timer init all returned, and a RAM PID1 reports uname 4.9.337. This shows the kernel boots. It does not show the kernel keeps running. |
| 3. Stable RAM runtime | Rest of gates 3–4 | **Open. This is where we are.** No 2M compute completion, no progress after the IRQ, no alarm wakeup, no sustained runtime. |
| 4. Storage + recovery | Gate 5 | **Open.** Only the early MMC hosts come up. Partitions, stock hash verification and an independent 4.9 rescue path aren't established. Diagnostic return to stock works. |
| 5. Android first boot | Gate 6 | **Not started on hardware.** The images are built and validated on the host, and early services run in a VM. Nothing has been flashed. |

So: package 3 of 5, which is gates 3–4 of 6. No percentage or ETA is justified.

**Useful work vs. scope drift:** Calibrating the reporting and proving entry were essential. The worktrace was useful: it pointed at the battery uevent → AUXADC → PMIC path. After that it drifted. Nohlt, single-CPU, direct clock, the RDMA IRQ skip, the counter-delay variants and the pwrap backstop each cost effort and none of them closed the gate. These variant loops have to end now. No retuning and no repeats.

**The one pending trial (battery uevent omission):**
- **Smallest meaningful positive:** one cold record that shows the omission took effect *and* the worker's uevent returned, *and* normal compute or post-IRQ progress happens. That supports the idea that this specific work is the trigger. It does **not** find the root cause and it does **not** close gate 3. A fast 2M loop is not 30-second stability.
- **Negative or unknown:** no progress, or the record is missing or ambiguous.
- **Stop rule:** one build, one trial. If the result is negative or unknown, stop and reassess as a whole. Don't add variants. If positive, record it as progress and still treat gate 3 as open.

**Plain-language status:**
> "Your phone is safe: stock Android still works and only the recovery partition has changed. We've proven our reporting is reliable and that the new Linux 4.9 kernel genuinely starts and runs its first program. What isn't working yet is keeping it running. It stalls soon after starting, and the evidence points to something in the battery or power-chip handling. We tried too many small variations on this, and that's over now. One focused test is ready. Whatever it shows, we'll stop and decide the next step deliberately rather than keep tinkering. Storage, recovery and actually flashing Android 17 all come after this hurdle."