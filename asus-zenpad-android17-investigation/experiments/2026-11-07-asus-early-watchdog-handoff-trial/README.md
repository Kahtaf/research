# Earlier watchdog handoff: supervised recovery trial

Question: does earlier registration of the existing MTK watchdog driver let the kernel reach the RAM-only USB PID1 reporter?

Status: user explicitly confirmed nearby Power fallback for this trial. Preparing one p10-only install and USB recovery entry. Existing stop/start/restart behavior is unchanged; its earlier execution may remove automatic reset. BOOT/SYSTEM/userdata remain stock.

Outputs: evidence/nearby-power.json, fresh identity baselines, actual install/entry and USB observations. Continuation: observe descriptor/report and new stock return. If it stalls, ask user for the known 5–20-second Power fallback while the observer remains running. Do not repeat recovery entry.

## Physical result

One install/full readback/cleanup and one USB-acknowledged recovery entry completed. No expected USB descriptor appeared; zero inventory errors. Original Android returned automatically, boot `3525090a-4d53-4ec6-b704-7ba459bdc610`, explicitly confirmed kernel `3.18.35`. No Power fallback needed. Estimated pre-stock-kernel interval remains32.734–32.779seconds, so early watchdog registration did not change this outcome. Cached PCs alone do not establish the fault cause. BOOT/SYSTEM/DATA stay untouched. Next source instrumentation will identify logger refusal paths via distinct cached-PC addresses instead of speculative hardware changes; this is diagnostic-only. Full Android BOOT packaging can proceed separately with uninstrumented a49 kernel and remains unqualified.
