# ADR-0023 — Litigiosidad SRT al ITCG; protestas y alertas siguen de contexto

- **Fecha:** 2026-07-03
- **Estado:** aceptada (decisión del editor: revisar si los contextos de
  gestión merecían entrar al índice, espejo del ADR-0022 en macro)

## Contexto

Gestión publicaba 3 indicadores de contexto. A diferencia de macro (donde los
4 eran insumos de componentes ya puntuados), acá cada uno tenía una razón
distinta — y una sola sobrevivió al análisis:

1. **litigiosidad_laboral** (juicios SRT, % 12m vs 12m previos): la dimensión
   reforma laboral descansaba en UN único indicador (Fondo de Cese = adopción
   del *instrumento*, hoy 10/100). La litigiosidad es el *resultado* que la
   reforma persigue — el par instrumento/resultado replica IdC (capacidad) +
   crédito real (realizado) del ADR-0022. Serie de 60 meses, elocuente:
   +40/67% (2021-22) → +33/37% (2023) → +3/7% (2024-26): la industria del
   juicio se enfrió pero no se revirtió.
2. **protestas_caba** (ACLED): sigue de contexto — el ADR-0017 mantiene su
   vigencia: mide marchas y concentraciones (no cortes); puntuarlo premiaría
   "menos protesta", que es un derecho ejercido y no un resultado de gestión.
   El protocolo ya puntúa el fenómeno cortes; el contraste (protesta +25% vs
   2023 mientras los cortes caen) ES la lectura.
3. **alertas_manifestacion** (GTFS-RT): sigue de contexto — la serie nació en
   jul-2026, sin baseline 2023: no hay nada que bandear. Es el candidato a
   automatizar protocolo_antipiquetes cuando madure (ADR-0014).

## Decisión

**litigiosidad_laboral entra a la dimensión reforma laboral con 30%**
(Fondo de Cese 70%). Bandas (variación % 12m vs 12m, calibradas a la historia
2021-2026): ≤−15 → 100 · −15/−5 → 85 · −5/+5 → 65 · +5/+20 → 40 · >+20 → 10.
Caída sostenida de juicios = canal judicial desactivándose. Como proxy usa
los juicios ART (única serie nacional mensual pública), no el canal
indemnizatorio de despidos que el Fondo reemplaza — la ficha lo declara.

## Consecuencias

- Estado 2026-07-03: litigiosidad +3,6% → 57,8 interpolado. Dimensión laboral
  10,0 → **24,3** (el 10 del Fondo de Cese ya no monopoliza la dimensión:
  el instrumento no avanza, pero el resultado acompaña tibio). **ITCG 69,8 →
  72,0** (tensión 3,0 → 2,8).
- Gestión publica 15 indicadores en el índice + 2 de contexto (con razones
  documentadas, no como cajón de sastre).
- Tests: reconciliación exige litigiosidad en el índice y el contexto exacto
  {alertas, protestas}; bandas y fixture pineados (40 verdes).
