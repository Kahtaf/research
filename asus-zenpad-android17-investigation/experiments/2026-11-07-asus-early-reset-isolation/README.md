# ASUS early reset isolation

Question: does the exact compiled 4.9 watchdog path explain the approximately 33-second recovery-to-stock return, and is there a defensible minimal boot fix?

Status: complete bounded source/ELF investigation; **no defensible fix or new candidate**. Actual candidate DT binding is correct. Exact ELF probe stops the watchdog. The legacy kicker is excluded despite its config boolean. A timeout before probe remains possible but unproved; the retained writer can silently refuse its strict header guards.

Important outputs:

- [Result and exact blocker](REPORT.md), including the single minimal independent observation contract.
- `evidence/offline-verification.json`: actual installed candidate DT/config checks, PASS.
- `evidence/vm/identity.json`: exact original vmlinux/build identity, source pins, present/absent symbols.
- `evidence/vm/disassembly-mtk_wdt_probe.txt` and other bounded disassembly; `evidence/stock-watchdog.disasm`: actual 4.9 and exact stock binary behavior.
- `source/stock-3.18/` and `evidence/vm/`: compact relevant source snapshots.
- `scripts/verify_delivery.py`: offline verification against preserved candidate; no device actions.

VM prefix `/srv/android/asus-early-reset-isolation-20261107`, accessed only through fixed `2026-11-06-asus-product-input-build-kit/scripts/remote.py`. No source or output tree was modified; no source copy was needed because no patch was justified. No build, diagnostic image, installer change or execution, device/card/ADB/root-helper action, raw/private log/factory/calibration/DATA/table access, other-owner process inspection/signals, active tree edit, cloud lifecycle action or subagent. Vendor-BPF worker untouched. Existing VM labels/disks and November 8 ~14:54 UTC auto-stop unchanged.

Continuation: root alone owns trials. Source cannot diagnose whether the candidate reaches watchdog probe or passes the retained header guard. The report states the exact prerequisite independent firmware/UART information; no speculative variant is proposed. Preserve physical Power fallback and the inherited 60-second PID1 normal reboot. Ultimate Android17 objective remains unproved.
