# Recovery USB pin monotonic-age fix

Question: can a host clock correction extend the exact recovery deployment pin beyond180elapsed seconds?

Status: parent implementing the independently reproduced P1 in a separate source revision. Original adapter/review/artifacts unchanged. No device actions.

Outputs: source/adapter.py and regression tests, source diff/pins and test evidence.

Continuation: require both wall and host-boot-bound monotonic pin ages at loading and actual nested dispatch, plus the existing contract deadline. Preserve historical install linkage without treating an old pin as fresh. Run both reviewer regressions and original suite offline; parent review exact new code before any physical session. No physical GO.
