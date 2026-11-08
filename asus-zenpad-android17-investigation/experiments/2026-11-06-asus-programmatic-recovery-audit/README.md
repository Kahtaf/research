# Programmatic stock recovery audit

Question: can the repaired stock-kernel diagnostic be entered and exited without physical buttons while the user is away?

Status: entry mechanism identified; one-shot clearing and actual normal return remain unproved. No reboot, flash or other device operation was issued by this audit. User permits programmatic recovery if a reliable return can be established; the first new-kernel test remains deferred until physical fallback is available.

The original ASUS 3.18 GPL source registers arch_reset as its restart handler. The exact recovery string calls rtc_mark_recovery(), which sets the MT6323 RTC_FAC_RESET spare register to one. A normal restart does not explicitly clear this flag in that handler. The saved diagnostic's proven normal-reboot deadline uses RESTART without the recovery argument; its deadline source is unchanged in the repaired image. This supports a software entry route but does not prove the boot chain consumes the RTC request only once. The exact saved LK/preloader handling must still be traced; standard adb reboot recovery must not be assumed BCB-free without checking the stock userspace path.

Important outputs: evidence/source-pins.json; original full LK/preloader and p10 backups remain in the boot-access-audit spike. No boot flags, BCB, metadata, keys or security configuration were changed.

Continuation: trace the exact bootloader/preloader RTC recovery-bit read/clear path and stock reboot dispatch. If a bounded stock-kernel round trip can be reviewed with normal Android left intact, prepare an explicit unattended transport mode/contract reflecting the user's authorization; never assert the existing --supervised flag while no person is present. Otherwise defer this physical test and continue the build, backup, rescue, data and networking work offline.

Parent static continuation located the exact LK RTC selection and clear path.
See evidence/rtc-one-shot-static-findings.json and lk-recovery-control-flow.txt.
The predicate at41e08320 reads PDN1/0x802c and tests(mask0x30)==0x10;
selection41e03bb6 cachesmode2 atglobal41e68500. Maincallsselectionat41e031a8
beforetheRTCcheckat41e031e8. The normalcontinuingRTCbranch41e07fee..08020
clearsbit4withmaskffef, writesPDN1, commitsRTCandreturns. Thecommithelper
writesRTCWRTGR803c andpollsbusy; no timeoutapparent. This is exactbinary/source
evidence, not end-to-endruntime or PMICwrite proof. Direct RESTART2 recovery
wouldavoidthestill-unauditedAndroiduserspaceBCBpath; itneedsfixednativehelper,
BCB/cache-command precheck, truthfulunattended-stock-onlycontract andparentreview.
No selector/flash/rebootwasexecuted. Firstnewkernelphysicaltrialstaysheld.
