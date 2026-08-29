---
madr: 4
id: '0244'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'gestion'
indicadores: [concesiones_infraestructura]
archivos: ['scripts/gestion.py', 'tests/test_gestion_concesiones.py', 'tests/fixtures/rfc_concesiones.json']
relacionado: ['0087', '0269']
ambito: 'Cinturón gestión · ITCG · `concesiones_infraestructura` · qué fuente decide que una etapa está adjudicada'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «la Resolución 1379/2026 adjudicó formalmente los ocho tramos de Etapa III»'
---

# ADR-0244 — El acto jurídico manda sobre el estado del portal

## Contexto y planteo del problema

`concesiones_infraestructura` publicaba **28,7%** — 2.614 de 9.091 km de la Red
Federal de Concesiones. El plan estaba **entero adjudicado**.

El indicador decidía si una etapa estaba adjudicada leyendo el **estado del
expediente en CONTRAT.AR**. CONTRAT.AR se queda viejo: al 25-ago-2026 seguía
mostrando «Disponible Para Adjudicar» dos etapas que ya tenían resolución
publicada en el Boletín Oficial.

| Etapa | Proceso | km | CONTRAT.AR al 25-ago | Adjudicación publicada |
|---|---|---:|---|---|
| I | 504-0007-LPU25 | 741,71 | Adjudicado | Res. 80/2025 · 19-nov-2025 |
| II | 504-0013-LPU25 | 1.871,82 | Adjudicado | Res. 706/2026 · 15-may-2026 |
| **II-B** | 504-0015-LPU25 | **2.557,11** | **Disponible Para Adjudicar** | **Res. 1149/2026 · 28-jul-2026** |
| **III** | 504-0001-LPU26 | **3.920,21** | **Disponible Para Adjudicar** | **Res. 1379/2026 · 24-ago-2026** |

La auditoría detectó la Etapa III y estimó el indicador en aproximadamente
**71,65%** usando 3.900 km como cota inferior. **No detectó la II-B**, que
estaba adjudicada desde un mes antes: con las cuatro etapas, el número es
**100%**.

Que el error fuera de casi 71 puntos y no de 43 no cambia el diagnóstico, pero
sí lo confirma: el problema no era una etapa puntual sino **la fuente elegida
para decidir el hecho**. Un portal de compras informa el trámite; lo que
adjudica es la resolución.

## Factores de decisión

- **El hecho a medir es jurídico**, y tiene un registro público con fecha.
- **CONTRAT.AR sigue siendo útil** —es la única fuente del número de proceso y
  del universo de expedientes— pero no puede ser el único juez del estado.
- **La discrepancia entre las dos fuentes es información**, no ruido a esconder.
- **La suma tiene que ser trazable tramo por tramo**: un porcentaje de avance
  sin el inventario que lo forma es lo que dejó pasar 28,7%.

## Opciones consideradas

- **A — Registro manual** de las etapas adjudicadas, con la resolución citada.
- **B — Consultar el Boletín Oficial** (vía InfoLeg) por el número de proceso y
  detectar la resolución que adjudica.
- **C — Esperar** a que CONTRAT.AR se actualice.

## Decisión

**Opción B.** Una etapa cuenta como adjudicada si CONTRAT.AR lo declara **o** si
existe una resolución publicada que adjudique su proceso. El Boletín **suma**
etapas, nunca las quita.

La detección tiene tres piezas, y las tres hicieron falta:

- **La clave es el número de proceso** (`504-0001-LPU26`), que CONTRAT.AR ya
  provee. Buscar «RED FEDERAL DE CONCESIONES» en InfoLeg devuelve 11.556
  resultados: el buscador hace OR entre palabras.
- **El buscador tampoco es exacto con el número**: pedirle `504-0007-LPU25`
  devuelve además resoluciones de otros procesos. Por eso el número se verifica
  dentro del **texto completo** de cada candidata, no en el sumario del listado,
  que viene truncado.
- **La adjudicación es la aprobación de lo actuado en la SEGUNDA etapa.** En
  esta licitación de etapa múltiple, la primera precalifica oferentes y la
  segunda evalúa las ofertas económicas y adjudica los renglones. Verificado
  contra el texto del Boletín Oficial de la Resolución 1379/2026, que lista los
  ocho tramos con sus adjudicatarios, y contra la cobertura de prensa de la
  Resolución 1149/2026, que nombra los cuatro de la II-B.

**Lo que valida la regla es que reproduce lo que ya se sabía**: aplicada a las
etapas I y II —las dos donde CONTRAT.AR está al día— encuentra exactamente una
resolución de segunda etapa para cada una, y coincide con el «Adjudicado» del
portal. No es una regla ajustada al caso que se quería detectar.

La opción A habría fijado números auditados como constantes, que es lo que el
propio mandato de la auditoría desaconseja. La C deja el indicador esperando a
una fuente que no tiene compromiso de actualización.

### Consecuencias

- El indicador pasa de **28,7% a 100%**. El puntaje de banda salta de 44,6 al
  tope de la escala del ITCG (`>75 → 100`) y la tensión del indicador cae de
  5,5/10.
- La card publica `inventario_etapas`: por etapa, km, si está adjudicada, **de
  qué fuente sale ese estado** y, cuando corresponde, la resolución y su fecha.
- El texto dice explícitamente que CONTRAT.AR está atrasado y en qué etapas.
- **InfoLeg sólo se consulta cuando el portal no declara la adjudicación**: si
  ya dice Adjudicado no hay nada que dirimir. Son dos consultas y no cuatro.
- **Si InfoLeg falla, el indicador no se cae**: informa lo que sabe por el
  portal, con un aviso.
- Queda una limitación declarada: las etapas se cuentan enteras. Las II-B y III
  adjudican por renglones y una adjudicación parcial contaría como total. Hoy no
  cambia nada —las cuatro están adjudicadas por completo— pero es el próximo
  refinamiento si aparece una etapa a medias.

### Confirmación

`tests/test_gestion_concesiones.py` contra `tests/fixtures/rfc_concesiones.json`
—los cuatro procesos con su estado real en CONTRAT.AR, los km por etapa y las
cuatro resoluciones—:

- el plan entero da 100% y **28,7% no puede volver**;
- el resultado supera la cota de ~71,65% que estimó la auditoría;
- la suma es trazable: los km del inventario reconstruyen el numerador;
- cada etapa declara de qué fuente sale su estado —I y II por CONTRAT.AR, II-B y
  III por el Boletín—;
- las adjudicadas por Boletín citan su resolución, y la 1379 y la 1149 aparecen
  en el texto de la card;
- **sin resolución publicada, el indicador vuelve a 28,7%**: el Boletín suma, no
  regala;
- con InfoLeg caído, el indicador publica igual;
- no se consulta el Boletín por las etapas que el portal ya declara adjudicadas;
- `Preadjudicado` sigue sin contar ([[0087-preadjudicado-no-es-adjudicado]]): la
  segunda fuente podría tapar ese error si la frontera de palabra se rompiera.

Probado rompiéndolo: si el estado vuelve a depender sólo de CONTRAT.AR, fallan
cuatro guardas.

## Pros y contras de las opciones

### A — Registro manual

- Bueno, porque es inmediato y auditable.
- Malo, porque fija números auditados como constantes productivas y hay que
  acordarse de actualizarlo en cada adjudicación.

### B — Boletín Oficial por número de proceso

- Bueno, porque mide el hecho jurídico donde ocurre, con fecha.
- Bueno, porque se valida sola contra las etapas que CONTRAT.AR sí tiene al día.
- Malo, porque depende del buscador de InfoLeg, que no es exacto y obliga a
  verificar el texto completo de cada candidata.
- Malo, porque la frase que identifica la adjudicación es propia de esta
  licitación: otra estructura licitatoria necesitaría otra regla.

### C — Esperar a CONTRAT.AR

- Bueno, porque no agrega fuentes.
- Malo, porque el portal no tiene compromiso de actualización: la II-B llevaba
  casi un mes adjudicada y seguía figurando disponible.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_gestion.md`, caso 11.
- Boletín Oficial, Resolución 1379/2026 (Etapa III, ocho tramos) y Resolución
  1149/2026 (Etapa II-B, cuatro tramos).
