# UART-fixed kernel: independent USB PID1 report

Question: can the existing RAM-only USB reporter expose actual userspace execution with the UART-disabled kernel, independently of SD and retained-RAM header guards?

Status: preparing one p10-only installation and one USB recovery entry. Kernel and static PID1 remain byte-identical to their actual inputs. The corrected initrd length excludes the 512-byte MTK wrapper. Original BOOT/SYSTEM/userdata stay stock.

Outputs: evidence/physical-baseline.json, host identity absence, exact install receipt, recovery-entry.json and actual USB observation. Raw host inventory stays in ignored private. Continuation: admit only the fresh USB serial P499342cbf13bf044d4b655 and runtime-derived ASUS-PID1 product, optionally read its readonly FAT report, and verify return to a new stock boot. Missing USB is not proof of kernel nonexecution. No watchdog, clock, display or PMIC change.

## Physical result

One p10 install/full readback and one USB-acknowledged recovery entry completed. No expected USB descriptor or FAT report was observed, with zero host inventory errors. Healthy stock Android returned as `0c805b5e-a9af-42f1-a9db-d567509cf639`. Cached reboot-reason was collected over USB with Enforcing restored; numeric CPU0 remains in the ported PMIC ADC code and CPU1 is in candidate idle code. These samples do not establish a fault cause. No full-OS write. Source inspection identified late watchdog platform-driver registration as a candidate handoff issue; no watchdog change has yet been built or tested. Physical Power fallback is requested before such a trial because automatic reset may cease after earlier watchdog stop.
