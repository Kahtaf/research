# Early UART disabled hardware trial

Question: does removing the unused early serial console bypass the hardware-linked UART read and allow the 4.9 retained checkpoints or SD report?

Status: preparing one recovery-only install and one USB recovery entry. Baseline OS remains stock. The cached UART PC is a concrete candidate, with capture epoch and exclusive causality unproven.

Outputs: evidence/physical-baseline.json, exact installation receipt, recovery-entry.json, and USB collector result. Continuation: collect one normal return and inspect actual v2 markers/report; no blind retry or unrelated hardware changes.

## Physical result

One p10 install/full readback/cleanup succeeded; one USB recovery request was acknowledged. Stock Android returned healthy as `de110e8a-fd75-41ae-8f90-6ac881b96085`. Complete USB log has no v2 checkpoint and SD report remains absent. Cached CPU PCs changed and resolve in the exact new image to `disp_irq_handler+0x530` and `asus_p00a_pmic_adc+0x154`; these are execution candidates, not independent epoch proof or evidence that these functions caused a fault. Estimated time before the new stock kernel is 32.906–32.963 seconds, shorter than PID1’s nominal 60-second wait. No full-OS writes. Next source question is firmware-watchdog handoff ordering; no blind display/PMIC disabling. See evidence/physical-result.json.

The ~33-second interval alone cannot identify a watchdog reset: physical timebase and deliberate PID1 return are not observed. No watchdog/clock change is justified from it. Next minimal discriminator is packaging this exact kernel with the existing RAM-only USB reporter, which requires neither SD nor retained-log header. No new kernel build or unrelated hardware change is needed.
