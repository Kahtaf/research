# Sensor BoardConfig path fix

Question: why did r6 Soong traverse /sepolicy?

Status: root cause observed in genuine generated variables. The sensor BoardConfig used an unavailable my-dir function at BoardConfig evaluation, producing an empty path. Prepared a one-line explicit device/asus/p00a/sensors path; active sources remain unchanged.

Outputs: source/BoardConfig.mk, source/sensor-board-path.patch, and evidence/r6-observed-path-failure.json.

Continuation: carry this exact delta into a separately recorded r7 under the original lifecycle lock. Require actual generated policy directories and manifest paths to be relative, present and correct before compiling. Preserve r6 logs, failed attempt and cache. No retry of r6, installclean or device operations.
