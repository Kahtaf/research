# Bounded source comparison

ASUS GPL3.18.22 is a reference, not exact shipped3.18.35 source. Its `mt_wdt.h` names request bit0 SPM_THERMAL, bit1 SPM_SCPSYS and bit18 THERMAL; request IRQ bits select interrupt vs reset. The actual4.9 probe enables0/18 and selects reset for both. Stock's MT8163 SPM init also calls `wd_spmwdt_mode_config(WD_REQ_EN, WD_REQ_RST_MODE)`; its thermal driver disables/re-enables direct thermal routing around configuration. These are legitimate protection paths; presence alone is no fault proof.

Stock `/proc/wdk` read handler reports mode/interval/timeout/enable software variables only, not RGU request registers. No live read or write of that interface occurred. Broad stock-vs-port audit stops here; no policy delta staged.
