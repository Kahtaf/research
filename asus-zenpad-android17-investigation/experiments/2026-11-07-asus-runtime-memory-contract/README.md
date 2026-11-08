# Experiment 2: stock runtime memory contract

Question: what memory reg does the current working stock kernel expose after LK handoff, and is the flattened original DT available?

Status: one read-only observation being collected. This is not proof of the failed4.9 x0 FDT. No build, image or device mutation. Raw DT values, if collected, stay private; public output is limited to memory/retention geometry. Continue by comparing observed runtime bank with packaged placeholder and the exact-bank entry guard.


Result: current stock memoryreg is0000000040000000000000007d600000, cells2/2, bank[0x40000000,0xbd600000), matchingR2. /sys/firmware/fdt is not readable by shell; no root escalation for this check. This is current unflattened stockDT, not directpre-MMUx0evidence. Parent admits using the observedreg in a fixture-only stock-control admission replay, while actual stockcandidate retains itsoriginalmemoryproperty andunchangedguard. This removes the packaged-placeholder-only preparationstop; it does not prove physicalcontroladmission or4.9entry. See evidence/parent-runtime-admission.json.
