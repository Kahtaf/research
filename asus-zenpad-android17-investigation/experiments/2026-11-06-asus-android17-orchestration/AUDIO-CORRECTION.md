# Stock speaker topology correction

The completed public-source/binary investigation in ../2026-11-06-asus-stock-speaker-topology-reconcile/report/HANDOFF.md supersedes the earlier claim that MTK_SPEAKER makes the whole stock external speaker switch inert. The generic pulse block is guarded, but ASUS's GPIO28 gate is outside that guard. Public shipping boot instructions and DT agree with that path.

The combined kernel adds AW8737S GPIO24 pulse code, omits the ASUS GPIO28 gate, and its exact appended DT lacks switch-mode-delay. Its init path therefore returns EINVAL before codec registration under that DT. This is a source/binary prediction, not a physical observation of pulses or proof of every possible bootloader DT fixup. GPIO24 also has a described USB consumer. Disabling AW alone permits the counterfactual registration path but does not restore stock topology.

A new isolated Sol source task stages only supportable stock-software-contract restoration with checked Linux4.9 GPIO handling. Fitted amp/electrical identity, active stock-route selection and physical sound remain unqualified. HAL routes stay unqualified; no gain, delay, pulse pattern or calibration is invented. Existing kernels, probes and build kit stay unchanged. The separate PCM patch remains excluded after its automatically rejected review; this is not a retry of that work.

Live stock ownership at00:34:13UTC confirms the controller-relativeGPIO28 request `spkamp-en-gpio` low andGPIO24 `USB_DPN_SEL` high (debugchipbase869; global897/893). Receipt: ../2026-11-06-asus-stock-gpio-ownership/evidence/observation-1794011653421961000.json. No GPIO/pinctrl setting was changed. This adds ownership evidence, not fitted-component/active-route acceptance.
