---
madr: 4
id: '0335'
estado: 'aceptado'
fecha: 2026-10-07
cinturon: 'politica'
indice: 'ITCP'
indicadores: [apoyo_empresario]
archivos: ['scripts/politica.py', 'web/src/lib/fichas.ts', 'tests/test_politica_apoyo_empresario.py', 'tests/test_apoyo_corpus_cerrado.py']
relacionado: ['0334']
ambito: 'Cinturón política · ITCP · `apoyo_empresario` · cuántos comunicados hacen falta para publicar el saldo de un mes'
origen: 'Punto flojo que ADR-0334 dejó anotado a propósito: con una sola cámara, nueve de los treinta meses quedaban con uno o dos comunicados en su ventana.'
---

# ADR-0335 — El saldo empresario necesita al menos tres comunicados

## Contexto y planteo del problema

`apoyo_empresario` es el saldo `(apoyos − críticas) / (apoyos + críticas)` de
los comunicados de la Unión Industrial en una ventana móvil de doce meses. Desde
ADR-0334 mide una sola cámara, y nueve de los treinta meses de la serie quedaban
con uno o dos comunicados en su ventana. Con dos observaciones el saldo sólo
puede valer −1, 0 o +1: los tres primeros meses daban −1,0 sobre dos
comunicados, con una precisión aparente de tres decimales que no existe.

## Factores de decisión

- Que un punto publicado se pueda leer como una postura y no como el azar de
  uno o dos comunicados.
- No inventar datos: un mes sin base suficiente se omite, no se rellena.
- Que el dato vigente no cambie por esta regla si su ventana tiene base.

## Opciones consideradas

1. Mínimo de tres comunicados computables por ventana.
2. Mínimo de cinco.
3. Publicar todo, con una marca de «base chica».

## Decisión

**Opción 1.** `APOYO_MIN_OBSERVACIONES = 3` en `scripts/politica.py`: un mes se
publica sólo si su ventana de doce meses tiene al menos tres comunicados
computables. Tres es el mínimo que deja de estar atado a −1, 0 y +1 sin vaciar la
serie.

### Consecuencias

- La serie pasa de 29 meses a 20 y arranca en agosto de 2024 en vez de abril. Los
  meses intermedios sin base quedan como huecos.
- El dato vigente no cambia: agosto de 2026, −0,25.
- Si la Unión Industrial publica poco durante un año, la card se queda sin dato
  nuevo y la frescura lo marca, en vez de mostrar un saldo de dos comunicados.

### Confirmación

`tests/test_politica_apoyo_empresario.py` fija el arranque en 2024-08 y exige que
la card vigente salga de una ventana con al menos el mínimo;
`tests/test_apoyo_corpus_cerrado.py` usa fixtures con base suficiente en cada
corte que afirma.

## Pros y contras de las opciones

### Opción 1 — Tres comunicados

- Bien: saca los saldos de −1,0 sobre dos comunicados y conserva veinte meses.
- Mal: deja huecos en la serie.

### Opción 2 — Cinco comunicados

- Bien: más robusto.
- Mal: con una sola cámara vacía buena parte de la serie.

### Opción 3 — Publicar con marca

- Bien: no pierde puntos.
- Mal: el punto sin base sigue entrando al índice con su peso entero.

## Más información

- ADR-0334: AEA sale del perímetro y deja anotado este punto flojo.
