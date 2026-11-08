from bounded import ROOT,run
run(['python3',ROOT/'scripts/make_tests.py'],'evidence/extraction-status.txt')
run(['/usr/bin/clang','-std=gnu89','-O0','-g','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-Wno-declaration-after-statement','-fsanitize=undefined','-fno-sanitize-recover=all','-pthread',ROOT/'tests/contract.c','-o',ROOT/'tests/lifecycle-host'],'evidence/corrected-replay-compile.txt')
print(run([ROOT/'tests/lifecycle-host'],'evidence/corrected-replay-run.txt').decode())
