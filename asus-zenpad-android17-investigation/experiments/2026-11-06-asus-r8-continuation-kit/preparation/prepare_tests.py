from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R.parent/'2026-11-06-asus-r7-continuation-kit/tests'
s=(O/'test_continuation.py').read_text();header=s[:s.index('class ContinuationTests')];tail=s[s.index('class PathTests'):]
(R/'tests/test_continuation.py').write_text(header+tail)
for n in ['test_provenance.py']:
 p=R/'tests'/n;p.write_text((O/n).read_text().replace('r7','r8'))
p=R/'tests/test_outputs.py';s=p.read_text().replace("self.assertIn('m -j8 bootimage systemimage', script)","self.assertIn('run_m bootimage systemimage', script)").replace("self.assertIn('m -j8 ', script)","self.assertIn('m showcommands -j8 ', script)");p.write_text(s)
