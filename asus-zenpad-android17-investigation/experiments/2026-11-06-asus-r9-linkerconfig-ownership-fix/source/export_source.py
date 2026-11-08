from pathlib import Path
import json,base64
R=Path('/srv/android/asus-r9-linkerconfig-ownership-fix-20261106');root=R/'inputs/linkerconfig-before';names=['contents/namespace/systemdefault.cc','contents/namespace/vendordefault.cc','contents/namespace/system.cc','contents/section/vendor.cc','contents/section/sectionbuilder.cc','contents/include/linkerconfig/namespacebuilder.h','contents/include/linkerconfig/context.h','modules/section.cc','modules/include/linkerconfig/namespace.h','main.cc','Android.bp','contents/tests/Android.bp','contents/tests/configuration/p00a_legacy_graphics_test.cc','modules/include/linkerconfig/apex.h','modules/configparser.cc']
d={str(p.relative_to(R)):base64.b64encode(p.read_bytes()).decode() for p in [root/n for n in names] if p.is_file()}
# Include public source project tree (under 2MiB) for local precise review.
for p in root.rglob('*'):
 if p.is_file():d[str(p.relative_to(R))]=base64.b64encode(p.read_bytes()).decode()
for p in [R/'evidence/frozen-source.json',R/'inputs/graphics-r6/linkerconfig.patch',R/'inputs/graphics-r6/source-manifest.json']:d[str(p.relative_to(R))]=base64.b64encode(p.read_bytes()).decode()
print(json.dumps(d))
