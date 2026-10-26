---
madr: 4
id: '0366'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'transversal'
indice: 'todos'
indicadores: [ipc_total, emae_ia, ipi_manufacturero, rem_ipc_12m, saldo_comercial_12m, ratio_dnu, cohesion_bloque, adhesion_reformas_provincial, reduccion_estado, rigi_inversiones, cepo_mulc, apertura_comercial, protocolo_antipiquetes]
archivos: ['web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'web/src/components/IndicadorModal.astro', 'scripts/publicar.py', 'scripts/parametrica.py', 'scripts/itcm.py', 'scripts/itcg.py']
relacionado: ['0340', '0361']
ambito: 'Todo el sitio · rótulos, unidades, descripciones y fichas de índice'
origen: 'Revisiones de Luis Babino del 26-oct-2026 (macro, gestión y político) y decisión de Juan del mismo día de empezar por lo transversal y los textos.'
---

# ADR-0366 — Rótulos y textos de la revisión de octubre

## Contexto y planteo del problema

Las revisiones de Luis del 26 de octubre marcaron problemas de lectura que no
tocan ningún número: rótulos con siglas o que prometen más de lo que miden, una
frase del semáforo que nombra un corte que no se ve, escalas en otra unidad que
la tarjeta, descripciones viejas y fichas de índice que atribuyen al documento
institucional cosas que son elaboración propia.

## Factores de decisión

- Que el lector entienda la tarjeta sin conocer las siglas ni el código.
- No mover ningún número: lo que cambia el cálculo va en ADR propios.

## Opciones consideradas

- **Corregir los textos ahora, antes del Monitor general de noviembre (elegida).**
- Esperar a los cambios de cálculo y hacer todo junto.

## Decisión

- **El color se explica:** la frase del semáforo dice el límite y el color del
  otro lado («94,4 está en Amarillo, a 0,6 del límite con Verde (95,0)») y la
  línea de las anclas aclara que dan el puntaje y no el color.
- **Rótulos sin siglas y que dicen lo que miden** en los trece indicadores del
  encabezado, y unidades con su base (`% vs. un año atrás`, `% vs. diciembre de
  2023`, `% sobre el dólar oficial`, «más alto = peor» en la liquidez).
- **Escalas en la unidad de la tarjeta:** la de expectativas se muestra en tasa
  anual; los números grandes de las escalas ya no salen en notación científica.
- **Descripciones:** capacidad prestable, reservas, liquidez, resultado primario
  (con su equivalencia en PBI), crédito privado, inversión física, gasto de
  funcionamiento (incluye salarios; compara con el mismo mes de 2023), fuentes de
  la brecha y de la desregulación, cita del decreto que fija la vigencia del
  FAL, piquetes (dato de 2025, protocolo vigente), y el signo de dos indicadores
  judiciales.
- **Fichas de los índices macro y de gestión:** qué viene del documento
  institucional y qué es propio, la cifra de dependencia del IPC (31,3 %), la
  excepción de reservas, la saturación del costo del Tesoro, y el historial
  completo sin siglas.

Dos datos de las revisiones no se usaron porque no resistieron el chequeo: el
protocolo antipiquetes no está anulado (la Cámara revocó la nulidad) y el pico
del costo real del Tesoro fue 33,8 % en agosto de 2025, no 58,8 %.

Quedan afuera los rótulos que cambian con decisiones de cálculo ya tomadas
(juicios por riesgos del trabajo, recaudación de IVA y cheque, postura de la
UIA, libertad de opción en salud).

### Consecuencias

- Ningún valor, puntaje, peso ni color cambia.
- Por ser texto, llega a la edición mensual y al archivo con el rearmado.

### Confirmación

`tests/test_publicar_semaforo.py` fija la frase nueva del semáforo; las guardas
de fichas y siglas corren en la suite.

## Pros y contras de las opciones

- Ahora: el Monitor general sale entendible; algunos textos se vuelven a tocar
  cuando entren los cambios de cálculo.
- Después: un solo pase, pero el lanzamiento de noviembre llega con los errores.

## Más información

Documentos de Luis en `docs/pedidos/texto/` (macro, gestión y político del
26-oct-2026). Lista de pendientes: `docs/pendientes-monitor.md`.
