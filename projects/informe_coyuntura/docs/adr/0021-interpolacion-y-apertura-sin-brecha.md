---
madr: 4
id: '0021'
estado: 'aceptado'
nota_estado: 'aceptada (decisión del editor; ejecuta las Decisiones 3 y 4b del ADR-0019)'
fecha: 2026-07-03
cinturon: 'gestion'
indicadores: [apertura_comercial]
supersede: ['0013']
relacionado: ['0054', '0055', '0056', '0069', '0071', '0072', '0075', '0076', '0081']
---

# ADR-0021 — Puntaje interpolado en ITCM/ITCG y apertura comercial sin brecha

- **Supersede:** el puntaje escalonado por banda de ADR-0013 (el motor) y el
  ILCE compuesto de la tanda ITCG (el indicador apertura_comercial)

## Contexto y planteo del problema

El ADR-0019 midió dos defectos de diseño y este ADR los ejecuta juntos, en un
solo cambio de método, porque sus efectos sobre el titular se compensan casi
exactamente (≈ +3 por interpolación, ≈ −2,5 por sacar la brecha del ILCE):

1. **Escalones de banda.** El puntaje discreto por banda creaba acantilados:
   dos valores casi iguales a ambos lados de un umbral diferían 15-25 puntos
   de componente, un indicador oscilando alrededor de un umbral hacía
   "parpadear" el índice, y el análisis de sensibilidad midió que los
   umbrales aportaban el DOBLE de incertidumbre que los pesos (σ 2,2-2,5 vs
   1,0-1,4). El estudio sombra (`interpolacion_sombra.py`) mostró deltas por
   componente de hasta ±13 puntos truncados por las bandas, con la misma
   lectura cualitativa agregada.
2. **Doble conteo de la brecha cambiaria en el ITCG.** La brecha puntuaba dos
   veces dentro de reformas económicas: como indicador propio (cepo_mulc,
   40% de la dimensión) y de nuevo al 50% dentro del ILCE de apertura
   comercial (40% de la dimensión) — peso efectivo ~60% de la dimensión
   (~21% del índice), diluyendo la alícuota arancelaria a ~7%.

## Opciones consideradas

- *Solo declarar el doble conteo* (ADR-0019 4a): transparente pero deja la
  distorsión de pesos. Descartada al decidir el cambio de método.
- *Sacar cepo_mulc y dejar el ILCE*: escondía la reforma insignia dentro de
  un compuesto; el doc le da nombre y peso propio. Descartada.
- *Histéresis en las bandas*: mitigaba el parpadeo pero no el truncamiento ni
  la incertidumbre; menos limpio que interpolar. Descartada.

## Decisión

**1. Puntaje por interpolación (motor común, `parametrica.py`).** Los
umbrales institucionales del doc son ANCLAS: cada banda finita ancla su
puntaje en su punto medio, las abiertas (±inf) en su borde finito; entre
anclas el puntaje es lineal, en los extremos queda plano (sin extrapolación).
`puntaje_banda` se conserva para las etiquetas discretas de interpretación
del índice agregado. Aplica a ITCM e ITCG por igual (el ITVC ya era continuo
por diseño). Las TABLAS del doc no se tocan: cambia cómo se leen, no sus
números.

**2. Apertura comercial = alícuota efectiva.** El indicador deja el ILCE
compuesto y mide la alícuota efectiva del comercio exterior: recaudación de
derechos de importación + exportación (ARCA, en USD por el A3500 promedio)
sobre el intercambio total del ICA. La brecha cambiaria puntúa UNA vez, en
cepo_mulc. Anclas de banda elegidas SOBRE la lineal del doc (0% → 100 ·
15% → 0): (−∞,1]→100 · (1;3,5]→85 · (3,5;7]→65 · (7;11]→40 · (11,∞)→10 —
los puntos medios 2,25/5,25/9 caen exactos en esa recta, así el puntaje
interpolado la reproduce. La card muestra la alícuota en % (hoy ~4,9%:
"cada dólar de intercambio paga ~4,9% de impuestos"), más legible que un
índice compuesto. Serie backfilled desde dic-2023
(`descargar_series.fetch_alicuota_serie`); el histórico del ILCE viejo se
purgó del acumulador (regla ADR-0012 de métricas redefinidas).

**3. Sensibilidad acompañada.** Con interpolación ya no hay acantilados que
simular: el experimento de "salto de banda" del análisis de robustez se
reemplaza por **ruido de insumos ±5%** re-puntuado por la escala interpolada
(los componentes con override del analista no se perturban).

### Consecuencias

- Valores publicados al cambiar el método (2026-07-03): **ITCM 51,7 → 54,7**
  (tensión 4,8 → 4,5) · **ITCG 68,5 → 69,8** (tensión 3,1 → 3,0; interpolación
  +2,7 y salida de la brecha del ILCE −1,4 — los dos cambios se compensan casi
  por completo). Ninguna lectura cualitativa cambia de banda de interpretación.
  Apertura comercial hoy: alícuota 4,86% → puntaje 67,6, exactamente la lineal
  del doc.
- El campo `puntaje_banda` del snapshot conserva su nombre histórico pero
  desde este ADR contiene el puntaje INTERPOLADO pre-override (schema
  estable para la web y los tests).
- Los tests pineados de ITCM/ITCG se recalibraron a los valores interpolados;
  la fórmula del modal dice "Anclas {SIGLA}: … (puntaje interpolado entre
  anclas)".
- El paquete completo (este ADR + ADR-0019/0020 + estudio sombra) queda como
  expediente para validar el refinamiento con CIGOB; los umbrales
  institucionales permanecen intactos como anclas.
