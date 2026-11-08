from pathlib import Path
import subprocess,json,base64,sys
S=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(S/'scripts'))
ssh=['ssh','-i',str(Path.home()/'.ssh/asus_p00a_android17'),'-o','IdentitiesOnly=yes','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=compute.8549823276971553556','-o',f'UserKnownHostsFile={Path.home()}/.ssh/google_compute_known_hosts','android@IP_REDACTED']
paths=['drivers/misc/mediatek/sensors-1.0/hwmon/sensor_attributes/sensor_attr.c','drivers/misc/mediatek/sensors-1.0/accelerometer/accel.c','drivers/misc/mediatek/sensors-1.0/accelerometer/Makefile','drivers/misc/mediatek/sensors-1.0/accelerometer/Kconfig','arch/arm64/configs/asus_p00a_defconfig']
script='from pathlib import Path\nimport json,base64\nK=Path("/srv/android/asus-build-continuation/kernel")\npaths='+repr(paths)+'\nprint(json.dumps({p:base64.b64encode((K/p).read_bytes()).decode() for p in paths if (K/p).exists()}))\n'
r=subprocess.run(ssh+['python3 -'],input=script.encode(),capture_output=True,check=True)
for p,v in json.loads(r.stdout).items():
 f=S/'source/kernel-preimages'/p; f.parent.mkdir(parents=True,exist_ok=True); f.write_bytes(base64.b64decode(v))
print('Fetched',len(json.loads(r.stdout)),'preimages')
