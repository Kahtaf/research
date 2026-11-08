from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parents[1];OLD=R.parent/'2026-11-06-asus-r8-continuation-kit'
for p in (OLD/'scripts').glob('*'):
 if p.is_file():shutil.copyfile(p,R/'scripts'/p.name)
# Copy exact r8 scripts; alter only the new revision coordinator. Compiler/image
# validators retain their strict gates until a sound cache lineage is available.
shutil.copyfile(OLD/'scripts/continuation.py',R/'scripts/r8_continuation.py')
p=R/'scripts/integrate.py';s=p.read_text()
s=s.replace("need(plan['revision'] == 'r8'", "need(plan['revision'] == 'r9'")
s=s.replace("read(plan['r7_staged_receipt'])['product_after'], 'Already-integrated r7 device preimage mismatch'", "read(plan['staged_receipt'])['product_after'], 'Already-integrated r8 device preimage mismatch'")
s=s.replace("    continuation_inputs(plan)\n    need(manifest(plan['device'])", "    continuation_inputs(plan)\n    from artifact import check_preimage, REL\n    check_preimage(safe(plan['aosp'],REL))\n    need(manifest(plan['device'])",1)
s=s.replace("    live = native_processes(plan)\n", "    from cache_lineage import require_ready\n    require_ready(plan)\n    live = native_processes(plan)\n",1)
# No source writes occur without this hard gate, even after approval.
s=s.replace(".reviewed-r8-tmp", ".reviewed-r9-tmp")
p.write_text(s)
p=R/'scripts/build.sh';s=p.read_text().replace('asus-reviewed-build-kit/r8','asus-reviewed-build-kit/r9').replace('full-build-r8','full-build-r9');s=s.replace('python3 -B "$kit/scripts/check_launch.py" "$kit"','python3 -B "$kit/scripts/cache_lineage.py" "$kit"\npython3 -B "$kit/scripts/check_launch.py" "$kit"');p.write_text(s)
# Keep validators byte-exact. Continuation apply independently records artifact.
print('Prepared inherited scripts; r9 remains fail-closed on incomplete cache lineage')
