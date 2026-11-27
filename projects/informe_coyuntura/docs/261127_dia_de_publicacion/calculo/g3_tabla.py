import re
import json, datetime as dt, calendar
L = json.load(open("llegadas.json")); dias = [dt.date.fromisoformat(d) for d in json.load(open("dias_con_snapshot.json"))]
snap = json.load(open("../../../../../../../Users/juan/dev/trabajo/CIGOB/Analisis CIGOB/projects/informe_coyuntura/web/src/data/informe.json".replace("../../../../../../..",""))) if False else None
def norm(fd):
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", fd)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else fd
def fin(fd):
    fd = norm(fd); y, m = int(fd[:4]), int(fd[5:7])
    return dt.date(y, m, calendar.monthrange(y, m)[1])
def prev_dia(d):
    ant = [x for x in dias if x < d]; return ant[-1] if ant else None
for k, v in sorted(L.items(), key=lambda x: x[1]["cinturon"]):
    p = v["primera"][:10]; filas = []
    v["llegadas"] = [x for x in v["llegadas"] if re.match(r"^\d{4}-\d{2}", x[0])]
    for fd, t in v["llegadas"]:
        d = dt.date.fromisoformat(t[:10])
        if t[:10] <= p: continue           # ya estaba en el primer snapshot
        lo = prev_dia(d)
        filas.append(f"{fd[:7]}→{t[5:10]}(+{(d-fin(fd)).days},desde {(lo-fin(fd)).days+1 if lo else '?'})")
    if filas and all('+-' not in f for f in filas): print(f"{v['cinturon'][:5]} {k}: " + "  ".join(filas[-8:]))
