from pathlib import Path
import importlib.util,sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder_remote',ROOT.parent/'2026-11-06-asus-product-input-build-kit/scripts/remote.py');remote=importlib.util.module_from_spec(spec);spec.loader.exec_module(remote)
script=Path(sys.argv[1]);out=remote.run(script.read_text());(ROOT/'evidence'/(script.stem+'.txt')).write_text(out);print(out)
