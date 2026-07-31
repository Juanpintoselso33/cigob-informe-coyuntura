---
madr: 4
id: '0014'
estado: 'aceptado'
fecha: 2026-07-02
cinturon: 'gestion'
archivos: ['scripts/gestion.py', 'scripts/piquetes_poll.py', '.github/workflows/piquetes-poll.yml', 'data/gestion/piquetes_alertas.json']
ambito: '`scripts/gestion.py` · `scripts/piquetes_poll.py` · `.github/workflows/piquetes-poll.yml` · `data/gestion/piquetes_alertas.json`'
---

# ADR-0014 — Piquetes: poller GTFS-RT acumulativo (el registro de cortes del GCBA está muerto)

## Contexto y planteo del problema

El ADR-0013 dejó `protocolo_antipiquetes` como carga manual y documentó el
camino de automatización: la API Transporte GCBA con su endpoint histórico
`/transito/v1/eventos?month=YYYY-MM` (serie mensual con duración). Con las
credenciales ya emitidas (registro 2026-07-02) se hizo la prueba decisiva:

- Auth **funciona** (secret inválido → 401 "Invalid Client").
- **Todo `/transito/v1/*` está muerto**: `/eventos` y `/cortes` devuelven
  HTTP 500 con el path como cuerpo, en todas las variantes de parámetros.
  Consistente con el RAML actual del console (ambos recursos comentados) y
  con el aviso de BA Data ("datasets con Formato API están suspendidos").
- Lo único vivo y relevante: los feeds **GTFS-RT de alertas de servicio**
  (`/colectivos/serviceAlerts`, `/subtes/serviceAlerts`, JSON con `json=1`) —
  verificado con una alerta real de subte. El estándar GTFS-RT trae
  `cause=5 (DEMONSTRATION)`, y los textos describen la disrupción.
- `/datos/movilidad/transito` (conteo vehicular por sensores, mensual desde
  feb-2020) está vivo pero mide flujo, no cortes.

## Opciones consideradas

- **Poller de `/transito/v1/cortes`** (plan B del ADR-0013): muerto junto con
  `/eventos`.
- **Puntuar las alertas GTFS-RT ya mismo**: sin baseline 2023 ni historia, un
  conteo de dos días no es bandeable; entraría ruido puro al índice.
- **Sheet de Vialidad Nacional** (cortes de rutas nacionales, sin key): mide
  otra jurisdicción (rutas, mayormente clima/obras) y también es snapshot sin
  histórico; se descarta para CABA.

## Decisión

**Acumular desde ahora** (mismo patrón que los patentamientos comerciales de
macro, ADR-0010): no existe fuente oficial que permita reconstruir la línea
base dic-2023.

- `gestion.actualizar_alertas_manifestacion()`: consulta ambos feeds, filtra
  alertas de manifestación (`cause=5` **o** texto con
  manifestaci/piquete/marcha/protesta/movilizaci) y las upserta en
  `data/gestion/piquetes_alertas.json` keyed por día, con **dedupe por id**
  (la misma protesta vista en dos muestreos cuenta una vez). Un día presente
  con `{}` = "se muestreó y no había" — la cobertura queda auditable.
- **Muestreo 3×/día**: la corrida del pipeline (00:00 ART) + el workflow
  liviano `piquetes-poll.yml` (12:00 y 18:00 ART, la franja típica de
  piquetes). Los feeds son tiempo real puro: sin muestreo diurno la serie se
  perdería casi todas las protestas.
- Nuevo indicador de **CONTEXTO** `alertas_manifestacion` (alertas únicas del
  mes corriente): no puntúa en el ITCG. `protocolo_antipiquetes` sigue manual
  (55% de reducción vs 2023, Diagnóstico Político) hasta que la serie propia
  tenga historia comparable.
- **Credenciales fuera del repo**: env vars `BA_TRANSPORTE_CLIENT_ID/SECRET`
  (secrets de GitHub Actions) con fallback a `.env` local gitignored, parseado
  sin dependencias nuevas.

### Consecuencias

- La serie de manifestaciones **arranca el 2026-07-02** y madura sola: cuando
  tenga ~12 meses podrá bandearse (variación i.a. propia) y reemplazar la
  carga manual de `protocolo_antipiquetes` — decisión para ese momento, con
  ADR nuevo.
- Costo CI: 2 corridas de ~1 minuto por día (checkout + `pip install requests`
  + 2 GETs); commits `[skip ci]` solo si hay alertas nuevas.
- **Riesgos**: los feeds pueden vaciarse o discontinuarse sin aviso (BA Data
  ya declaró APIs "en revisión"); la métrica es "alertas que afectan al
  transporte", un subconjunto de los piquetes reales — sesgo a subcontar
  protestas chicas que no desvían líneas. Ambas cosas quedan a la vista en la
  ficha del indicador.
