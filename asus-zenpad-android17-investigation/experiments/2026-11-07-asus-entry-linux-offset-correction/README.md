# Measured correction: Linux retained-area lower bound

Question: does the entrywriter incorrectly treat stock default0x200 as a universal Linuxarea minimum?

Status: parentstagedexactonecomparisoncorrectioninassemblyandmatchingCguard; no build or device action here. Physicalstockcaptureprovedearlyentry, validFDTx04e000000,EL2,MMUoff/Dcacheoff,andrefusalID114 at derivedlinuxoff<0x200. Shippedstockinitializer f414f8..f41540 uses0x200asfallback only; a valid nonzeroLKrecord derivesoff_lk+2*align64(sz_lk) withoutsuchminimum.

Correction: keepdefault0x200unchanged; requirederivedarea at or above the64-byteheader. ExistingcompletePL/LKextent/nonoverlap/boundschecksremainexact. Source/correction.patch changes onecompareandoneCbound. Evidence/correction-receipt.json recordsactualvaluesandpins.

Next: one stock positivecontrol must show bothactualentrymagic/statuscommit andactualfreshtextreadback, notconstantlateUUIDalone. Thenonejustified4.9build/trial withsamecorrection. No driverwork/experiment3 untilfresh4.9proof.
