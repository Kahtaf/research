#!/usr/bin/env python3
"""Allowlist-only local staging. Never reads calibration records or contacts a VM."""
import hashlib, json, pathlib, shutil
ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
STOCK = WORKSPACE/'2026-11-05-asus-latest-android-feasibility'
DEVICE = ROOT/'staged/device/asus/p00a/connectivity'
FILES = {
 'WIFI_RAM_CODE_8163':'vendor/firmware/WIFI_RAM_CODE_8163',
 'WMT_SOC.cfg':'vendor/firmware/WMT_SOC.cfg',
 'ROMv2_lm_patch_1_0_hdr.bin':'vendor/firmware/ROMv2_lm_patch_1_0_hdr.bin',
 'ROMv2_lm_patch_1_1_hdr.bin':'vendor/firmware/ROMv2_lm_patch_1_1_hdr.bin',
}
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 manifest = []
 for name, rel in FILES.items():
  src=STOCK/'evidence/device'/rel
  dest=DEVICE/'firmware'/name
  dest.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(src,dest)
  manifest.append({'source':str(src.relative_to(WORKSPACE)), 'staged':str(dest.relative_to(ROOT)), 'sha256':digest(src), 'bytes':src.stat().st_size, 'install':'vendor/firmware/'+name, 'provenance':'Previously captured stock ASUS device vendor firmware; not per-device NVRAM', 'license':'Proprietary ASUS/MediaTek; redistribution permission not established; local device bring-up only'})
 for name in ['libbt-vendor.so','libbluetooth_mtk.so']:
  src=STOCK/'evidence/device/vendor/lib'/name
  dest=ROOT/'staged/deferred-bluetooth/blobs/lib'/name
  dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dest)
  manifest.append({'source':str(src.relative_to(WORKSPACE)), 'staged':str(dest.relative_to(ROOT)), 'sha256':digest(src), 'bytes':src.stat().st_size, 'install':None, 'provenance':'Captured stock ELF32 library; reference inputs only, NOT included in base product', 'license':'Proprietary ASUS/MediaTek; redistribution permission not established'})
 (ROOT/'evidence/stock-input-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Staged',len(manifest),'allowlisted non-personal firmware/library files')
if __name__=='__main__': main()
