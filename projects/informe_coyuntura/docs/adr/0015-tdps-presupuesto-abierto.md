---
madr: 4
id: '0015'
estado: 'aceptado'
fecha: 2026-07-02
cinturon: 'gestion'
archivos: ['scripts/gestion.py', 'data/gestion/tdps_baseline_2023.json', '.github/workflows/data-pipeline.yml']
ambito: '`scripts/gestion.py` · `data/gestion/tdps_baseline_2023.json` · `.github/workflows/data-pipeline.yml`'
---

# ADR-0015 — TDPS: la asistencia directa se verifica contra la ejecución presupuestaria (API Presupuesto Abierto)

## Contexto y planteo del problema

`asistencia_directa` (D5 del ITCG) medía la Tasa de Desintermediación de
Planes Sociales (TDPS, doc 260702) como **carga manual = 100**, apoyada solo
en el plano normativo (el Dto. 198/2024 eliminó las Unidades de Gestión del ex
Potenciar Trabajo). El propio doc pedía verificarlo con el dato presupuestario.
Con el token de la API Presupuesto Abierto (alta automática, emitido
2026-07-02) el supuesto se puede contrastar contra el devengado real.

## Opciones consideradas

- **CSVs anuales sin token** (`credito-mensual-YYYY.zip`): funcionan y tienen
  la misma granularidad, pero obligan a descargar y parsear 200-550 MB por
  corrida en CI. Quedan documentados como plan B si el token caduca.
- **Buscar por programa_desc** ("Volver al Trabajo" no existe como programa:
  vive como *actividad* dentro de "Acciones de Empleo"); por eso el filtro va
  por `actividad_desc`.

## Decisión

Colector AUTO contra la **API Presupuesto Abierto** (base SIDIF, la misma que
publica los CSVs sin token de `dgsiaf-repo.mecon.gob.ar` — se eligió la API
porque devuelve agregados filtrados de pocos KB en vez de archivos de
200-550 MB por ejercicio):

- **TDPS = 100 × (devengado partida 5.1.4 "Ayudas sociales a personas" /
  devengado total del inciso 5)** sobre los programas sucesores del Potenciar:
  actividades **"Volver al Trabajo"** (Sec. Trabajo, serv. 350, prog. 16,
  act. 17) y **"Acompañamiento Social"** (Sec. Niñez, serv. 311, prog. 38,
  act. 10). Se localizan por `actividad_desc LIKE` (robusto a renumeraciones
  entre ejercicios); si el ejercicio corriente no tiene devengado (enero), cae
  al anterior.
- "Directo" = 5.1.4; **todo el resto del inciso 5 cuenta como intermediado**
  (instituciones sin fines de lucro, cooperativas, municipios, universidades):
  es plata que llega al beneficiario a través de un tercero. Más simple y
  menos frágil que matchear por texto qué parcial es una "Unidad de Gestión".
- **Baseline 2023** (contexto de la ficha): Potenciar Trabajo (jur. 85,
  prog. 38), ejercicio cerrado → se computa una vez y se cachea versionado en
  `data/gestion/tdps_baseline_2023.json`.
- Token fuera del repo: secret `PRESUPUESTO_ABIERTO_TOKEN` en Actions +
  `.env` local gitignored. Fallback: la entrada manual de manuales.json.

### Consecuencias

- Gestión queda con **13 indicadores automáticos de 16** (manuales: solo
  concesiones, protocolo antipiquetes y opción salud).
- El TDPS ahora puede DETECTAR una reversión (si reaparecieran transferencias
  a organizaciones, el valor cae solo y la banda castiga).
- **Riesgos**: si el nombre de las actividades cambia en un presupuesto
  futuro, el colector cae al fallback manual (visible como "Carga manual" en
  la web); actualizar TDPS_ACTIVIDADES en ese caso.

## Más información

### Resultado verificado (2026-07-02)

- **2026: TDPS = 100,0%** — $527.680M devengados ($434.585M Volver al Trabajo
  + $93.095M Acompañamiento Social), **todo** por 5.1.4; cero por
  organizaciones.
- **2023 (baseline): TDPS = 98,3%** — el Potenciar devengó $1,02 billones,
  de los cuales ~$17.224M pasaron por cooperativas, instituciones sin fines
  de lucro y municipios.
- Lectura honesta que el dato agrega al relato: la intermediación financiera
  ya era minoritaria en 2023 (el Salario Social Complementario se pagaba
  directo); lo que el Dto. 198/2024 eliminó fue el canal institucional
  restante — que ahora es exactamente $0. La banda del ITCG no cambia
  (TDPS ≈ 100 → 100 puntos): cambia el sustento, de supuesto normativo a
  dato verificado.
