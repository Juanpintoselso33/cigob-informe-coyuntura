---
madr: 4
id: '0345'
estado: 'aceptado'
fecha: 2026-10-07
cinturon: 'vida'
indice: 'ITVC'
indicadores: [icg_utdt]
archivos: ['scripts/itvc.py', 'scripts/publicar.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', 'scripts/panel_validacion.py', 'scripts/procedencia_anclas.py', 'config.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
relacionado: ['0245', '0248', '0314', '0336', '0344']
ambito: 'Cinturón impacto social · ITCIS · entra `icg_utdt` en «Confianza y percepción»; el ITCP pierde su factor común de validación'
origen: 'Reunión del 6-oct-2026 sobre el Monitor (punto 5 de docs/261006_reunion_pendientes.md): «agregar el Índice de Confianza en el Gobierno de la UTDT a vida cotidiana».'
---

# ADR-0345 — La confianza en el Gobierno entra al índice de impacto social

## Contexto y planteo del problema

La dimensión «Confianza y percepción» del índice de impacto social (8,25 %) quedó
vacía en agosto de 2026, cuando se suspendió `sentimiento_digital` (ADR-0248).
`itvc.py` la dejó declarada a propósito para que un componente de confianza
tuviera dónde entrar. La reunión del 6-oct-2026 pidió sumar el Índice de
Confianza en el Gobierno de la UTDT como card que puntúa. La serie ya se
descargaba (`icg_utdt`, mensual desde nov-2001, escala 0-5), pero sólo como
referencia externa del índice político.

## Factores de decisión

- «O integra el índice, o no es card» (ADR-0153/0216): entra puntuando.
- Una estadística del panel de validación no puede ser componente de ningún
  índice (`test_panel_validacion.py`).
- Mismo tratamiento que el resto de los componentes del índice de impacto social.
- El rezago se mide: último dato al 7-oct, sep-2026 = 1,937, con 36 días.

## Opciones consideradas

1. Entrar en «Confianza y percepción», rebaseado a 4T-2023 como el resto.
2. Entrar con una base propia (diciembre de 2023 o la mediana histórica).
3. No sumarlo y dejar la dimensión vacía.

## Decisión

**Opción 1.**

- **Dimensión y peso.** `percepcion` pasa a `{"icg_utdt": 0.5,
  "sentimiento_digital": 0.5}`. Con el sentimiento suspendido, el mecanismo de
  ADR-0245 lo saca del cálculo y el ICG absorbe su mitad: hoy pesa el 8,25 %
  entero. Si el sentimiento reingresa, el reparto lo fija su propio ADR.
- **Escala y base.** No se invierte (más confianza es mejor). Se rebasea al
  promedio de 4T-2023, la base de todos los componentes. Ese trimestre mezcla
  dos gobiernos (oct-nov en 1,2-1,4; dic en 2,86), pero lo mismo vale para el
  resto y una base propia haría de este componente un caso aparte. Con base
  4T-2023 el ICG vale 105,8; con diciembre sólo valdría 67,8.
- **Tope de demora.** `MAX_DIAS["icg_utdt"] = 90`: el dato se fecha el 1 del mes
  y sale 3-4 semanas después, así que llega normalmente con 55-60 días.
- **Serie.** Pasa de `gestion.csv` a `vida_cotidiana.csv`.
- **Validación.** Sale del panel (familia itcp, factor del ITCP). El ITCP queda
  con una sola estadística propia (EPU) y **pierde su factor común**, como el
  ITCG en ADR-0336; la correlación con EPU se sigue publicando.

### Consecuencias

- El índice de impacto social pasa de 92,5 a ≈93,6 (tensión 6,5 → 6,3) con los
  datos de septiembre.
- La validación del índice de impacto social contra la confianza del consumidor
  de la misma universidad queda en parte contaminada: ICG e ICC correlacionan
  0,78 en cambios mensuales desde dic-2023 (0,20 en niveles). Se declara en la
  ficha.
- El ICG mide popularidad, el argumento que lo sacó del cinturón político en
  mayo de 2026. Acá entra por otra razón: es la percepción de los hogares, con
  un peso chico frente a las condiciones materiales.
- El Monitor vuelve a 67 cards (ADR-0344 había dejado 66).

### Confirmación

Las pruebas del ITCIS verifican la dimensión y los pesos;
`test_la_ficha_no_se_queda_atras.py` exige la ficha y la entrada de este ADR;
`test_panel_validacion.py` exige que ninguna estadística del panel sea componente.

## Pros y contras de las opciones

### Opción 1 — Base 4T-2023

- Bien: mismo tratamiento que todo el índice.
- Mal: la base mezcla dos gobiernos.

### Opción 2 — Base propia

- Bien: evita el promedio mixto.
- Mal: el resultado depende mucho de la base elegida (67,8 a 105,8) y rompe la regla común.

### Opción 3 — No sumarlo

- Mal: no responde al pedido y deja una dimensión declarada sin componentes.

## Más información

- ADR-0245 y ADR-0248: el mecanismo de suspensión y el sentimiento digital.
- ADR-0314: la confianza del consumidor como referencia externa del índice.
- ADR-0336: el ITCG sin factor común.
- ADR-0344: sale el Votómetro, el otro cambio del mismo pedido.
