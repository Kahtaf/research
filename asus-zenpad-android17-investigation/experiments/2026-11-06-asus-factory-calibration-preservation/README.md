# ASUS factory calibration preservation

Question: preserve the exact factory Bluetooth and WLAN records before clean internal data migration. Status: two exact full-container copies match and device staging cleanup is verified; no formatting or calibration modification. Payloads stay private local and are excluded from Git/cloud/product bundles. Continue by verifying the private manifest and restoring exact records under the new OS before radio enablement.

ActualOEMcontainersare66B(BT)and514B(WLAN), withlogical64/512byteprefixes.
The2trailingbytesarepreserved,notinterpretedorregenerated. CurrentradioBT
providerincorrectlyrequires64Bfile. `integration/0001-accept-asus-bt-container.patch`
correctsitsread-onlyfile-sizecheckwhileAPIstillreturnslogicalsize64/count1.
ASan/UBSanhosttestagainstactualprivatefilepassedAPIread/close/unsupportedwrite;
truncated64,extra67andmulticastfixturesfailed. No actualcalibrationvalues printed.
See evidence/bt-container-compatibility.json andlogical-record-offset-check.json.
ARM32Androidbuild/hardwarevalidationremainsmainowner/parentwork.
