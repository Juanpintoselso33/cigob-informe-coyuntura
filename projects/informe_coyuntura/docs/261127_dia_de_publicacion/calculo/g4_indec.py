import re, json, glob
MESES = {m: i+1 for i, m in enumerate("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split())}
out = []
for f in sorted(glob.glob("cal/*.lay")):
    y = int(re.search(r"(\d{4})", f).group(1))
    for page in open(f).read().split("\f"):
        lines = page.split("\n")
        # columna derecha: posición del encabezado de mes de la derecha
        cut = None
        for l in lines:
            ms = [(m.start(), m.group(1)) for m in re.finditer(r"\b(Enero|Febrero|Marzo|Abril|Mayo|Junio|Julio|Agosto|Septiembre|Octubre|Noviembre|Diciembre)\b(?! de)", l)]
            if len(ms) == 2: cut = ms[1][0] - 2; break
        cols = [[l[:cut] if cut else l for l in lines]] + ([[l[cut:] for l in lines]] if cut else [])
        for col in cols:
            mes = dia = None
            for l in col:
                s = l.strip()
                if not s: continue
                if s.lower() in MESES: mes = MESES[s.lower()]; continue
                m = re.match(r"^(\d{1,2}) (LU|MA|MI|JU|VI|SA|DO)\s+(.*)$", s)
                if m: dia = int(m.group(1)); s = m.group(3).strip()
                if mes and dia and s and not s.startswith("CALENDARIO"):
                    out.append({"fecha": f"{y}-{mes:02d}-{dia:02d}", "titulo": s})
json.dump(out, open("indec_cal.json", "w"), ensure_ascii=False, indent=0)
for pat in ["Índice de precios al consumidor", "Intercambio comercial argentino", "Estimador mensual de actividad", "IPI manufacturero", "coyuntura de la actividad de la construcción", "Encuesta de supermercados", "Índice de salarios", "canasta básica total", "Mercado de trabajo", "patentamientos"]:
    xs = [(o["fecha"], re.sub(r".*\. ", "", o["titulo"])) for o in out if re.search(pat, o["titulo"])]
    print(pat[:30], " · ".join(f"{a[2:]}({b[:9]})" for a, b in xs))
