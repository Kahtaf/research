# Correct the timer-interrupt diagnostic format

Question: can the prepared runnable timer observation consume the actual selected Linux4.9 interrupt table?

Status: parent caught a parser-only issue before any device trial. GICv2 and the selected Level field were missing from the original parser. New source changes only that bounded parser plus a fresh helper UUID; all other reviewed new functions and observation bounds remain unchanged. Original candidate, logs and evidence are preserved. One corrected helper compile and package are pending. No physical actions by this spike yet.

No kernel, driver, bootarg, watchdog, timer configuration or hardware DT change. Parent owns nearby Power availability, installation and one physical trial.

## Candidate ready

One corrected helper compile exit0, source scope and focused actual-producer parser cases passed. Exact kernel/ramdisk packaging preservation passed and actual default parent PLAN passed. Initramfs 256373B stays below258055B. Candidate SHA256 13033865fe5c88952efe2d5e429246a76a08689be604fb89a4776afa990c4ab8; fullp10 88f79cc02d71bfe0708d6be77d66d06d3107befcee3d5d0225ecc8134942f617. VM is verified TERMINATED. Original uncorrected candidate was never installed. Parent owns one current trial; no other variant prepared.
