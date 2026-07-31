---
madr: 4
id: '0009'
estado: 'aceptado'
fecha: 2026-06-28
cinturon: 'macro'
archivos: ['scripts/itcm.py', 'scripts/macro.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'tests/', 'datos.ts', 'descripciones.ts', '[slug].astro', 'Hero.astro']
relacionado: ['0053', '0054']
ambito: '`scripts/itcm.py` · `scripts/macro.py` · `scripts/descargar_series.py` · `scripts/publicar.py` · `tests/` · web (`datos.ts`, `descripciones.ts`, `[slug].astro`, `Hero.astro`)'
---

# ADR-0009 — Índice de Desequilibrio Monetario (real-real i.a.) y el TCRM como 5ª dimensión del ITCM

## Contexto y planteo del problema

Sobre el cinturón macro llegaron cuatro correcciones (doc `250627 INDICE DE
DESEQUILIBRIO MONETARIO.docx` + notas del analista):

1. Varios datos son **de contexto** y no construyen la tensión, pero se mostraban
   mezclados con los del índice → confunde cómo se arma el indicador.
2. No quedaba claro **de dónde sale la capacidad prestable** (IdC): faltaba exponer
   indicador + fuente.
3. Una **propuesta de Índice de Desequilibrio Monetario (IDM)** para integrar al
   índice la variación de la masa monetaria, e **incluir el TCRM** (hasta ahora
   contexto) en el cálculo.
4. Un **título e introducción** nuevos para el inicio del informe.

Este ADR cubre la decisión metodológica (3); las correcciones 1, 2 y 4 son de
presentación.

La propuesta del doc define el IDM como **ΔM3 privado (nominal) − ΔM2 privado real**,
mensual, con un semáforo de dos colores (≤0 verde, >0 rojo).

## Opciones consideradas

- **IDM literal (nominal-real, m/m).** Rechazada: rojo permanente + estacional.
- **IDM real-real mensual.** Rechazada: corrige el sesgo pero no la estacionalidad.
- **IDM real-real interanual.** Elegida.
- **TCRM dentro de fiscal-comercial** vs. **nueva dimensión.** Se eligió dimensión
  propia (decisión del usuario): el frente cambiario es conceptualmente distinto
  del comercial y merece peso explícito.

## Decisión

**IDM — versión real-real interanual.** Se integra el IDM a la dimensión
*estabilidad monetaria* (que pasa de `{IPC 0,50 · REM 0,50}` a
`{IPC 0,40 · REM 0,30 · IDM 0,30}`), pero **no con la fórmula literal del doc**:
se implementa como

```
IDM = ΔM3 privado real i.a. − ΔM2 privado real i.a.   (en pp)
```

donde **M3 privado = circulante en poder del público (BCRA var. 17) + depósitos
privados (var. 100)** y **M2 privado = M2 transaccional del sector privado (var.
197)**, ambos deflactados por el IPC del INDEC. Bandas (`itcm.BANDAS_ITCM["idm"]`):
`≤−2 → 100 · −2 a 2 → 85 · 2 a 5 → 60 · 5 a 8 → 35 · >8 → 10`. Negativo =
remonetización genuina traccionada por la demanda real (baja tensión); positivo =
excedente de pesos sobre la demanda que presiona la brecha cambiaria.

**TCRM — nueva dimensión competitividad externa (12%).** El TCRM (ITCRM oficial,
[[0008-tcrm-itcrm-bcra]]) deja de ser contexto y puntúa en una 5ª dimensión.
Bandas calibradas con la historia 1997-2026 (p10≈75, p25≈87, mediana≈106):
`>110 → 100 · 95-110 → 80 · 85-95 → 60 · 75-85 → 35 · ≤75 → 10`. Apreciación real
= atraso cambiario = más tensión.

**Reponderación de dimensiones.** Las cuatro originales de la Paramétrica CIGOB
(35/30/20/15) se recortan en proporción para hacer lugar al 12% del TCRM:
estabilidad **0,30** · fiscal-comercial **0,27** · financiamiento **0,18** ·
actividad **0,13** · competitividad **0,12**. Estos números son operacionalización
propia (el doc solo definió las cuatro originales); pisables vía
`data/macro/ajustes_itcm.json`.

### Por qué se rechaza la fórmula literal del IDM

Validada contra datos reales (oct-2024 → may-2026), la fórmula nominal-real
mensual tiene dos defectos fatales:

- **Sesgo inflacionario.** Restar una tasa *real* de una *nominal* arrastra la
  inflación (~2-3 pp/mes): el gap queda casi siempre en +2,4 a +6 pp y el semáforo
  da **rojo permanente**. La inflación, además, ya la mide el IPC en la misma
  dimensión (doble conteo).
- **Estacionalidad del aguinaldo.** El m/m salta en dic/jun (la demanda de M2 real
  trepa) y revierte en enero → falsos verdes y rojos.

La versión real-real interanual elimina ambos (sin sesgo de inflación, sin
estacionalidad) y respeta la **intención** del doc: medir oferta amplia de pesos
vs. demanda real. Decisión del usuario vía AskUserQuestion explícito.

### Consecuencias

- Macro **ITCM 71,2 → 65,0** (Moderadamente aflojado), **tensión 2,9 → 3,5**: el
  índice ahora capta la apreciación real (TCRM 84,3 → banda 35) y el excedente
  monetario incipiente (IDM +4,5 pp → banda 60), tensiones que antes ignoraba.
- M3 privado **no existe como serie directa** en el BCRA: se construye var. 17 +
  100 (coincide con la definición del doc). Doble descarga BCRA (en `macro.py` y
  `descargar_series.py`), como ya ocurre con reservas.
- `tcrm` sale de `INDICADORES_CONTEXTO`; quedan badlar, prestamos_privados,
  base_monetaria y tc_mayorista. La web los muestra en un bloque "No integran el
  índice" ([[0007-fichas-explican-concepto-no-fuente]]).
- Sparkline del IDM disponible (serie i.a. mensual, 18 puntos).
- Tests pineados reescritos (`test_itcm.py` fixture EJEMPLO + bordes idm/tcrm;
  `test_publicar.py` 9 indicadores en el índice).
