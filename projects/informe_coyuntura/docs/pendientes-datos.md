# Pendientes de datos y roadmap de indicadores

> Doc vivo de seguimiento. Registra qué indicadores faltan automatizar, qué datos
> están bloqueados o son de pago, qué se acumula a la espera de histórico, y el
> índice de decisiones (ADRs). **No** es metodología del informe (eso vive en
> `docs/cinturon_*.md`): es la lista de trabajo pendiente.
>
> **Última actualización:** 2026-06-30.

---

## 1. Indicadores manuales / estimados (placeholders)

Indicadores que hoy NO se actualizan solos: usan un valor cargado a mano o una
estimación. Ordenados por cinturón.

### Política
| Indicador | Estado | Por qué no se automatiza | Camino posible |
|---|---|---|---|
| `cohesion_bloque` | Placeholder (78%) | Las votaciones nominales del CKAN de Diputados están **congeladas en 2019** (período 137); LLA no existía. La composición actual del bloque está, pero sin `PERSONA_ID` que mapee a los votos históricos. | Headless browser sobre hcdn.gob.ar/votaciones, o acuerdo con HCDN por una fuente alternativa. |
| `gobernadores_alineamiento` | Placeholder (55%) | Métrica cualitativa, **sin fuente estructurada**. | NLP sobre declaraciones (La Nación Data, Infobae) — proyecto separado. |

### Gestión (reformas APN)
| Indicador | Estado | Por qué no se automatiza | Camino posible |
|---|---|---|---|
| `privatizaciones` | Manual ("En proceso") | Boletín Oficial **sin API JSON pública**; ComprAR es ASP.NET con `__VIEWSTATE`; `tipoNorma=3 "privatizacion"` es ambiguo (OR-search; contar normas ≠ transferencia completa). | Scraper BO con sesión, o seguimiento manual de transferencias efectivas. |
| `libertad_opcion_salud` | Placeholder | Backend de la SSS con **fingerprinting** (`/fwb/first_submit.df`); padrón de obras sociales en datos.gob.ar **congelado en 2019**. | Sin alternativa conocida hoy. |
| `concesiones_infraestructura` | Manual ("Parcial") | Informes de Vialidad Nacional / ORSNA periódicos, no estructurados. | Parseo de informes PDF, si aparecen con regularidad. |
| `asistencia_directa` | Placeholder | ANSES / MDS (Volver al Trabajo, ex Potenciar) sin serie pública estable. | Seguir publicaciones de ANSES/MDS. |
| `fal_modernizacion_laboral` | Manual (legislación) | La FAL (modernización laboral) **no operativa hasta H2-2026**; sin métrica de ejecución todavía. | Revisar cuando entre en vigencia. |
| `protocolo_antipiquetes` | Placeholder | Min. Seguridad, sin serie estructurada de aplicación. | Métrica cualitativa / conteo de operativos si hay fuente. |

### Macro — ver §4 (acumulación) y §3 (bloqueadas).

---

## 2. Scrapers automáticos frágiles o degradados

Funcionan vía `carry-forward` (mantienen el último valor si la fuente falla), lo
que puede **enmascarar** una rotura. Verificar periódicamente.

| Indicador | Cinturón | Estado (2026-06-30) | Nota |
|---|---|---|---|
| `inseguridad` (SNIC) | Vida | ⚠️ Pegado en **2024** (2.501.057) | `collectors/snic.py`: el CSV nacional cambió de formato y `_parse_snic_csv` ya no extrae `total_hechos`. Carry-forward a 2024 lo disimula. **Hay que re-mapear columnas del CSV nuevo.** |
| `sentimiento_digital` | Espíritu | ⚠️ Flaky (Google Trends) | pytrends cae seguido; usa cache. Si Trends viene null, `espiritu_epoca.py` busca hacia atrás. |
| `movilizacion_cepa` | Política | ✅ Recuperado (fresco 2026-06-28) | Estuvo roto en jun-2026; volvió. Selector de centrocepa.com.ar/informes a vigilar. |
| `votometro_ventaja_lla` / `clima_electoral` | Política / Espíritu | Cadencia de actualización del Votómetro (producto propio CIGOB) | Se marca "desactualizado" entre corridas del Votómetro; no es una rotura. |

---

## 3. Fuentes bloqueadas / por conseguir

Datos que **no existen como serie automatizable** hoy (investigados a fondo).

| Dato | Para | Por qué está bloqueado | ADR |
|---|---|---|---|
| **Patentamientos comerciales** (camiones + utilitarios) | IAI (inversión física) | DNRPA solo expone el **mes corriente** a nivel registro; el agregado histórico solo trae "Automotores" total. → resuelto por acumulación (§4). | [0010](adr/0010-capitulo-inversion-iai-icip.md) |
| **Hardware hi-tech** (NCM 8471/8517/8542: servers, telecom, circuitos integrados) | ICIP (inversión digital) | El NCM oficial en datos.gob.ar es **solo a 2 dígitos** (capítulo, demasiado amplio) y **~16 meses viejo**. Las posiciones a 8 dígitos solo viven en microdata bulk de Aduana, sin serie. | [0010](adr/0010-capitulo-inversion-iai-icip.md) |
| **Bienes de capital importados por CANTIDAD** | IAI | El índice de cantidad (limpio de precios) es **trimestral**; hoy el IAI usa el valor mensual en USD (`74.3_IIBCA`). Caveat menor. | — |
| Votaciones nominales Diputados (LLA) | `cohesion_bloque` | CKAN congelado en 2019 (ver §1). | — |

---

## 4. Acumulaciones en curso (se completan con el tiempo)

Cuando la fuente no da histórico, se **acumula mes a mes** en un JSON versionado.

| Store | Indicador | Estado | Serie i.a. lista |
|---|---|---|---|
| `data/macro/patentamientos_comerciales.json` | `iai` (3er componente) | Arrancó **2026-05** (12.652 comerciales/mes). `macro.actualizar_patentamientos_comerciales()` upserta un mes por corrida. | **~mediados de 2027** (a los 13 meses). Ahí el IAI pasa de 65/35 a 55/30/15 automáticamente. |

---

## 5. Data de pago / suscripción (evaluación pendiente)

Atajos comerciales que resolverían algún bloqueo, a sopesar costo/beneficio.

| Servicio | Resolvería | Notas |
|---|---|---|
| **SIOMAA** (ACARA) | Patentamientos comerciales **ya** (sin esperar la acumulación a 2027) | Producto comercial con login/paywall. Decisión: por ahora se acumula gratis vía DNRPA (§4). |
| Microdata Aduana por NCM 8 dígitos | Hardware hi-tech del ICIP | No es "pago" pero requiere un pipeline de extracción/normalización de archivos bulk; sin serie limpia. Proyecto aparte si se prioriza. |

---

## 6. Mejoras metodológicas pendientes

Cosas que funcionan pero podrían afinarse.

- **`mortalidad_pymes` (Vida):** hoy usa **% m/m de la serie IPI original**, dominada por estacionalidad (feb→mar puede dar +21% m/m espurio). **Cambiar a i.a. o serie desestacionalizada** con nuevas anclas.
- **Divergencia de score de Vida:** el colector (`vida_cotidiana.py`/`generar_informe.py`) escribe el score legacy de 3 indicadores; `publicar.py` lo **sobrescribe** con el promedio de aportes en el snapshot. Pendiente opcional: portar el scoring al colector para eliminar la divergencia.
- **IAI / ICIP volatilidad:** las series i.a. de inversión son ruidosas (±30-180% en 2024-25). Las bandas ya clampean, pero si el score mensual salta mucho, evaluar **media móvil 3m** de los componentes antes de componer.
- **ICIP — `servicios_tech`:** hoy usa solo "Pago de servicios de informática" (`185.1`). Se podría sumar "uso de propiedad intelectual" (licencias) si se valida que no mete ruido.

---

## 7. Índice de decisiones (ADRs)

Las decisiones de diseño/metodología viven en [`docs/adr/`](adr/README.md). Resumen:

| # | Decisión |
|---|---|
| [0001](adr/0001-datos-calculados-no-hardcodeados.md) | Todo calculado de datos oficiales; nunca hardcodeado. |
| [0002](adr/0002-rem-equivalente-mensual.md) | REM por equivalente mensual (raíz-12). |
| [0003](adr/0003-recaudacion-interanual-real.md) | Recaudación en variación i.a. real. |
| [0004](adr/0004-financiamiento-indice-capacidad-prestable.md) | Financiamiento usa el Índice de Capacidad Prestable (IdC). |
| [0005](adr/0005-reservas-netas-a-secas.md) | Reservas netas "a secas" (SDDS + Tesoro + Bopreal). |
| [0006](adr/0006-brecha-cambiaria-ccl-mayorista.md) | Brecha cambiaria CCL/mayorista. |
| [0007](adr/0007-fichas-explican-concepto-no-fuente.md) | Las fichas explican qué mide, no de dónde sale. |
| [0008](adr/0008-tcrm-itcrm-bcra.md) | TCRM via ITCRM oficial del BCRA. |
| [0009](adr/0009-idm-y-tcrm-en-el-itcm.md) | IDM (real-real i.a.) + TCRM como 5ª dimensión. |
| [0010](adr/0010-capitulo-inversion-iai-icip.md) | Capítulo Inversión: IAI + ICIP (6ª dimensión); patentamientos por acumulación. |

---

## 8. Snapshot de cobertura (2026-06-30)

| Cinturón | Automáticos | Manuales / estimados | Score |
|---|---|---|---|
| Macro | 11 en el índice (+ 4 contexto) | 0 | 3,7 |
| Política | 7/9 | 2 (`cohesion_bloque`, `gobernadores_alineamiento`) | 4,5 |
| Vida cotidiana | la mayoría (⚠️ SNIC stale) | — | 3,5 |
| Gestión | 6/12 | 6 (ver §1) | 5,8 |
| Espíritu de época | 3 proxies (⚠️ Trends flaky) | — | 2,4 |
