from pathlib import Path
import shutil
r=Path(__file__).resolve().parents[1]
w=r/'stagedpatches/kernel-input'
w.mkdir(exist_ok=True)
for src in ['asus-3.18','kernel-4.9']:
 p=r/'sourceinputs'/src/'drivers/misc/mediatek/connectivity'
 shutil.copytree(p,w/'drivers/misc/mediatek/connectivity',dirs_exist_ok=True)
