from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[1]
image="sha256:98529c9b6853b83c42527257027643890f7855478b30e30bf2e44132b33b5459"
cmd=["docker","--context","orbstack","run","--rm","--pull","never","--network","none","--read-only","--user","501:20","--cpuset-cpus","0","--cpus","1","--memory","1g","--memory-swap","1g","--pids-limit","32","--cap-drop","ALL","--security-opt","no-new-privileges","--tmpfs","/tmp:rw,size=64m","-v",str(R/"fixture")+":/work","-w","/work",image,"sh","tests/review_run.sh"]
(R/"evidence/independent-container-command.json").write_text(json.dumps(cmd,indent=2)+"\n")
with (R/"evidence/independent.stdout").open("w") as out,(R/"evidence/independent.stderr").open("w") as err:
 p=subprocess.run(cmd,stdout=out,stderr=err)
(R/"evidence/independent.exit").write_text(str(p.returncode)+"\n")
raise SystemExit(p.returncode)
