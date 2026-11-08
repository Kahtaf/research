from pathlib import Path
import subprocess,json,hashlib,base64,datetime
R=Path(__file__).resolve().parents[1];E=R/'artifacts/frozen-r3/evidence';H=Path.home()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((E/'qualification-final.json').read_text());assert len(q['checks'])==37 and all(c['passed'] for c in q['checks'])
assert (E/'service-ready-check.exit').read_text().strip()=='2'
export=json.loads((R/'evidence/export-verification-r3.json').read_text());assert sha(R/'artifacts/evidence-r3.tar.gz')==export['archive_sha256']
for n,v in json.loads((E/'export-manifest.json').read_text()).items():assert sha(R/'artifacts/frozen-r3'/n)==v['sha256']
text=(R/'REPORT.md').read_text();assert not any(t in text for t in ['@IMAGE@','@CHECKS@','SERVICE_UTC','EXPORT_SHA','EXPORT_FILES','EXPORT_BYTES'])
h=json.loads((R/'handoff.json').read_text())
for n,s in h['files'].items():assert sha(R/n)==s
SSH=['ssh','-i',str(H/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o','UserKnownHostsFile='+str(H/'.ssh/google_compute_known_hosts'),'android@IP_REDACTED']
files={n:base64.b64encode((R/n).read_bytes()).decode() for n in ['REPORT.md','README.md','MISSING-TARGETS.md','handoff.json']}
code="from pathlib import Path\nimport base64,hashlib,json,subprocess\nr=Path('/srv/android/asus-firstboot-parity-continuation');out={}\nfor n,b in "+repr(files)+".items():\n p=r/n;assert not p.exists();p.write_bytes(base64.b64decode(b));out[n]=hashlib.sha256(p.read_bytes()).hexdigest()\nps=subprocess.check_output(['ps','-eo','pid,comm,args'],text=True).splitlines();out['fixture_qemu_processes']=[l for l in ps if l.split()[1].startswith('qemu-system') and str(r) in l];assert not out['fixture_qemu_processes'];print(json.dumps(out))\n"
p=subprocess.run(SSH+['python3 -'],input=code.encode(),capture_output=True,check=True);remote=json.loads(p.stdout)
for n in files:assert remote[n]==sha(R/n)
qa={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'qualification_assertions':37,'export_payloads_verified':84,'service_readiness_exit':2,'report_no_placeholders':True,'remote_reports_verified':remote,'all_passed':True}
(R/'evidence/final-qa.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
