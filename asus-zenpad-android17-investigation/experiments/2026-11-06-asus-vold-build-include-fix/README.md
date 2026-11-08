# SDK37 vold compile include fix

Question: does explicitly including algorithm clear the actual r5 PublicVolume.cpp
compile failure without changing behavior or active sources?

Status: isolated original compile reproduces the exact failure; adding only the
algorithm include compiles successfully with the genuine SDK37 action. Active
sources remain unchanged. Original full build is terminal
with exit1 at21:15:32UTC; no final BOOT/SYSTEM report. No active source edits or
new full-build launch occurred here.

Outputs: exact original/modified source, patch, compiler invocation and isolated
object/diagnostic receipts belong here. Continue by checking actual before/after
compilation, then bind the additive fix into a new parent-reviewed product kit.
Preserve original r5 logs and cached outputs; no installclean/restart.

The receipt is [evidence/receipt.json](evidence/receipt.json), and the exact
one-line patch is [artifacts/include-algorithm.patch](artifacts/include-algorithm.patch).
The successful output is ThinLTO bitcode, not a linked vold executable. Actual
product linking and runtime remain pending.
