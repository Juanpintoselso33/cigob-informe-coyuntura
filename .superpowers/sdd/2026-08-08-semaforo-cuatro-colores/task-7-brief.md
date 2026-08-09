### Task 7: Los tres ADR

**Files:**
- Create: `docs/adr/0181-el-color-es-la-tension-que-ya-se-publica.md`
- Create: `docs/adr/0182-los-umbrales-del-semaforo-se-calculan.md`
- Create: `docs/adr/0183-rediseno-del-cinturon-politico.md`
- Modify: `docs/adr/README.md` (**generado** — no editar a mano)

**Interfaces:**
- Consumes: la spec.
- Produces: nada que otra tarea consuma.

- [ ] **Step 1: Leer el formato vigente**

Run: `head -20 docs/adr/0179-ningun-test-escribe-en-un-archivo-versionado.md`

MADR v4 en castellano: frontmatter YAML + `Contexto y planteo · Factores de
decisión · Opciones consideradas · Decisión (+ Consecuencias, Confirmación) ·
Pros y contras · Más información`.

**Los ids van entre comillas** (`id: '0181'`, `relacionado: ['0121']`). Sin
comillas, YAML 1.1 los lee como octal y la referencia apunta a otro ADR sin que
falle nada.

- [ ] **Step 2: Escribir ADR-0181 — la regla**

Frontmatter: `id: '0181'`, `estado: 'aceptado'`, `fecha: 2026-08-08`,
`cinturon: 'transversal'`, `indice: 'todos'`,
`archivos: ['scripts/parametrica.py', 'scripts/publicar.py', 'web/src/lib/datos.ts']`,
`relacionado: ['0121', '0021']`.

Contenido obligatorio, todo de la spec:

- Las **tres opciones** (§3.1) con la premisa falsa del doc `ITCG_completo`: propone 85/55/25 como "punto medio entre anclas 100/70/40/10", y las anclas del ITCG son 100/85/65/40/10.
- Que las fichas de Gestión ya implementaban 65/45/25, verificado exacto en 12 indicadores.
- Que 60/40/20 son los bordes de `BANDAS_INTERPRETACION`, que ya se publican.
- **Efecto honesto, las dos mitades.** Los 6 indicadores que mejoran (§3.2) **y** la tabla de vida cotidiana, donde 5 componentes empeoran y el ITVC total pasa a naranja. Este ADR no puede mostrar solo la mitad favorable.
- Que el cambio **corrige** una inconsistencia previa: `semaforoDimension` usaba verde a tensión 4 para los índices 0-100 y a tensión 6 para el ITVC.
- La histéresis de dos meses como opción **descartada**, con el motivo (§3.3).

- [ ] **Step 3: Escribir ADR-0182 — umbrales calculados**

`id: '0182'`, `estado: 'aceptado'`, `continua: ['0181']`,
`archivos: ['scripts/parametrica.py']`.

Contenido: por qué los umbrales se calculan por interpolación inversa y no se
escriben en la ficha (las fichas de agosto envejecieron en una semana: RIGI
24,6% → 31,6%); el caso no monótono de `costo_financiamiento_tesoro` con su
mapa de colores completo; la trampa del redondeo de `aporte_score`; y que los
indicadores sin anclas reciben color pero no tabla.

- [ ] **Step 4: Escribir ADR-0183 — rediseño del ITCP, propuesto**

`id: '0183'`, **`estado: 'propuesto'`**, `cinturon: 'politica'`,
`indice: 'itcp'`, `relacionado: ['0048']`.

Contenido: los 11 indicadores del documento, los 10 que mapean, el que no
existe (Postura de los Sindicatos, con el sistema de puntajes por tipo de
acción que el documento propone), los **8 que hoy puntúan y el documento no
menciona**, y que reabrir la cohesión por cámara revierte ADR-0048. Más los
**cinco defectos** de los umbrales del documento (§7.3 de la spec): el hueco
90–99,9% en cohesión, el hueco por encima de 3,0 en ratio DNU, los dos ejes
mezclados en designación de jueces, los tramos compuestos del votómetro, y el
indicador de cámaras empresarias duplicado.

Este ADR **no se implementa**: registra la propuesta para que CIGOB la apruebe
o la baje.

- [ ] **Step 5: Regenerar el índice y correr el gate de ADR**

```bash
python scripts/adr_coherencia.py
python -m pytest tests/test_adr_format.py -q
```

Expected: PASS. El índice del README y las relaciones inversas se generan; no
se editan a mano.

- [ ] **Step 6: Commit**

```bash
git add docs/adr/0181-*.md docs/adr/0182-*.md docs/adr/0183-*.md docs/adr/README.md
git commit -m "docs(adr): 0181 la regla de color, 0182 los umbrales calculados, 0183 el ITCP propuesto"
```

---

