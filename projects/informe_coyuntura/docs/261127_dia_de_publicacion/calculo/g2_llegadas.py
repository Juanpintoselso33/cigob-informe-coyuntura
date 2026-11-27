"""Llegada de cada período de cada indicador: primer snapshot (generated_at, hora ART) que lo trae."""
import json, datetime as dt
from collections import defaultdict
g = json.load(open("git_snap.json"))
ART = dt.timezone(dt.timedelta(hours=-3))
def ts(s):
    s = s.replace("Z", "+00:00")
    x = dt.datetime.fromisoformat(s)
    if x.tzinfo is None: x = x.replace(tzinfo=dt.timezone.utc)
    return x.astimezone(ART)
snaps = []
for h, v in g.items():
    t = ts(v["gen"] or v["t"])
    snaps.append((t, h, v))
snaps.sort(key=lambda x: x[0])
# fechas de snapshot (días con al menos un snapshot)
dias = sorted({s[0].date() for s in snaps})
json.dump([d.isoformat() for d in dias], open("dias_con_snapshot.json", "w"))
hist = defaultdict(list)   # ind -> [(t, fecha_dato)]
for t, h, v in snaps:
    for k, (c, fd, val, peso, en, obt, des) in v["ind"].items():
        if fd: hist[k].append((t, fd[:10], c))
lleg = {}
for k, xs in hist.items():
    vistos = {}
    for t, fd, c in xs:
        if fd not in vistos: vistos[fd] = t
    # una fecha_dato «llega» si es mayor que todas las anteriores (descarta revisiones hacia atrás)
    orden = sorted(vistos.items(), key=lambda x: x[1])
    mx = ""; out = []
    for fd, t in orden:
        if fd > mx:
            out.append((fd, t.isoformat())); mx = fd
    lleg[k] = {"cinturon": xs[-1][2], "primera": xs[0][0].isoformat(), "llegadas": out}
json.dump(lleg, open("llegadas.json", "w"), ensure_ascii=False, indent=0)
print(len(dias), "días con snapshot de", dias[0], "a", dias[-1])
huecos = [(dias[i], dias[i+1]) for i in range(len(dias)-1) if (dias[i+1]-dias[i]).days > 1]
print("huecos:", [(a.isoformat(), (b-a).days-1) for a, b in huecos])
