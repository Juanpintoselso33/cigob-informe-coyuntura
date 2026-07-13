# Cinturón Vida Cotidiana

| Campo | Valor |
|---|---|
| Orquestador completo | `scripts/vida_cotidiana/main.py` |
| Script puente (legacy) | `scripts/vida_cotidiana.py` |
| Output del orquestador | `scripts/vida_cotidiana/data/vida_cotidiana_YYYYMMDD_HHMM.json` |
| Peso en score global | 20% |
| Barbarismo de riesgo | político — confundir popularidad con poder o ignorar el malestar material |

## Encuadre

Marco conceptual: cinturones de gobierno de Carlos Matus combinado con la propuesta de 15 indicadores del documento *Monitor de la Vida Cotidiana* (CIGOB, mayo 2026). El cinturón mide la experiencia material cotidiana del ciudadano: precios, ingreso, empleo, consumo, salud, seguridad, percepción.

## Indicadores activos

El orquestador `main.py` recolecta 8 fuentes con aproximadamente 32 datapoints por ejecución. Tabla de mapeo contra los 14 conceptos del documento base:

| Concepto del documento base | Indicador técnico | Fuente | Frecuencia | Estado |
|---|---|---|---|---|
| Brecha Salario Real vs. CBT | `brecha_salario_cbt` | INDEC (RIPTE + CBT) | Mensual | Automático |
| IPC Alimentos | `ipc_alimentos` | INDEC, serie 146.3 | Mensual | Automático |
| Endeudamiento Familiar | `prestamos_*` (tarjeta, personales, hipotecarios, consumo) | BCRA API v4.0 | Diaria | Automático |
| Peso de Tarifas | `ipc_vivienda + ipc_regulados` | INDEC | Mensual | Automático |
| Consumo de Carne Vacuna | `consumo_carne_per_capita` | CICCRA (parsing PDF) | Mensual | Automático |
| Informalidad Laboral | `informalidad_anual` | INDEC (asalariados sin descuento) | Anual | Automático |
| Mortalidad de PyMEs (proxy) | `ipi + emae` | INDEC | Mensual | Automático |
| Despacho Cemento e Hierro | `isac + acero_crudo` | INDEC | Mensual | Automático |
| Pluriempleo (proxy) | `subocupacion_demandante` | INDEC EPH | Trimestral | Automático |
| Espera en Salud Pública | `salud_datasets` | DEIS / CKAN (solo enumera datasets) | Variable | Automático parcial |
| Inseguridad Urbana | `inseguridad_snic + delitos_caba_disponible` | SNIC + CABA datos abiertos | Anual | Automático |
| ICC Confianza del Consumidor | `icc_utdt` | UTDT (scraping XLS) | Mensual | Automático |
| Sentimiento Digital | `sentimiento_digital` (Google Trends) | pytrends | Tiempo real | Automático |
| Apatía Electoral | (implementado en cinturón POLÍTICO como `votometro_ventaja_lla`) | Votómetro CIGOB | Continua | Automático |

### Indicador adicional implementado

| Indicador | Fuente | Comentario |
|---|---|---|
| `patentamiento_motos` | CAFAM | Proxy adicional de consumo discrecional. 51.124 unidades en mayo 2026. |

### Indicador de carga manual

| Indicador | Razón de carga manual |
|---|---|
| Deserción escolar | Sin serie mensual disponible. Ministerio de Educación publica datos con rezago anual; carga manual en cada actualización ministerial. |

## Estado de extracción (mayo 2026)

Las 8 fuentes activas devolvieron datos en la última ejecución (23 de mayo de 2026, 13:56):

| Fuente | Indicadores | Última fecha de dato |
|---|---|---|
| INDEC (datos.gob.ar) | 19 (IPC variantes, CBT/CBA, RIPTE, salario real, EPH, EMAE/IPI, faena/acero) | marzo 2026 |
| BCRA API v4.0 | 6 (préstamos privados, tarjeta, personales, hipotecarios, consumo, BADLAR) | mayo 2026 (diaria) |
| UTDT | ICC = 40.5 | mayo 2026 |
| CAFAM | Patentamiento motos = 51.124 | mayo 2026 |
| CICCRA | Consumo carne (parsing PDF) | abril 2026 |
| SNIC + CABA | Inseguridad (2.501.057 hechos en 2024) | 2024 (anual) |
| Salud (datasets) | 3 datasets CKAN identificados | — |
| Google Trends | inflación, precios, inseguridad, trabajo | tiempo real |

## Ejecución

```bash
cd projects/informe_coyuntura/scripts/vida_cotidiana
python main.py
```

El output se guarda en `data/vida_cotidiana_YYYYMMDD_HHMM.json`.

## Observación técnica importante

El script puente `scripts/vida_cotidiana.py` —que integra con el orquestador global del informe— solo expone tres indicadores legacy (`ipc_total`, `desocupacion`, `icc_utdt`). El dashboard agregado debería migrarse a leer del output del orquestador (`scripts/vida_cotidiana/data/vida_cotidiana_*.json`) para acceder a los 14 indicadores completos.

## Indicador propuesto prioritario

### `ingreso_disponible_real` — Salario real vs. gastos fijos del hogar

Inspiración: [Empiria Consultores](https://empiriaconsultores.com/) (Hernán Lacunza). Captura el efecto tarifas post-subsidios que el IPC general oculta.

Fórmula propuesta (completamente automatizable sin EPH):

```
ingreso_disponible_real(t) = IS_registrado(t) / IPC_vivienda(t)
variacion_ia = (idx_t / idx_t-12 − 1) × 100
```

Series verificadas en datos.gob.ar:

| Variable | Serie ID | Última fecha disponible |
|---|---|---|
| IS_registrado | `149.1_TL_REGIADO_OCTU_0_16` | enero 2026 |
| IPC_vivienda | `146.3_IVIVIENNAL_DICI_M_52` | marzo 2026 |

Cálculo a mayo 2026 (enero 2026 vs. enero 2025): −8.0% interanual. El salario perdió contra los gastos fijos pese a la desinflación general (variación IS vs. IPC general fue +3.99%).

Implementación sugerida: `scripts/vida_cotidiana/collectors/ingreso_disponible.py`, siguiendo el patrón de `indec_series.py`.

Score propuesto: +3% i.a. equivale a 0; 0% equivale a 5; −5% equivale a 10. Fórmula: `max(0, min(10, 5 − var_ia × 5/3))`.

## Fórmula de score actual (legacy, solo 3 indicadores)

```python
score_ipc   = min(10, max(0, ipc))             # 0% → 0, 10% → 10
score_desoc = min(10, max(0, desoc / 2))        # 0% → 0, 20% → 10
score_icc   = min(10, max(0, (60 - icc) / 3))   # 60 → 0, 30 → 10
score = promedio(disponibles)
```

Umbrales: 0–3 estable, 4–6 en tensión, 7–10 tensionado.

**Pendiente:** scorer compuesto sobre los 14 indicadores del orquestador `main.py` para reemplazar el legacy.

## Notas de mantenimiento

- **UTDT:** requiere `xlrd==1.2.0` (NO usar `xlrd>=2.0` que no soporta archivos `.xls` OLE2). ICC corresponde a la página 16458 (Confianza del Consumidor). No confundir con ICG = página 16457 (Confianza en el Gobierno).
- **CICCRA:** scraping del PDF mensual desde `ciccra.com.ar/wp-content/uploads/YYYY/MM/`. Si cambia la estructura del PDF, ajustar `collectors/ciccra.py`.
- **BCRA:** requiere `verify=False` + `urllib3.disable_warnings()`.
- **Google Trends:** `pytrends` requiere rate limiting. Si falla con error 429, esperar y reintentar.
- **Salud:** el colector actual solo enumera cuántos datasets hay en CKAN; no procesa contenido. Mejora pendiente: parsear el dataset DEIS de tiempos de espera real cuando esté disponible.
