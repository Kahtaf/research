#!/usr/bin/env python3
"""Run only inside this spike's isolated builder prefix; never invoke Android builds."""
from pathlib import Path
import hashlib, json, os, secrets, subprocess, sys, zipfile

R = Path(__file__).resolve().parents[1]
assert str(R) == '/srv/android/asus-wifi-adb-apk-20261107'
os.chdir(R)
os.umask(0o077)
os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
JDK = Path('/srv/android/lineage24/prebuilts/jdk/jdk21/linux-x86')
SDK = Path('/srv/android/lineage24/prebuilts/sdk')
BIN = SDK / 'tools/linux/bin'
JAR = SDK / '37.0/public/android.jar'
os.environ.update(JAVA_HOME=str(JDK), PATH=str(JDK/'bin')+':/usr/bin:/bin',
                  TMPDIR=str(R/'build'), OMP_NUM_THREADS='1',
                  JAVA_TOOL_OPTIONS='-Xmx256m -XX:ActiveProcessorCount=1')
for p in ['build', 'build/classes', 'build/dex', 'artifacts', 'evidence']:
    (R/p).mkdir(exist_ok=True)
required = [JDK/'bin/javac', JDK/'bin/java', JDK/'bin/keytool', JAR,
            BIN/'aapt2', BIN/'zipalign', SDK/'tools/linux/lib/apksigner.jar', SDK/'tools/linux/lib/d8.jar']
for p in required:
    if not p.is_file(): raise SystemExit('Missing existing tool: '+str(p))
H = lambda b: hashlib.sha256(b).hexdigest()
expected = {'mtk-su64':'328632e853ff6427af9f35cb83a91d9e960f35d01188ee66d46ae9c7ce7c7827',
            'root-actions.sh':'75bc4f393a44c8dfb4663b8da53e7986e1dca47ddf6b0c18472f39b2c523e05b'}
for n, h in expected.items(): assert H((R/'assets'/n).read_bytes()) == h
logs = []
def run(cmd, timeout=90):
    p = subprocess.run([str(x) for x in cmd], capture_output=True, text=True, timeout=timeout)
    logs.append({'command':[str(x) for x in cmd], 'returncode':p.returncode,
                 'stdout':p.stdout, 'stderr':p.stderr})
    (R/'evidence/build-log.json').write_text(json.dumps(logs, indent=2)+'\n')
    if p.returncode: raise RuntimeError(p.stderr[-3000:] or p.stdout[-3000:])
    return p.stdout

# Verify ignore rules before creating the disposable development signing material.
assert '/private/' in (R/'.gitignore').read_text().splitlines()
run(['git', '-c', 'init.defaultBranch=main', 'init', '-q'])
assert run(['git','check-ignore','private/development.p12']).strip() == 'private/development.p12'
private = R/'private'
private.mkdir(mode=0o700, exist_ok=True)
os.chmod(private, 0o700)
password = private/'password'
key = private/'development.p12'
if not key.exists():
    password.write_text(secrets.token_urlsafe(32)+'\n')
    os.chmod(password, 0o600)
    run([JDK/'bin/keytool','-genkeypair','-noprompt','-keystore',key,
         '-storetype','PKCS12','-storepass:file',password,'-keypass:file',password,
         '-alias','development','-keyalg','RSA','-keysize','2048','-validity','3650',
         '-dname','CN=ASUS WiFi ADB DEVELOPMENT,OU=Disposable Development,O=Local Owner,C=CA'])
assert key.is_file() and password.is_file()
os.chmod(key, 0o600)
final = R/'artifacts/asus-wifi-adb-development.apk'
assert sys.argv[1:] in ([], ['--verify-existing'])
if not sys.argv[1:]:
    run([JDK/'bin/javac','-source','8','-target','8','-bootclasspath',JAR,
         '-encoding','UTF-8','-d','build/classes',*sorted((R/'source').rglob('*.java'))])
    run([JDK/'bin/java','-Xmx256m','-XX:ActiveProcessorCount=1','-cp',SDK/'tools/linux/lib/d8.jar',
         'com.android.tools.r8.D8','--release','--thread-count','1','--min-api','24','--lib',JAR,
         '--output','build/dex',*sorted((R/'build/classes').rglob('*.class'))])
    run([BIN/'aapt2','link','--manifest','AndroidManifest.xml','-I',JAR,
         '--min-sdk-version','24','--target-sdk-version','24','-A','assets','-o','build/base.apk'])
    with zipfile.ZipFile('build/base.apk') as base, zipfile.ZipFile('build/unsigned.apk','w',zipfile.ZIP_DEFLATED) as apk:
        for info in base.infolist(): apk.writestr(info, base.read(info.filename))
        apk.write('build/dex/classes.dex','classes.dex')
    run([BIN/'zipalign','-f','4','build/unsigned.apk','build/aligned.apk'])
    run([JDK/'bin/java','-jar',SDK/'tools/linux/lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','development',
         '--ks-pass','file:'+str(password),
         '--min-sdk-version','24','--v1-signing-enabled','true','--v2-signing-enabled','true',
         '--v3-signing-enabled','false','--v4-signing-enabled','false','--out',final,'build/aligned.apk'])
verification = run([JDK/'bin/java','-jar',SDK/'tools/linux/lib/apksigner.jar','verify','--verbose','--print-certs','--min-sdk-version','24',final])
assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in verification
manifest = run([BIN/'aapt2','dump','badging',final])
assert "package: name='com.kahtaf.asuswifisetup'" in manifest
assert ("sdkVersion:'24'" in manifest or "minSdkVersion:'24'" in manifest) and "targetSdkVersion:'24'" in manifest
assert 'uses-permission:' not in manifest
assert "launchable-activity: name='com.kahtaf.asuswifisetup.MainActivity'" in manifest
xml = run([BIN/'aapt2','dump','xmltree',final,'--file','AndroidManifest.xml'])
with zipfile.ZipFile(final) as apk:
    assert any(n.startswith('META-INF/') and n.endswith('.SF') for n in apk.namelist())
    assert any(n.startswith('META-INF/') and n.endswith('.RSA') for n in apk.namelist())
    assert 'classes.dex' in apk.namelist() and apk.read('classes.dex').startswith(b'dex\n')
    for n,h in expected.items(): assert H(apk.read('assets/'+n)) == h
    assert not any('private/' in n or n.endswith(('.p12','.jks','.java')) for n in apk.namelist())
    entries = [{'path':i.filename,'bytes':i.file_size} for i in apk.infolist()]
result = {'status':'SIGNED_PACKAGING_VERIFIED_APP_CONTEXT_UNPROVED',
          'apk':{'name':final.name,'bytes':final.stat().st_size,'sha256':H(final.read_bytes())},
          'assets_sha256':expected,'entries':entries,'min_sdk':24,'target_sdk':24,
          'permissions':[], 'sdk24_v2_verified':True,'v1_signature_entries_present':True,'device_operations':0,
          'builder_prefix':str(R), 'tool_paths':[str(p) for p in required],
          'signing_private_mode':oct(private.stat().st_mode & 0o777),
          'key_ignored':True,'parallel_builds':1}
(R/'evidence/verification.json').write_text(json.dumps(result,indent=2)+'\n')
(R/'evidence/apksigner.txt').write_text(verification)
(R/'evidence/manifest-badging.txt').write_text(manifest)
(R/'evidence/manifest-tree.txt').write_text(xml)
print(json.dumps(result,indent=2))
