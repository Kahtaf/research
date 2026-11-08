# Copy installation sources without enabling installation

Question: can the real final Android and stock rollback sources reach the ASUS
microSD without another card swap while the physical kernel diagnosis continues?

Status: parent-controlled USB ADB transfer. No recovery or internal partition
writes. Source trees contain chunks and original recovery only, with no mode,
manifest selector, or execution triggers. Existing PROBE.ID and STOCK.TXT remain.

`transfer.py` checks the exact tablet, boot, card marker and capacity, then copies
the staged source trees. It holds the shared device-operation lock and stops on
transport errors without retrying. `evidence/transfer.json` is authoritative.
ADB copy completion is not a device-side source hash qualification; the rescue
frontend still requires its complete reconstructed-image preflight before writes.

Continuation: inspect the terminal receipt. Never launch this one-shot script
again after a partial result. Reconcile any existing destination first. Installation
controls and recovery deployment remain separate, pending physical kernel startup.

USB transfer ended with sync-response EOF after stock2901files succeeded and2256/2508installfiles appeared. Original terminalreceipt is preserved. Fresh authenticated Wi-Fi guard verifiedsameboot/card; exact inventory found252missing files, no lengthmismatches, lastunacknowledged000652included amongmissing. Parentexplicitly reconciled andstarted separateone-shot resume_wifi.py foronly264241152remainingbytes. Existingfilesare untouched; no executioncontrols orinternalpartitionwrites. `evidence/wifi-resume.json` is authoritative for this second phase. No device sourcehash claim; frontendpreflight remains required.

Completed2026-11-07T14:09:50Z: Wi-Fi remainderexit0; sync and exact5,409sourcefilecount passed. No mode ortrigger present, reportdirectoriesempty. `evidence/wifi-resume.json` records UNARMED_SOURCE_COPY_COMPLETE. No live transferremains. The rescue whole-sourcehashpreflight is still required before installation.
