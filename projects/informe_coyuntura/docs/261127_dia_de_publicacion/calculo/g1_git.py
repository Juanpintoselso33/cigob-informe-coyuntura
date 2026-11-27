"""Por cada commit que tocó el snapshot: fecha_dato, valor y peso de cada indicador."""
import json, subprocess, sys, os
sys.path.insert(0, os.path.expanduser("~/.claude/tools"))
from claude_tqdm import tqdm
R = "/Users/juan/dev/trabajo/CIGOB/Analisis CIGOB"
F = "projects/informe_coyuntura/web/src/data/informe.json"
OUT = "/private/tmp/claude-501/-Users-juan-dev-trabajo-CIGOB-Analisis-CIGOB/e2f72bed-8017-4c00-a9c4-443e704dc741/scratchpad/fecha/git_snap.json"
log = subprocess.run(["git", "-C", R, "log", "--format=%H %cI %an", "--", F], capture_output=True, text=True).stdout.split("\n")
res = json.load(open(OUT)) if os.path.exists(OUT) else {}
bar = tqdm([l for l in log if l], desc="snapshots de git", unit="commit", goal="cuándo entró cada dato")
for l in bar:
    h, t, *a = l.split(" ")
    if h in res: continue
    try:
        d = json.loads(subprocess.run(["git", "-C", R, "show", f"{h}:{F}"], capture_output=True, text=True).stdout)
    except Exception:
        continue
    fila = {"t": t, "autor": " ".join(a), "gen": d.get("generated_at"), "period": d.get("period"), "ind": {}}
    for c, cv in (d.get("cinturones") or {}).items():
        for k, v in (cv.get("indicadores") or {}).items():
            if isinstance(v, dict):
                fila["ind"][k] = [c, v.get("fecha_dato"), v.get("valor"), v.get("peso_efectivo"), v.get("en_indice"), v.get("obtenido_en"), v.get("desactualizado")]
    res[h] = fila
    bar.log(f"{t[:10]} {len(fila['ind'])} ind")
json.dump(res, open(OUT, "w"))
print(len(res))
