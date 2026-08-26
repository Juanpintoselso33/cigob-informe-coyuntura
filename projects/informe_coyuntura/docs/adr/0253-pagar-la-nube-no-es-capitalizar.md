---
madr: 4
id: '0253'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'macro'
indicadores: [icip]
archivos: ['scripts/macro.py', 'scripts/itcm.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'tests/test_constructos_no_prometen_de_mas.py']
relacionado: ['0009', '0262', '0264']
ambito: 'Cinturón macro · ITCM · `icip` · por qué unos pagos al exterior no son formación de capital'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «pagos transfronterizos de informática y nube suelen ser consumo intermedio; no son por sí mismos formación bruta de capital»'
---

# ADR-0253 — Pagar la nube no es capitalizar

## Contexto y planteo del problema

`icip` se llamaba **«Índice de Capitalización Inteligente y Productividad»** y se
publicaba como **«Capitalización digital»**. Su insumo principal son los **pagos
al exterior por servicios de informática** —software, nube, IA— de la balanza de
servicios del INDEC, combinados con productividad laboral (IPI/empleo).

En cuentas nacionales esos pagos son, en general, **consumo intermedio**: no son
formación bruta de capital. Pagar la licencia de la nube todos los meses es un
gasto corriente, igual que pagar la luz. Un país puede duplicar esos pagos sin
haber capitalizado nada — de hecho, la propia ficha ya declaraba la ambigüedad:
«un aumento de los pagos al exterior por software admite leerse como
digitalización o como dependencia tecnológica, y el indicador puntúa la
primera».

Esa advertencia estaba bien puesta y no alcanzaba, porque el **nombre** seguía
afirmando lo contrario. Un lector que ve «Capitalización digital» no va a la
ficha a enterarse de que no es capitalización.

## Factores de decisión

- **El nombre no puede afirmar lo que el insumo no observa.**
- **El dato sirve igual**: cuánto paga la economía por servicios digitales es
  información, y leída junto al IAI sigue contrastando inversión física contra
  gasto en digitalización.
- **Medir inversión digital de verdad es otro indicador**, no otro rótulo sobre
  éste.

## Opciones consideradas

- **A — Renombrar** a pagos/importaciones de servicios digitales, sin lenguaje
  de capitalización.
- **B — Reemplazar el insumo** por inversión en software, bases de datos y
  equipos TIC según cuentas nacionales.

## Decisión

**Opción A**, la mínima que propuso la auditoría. El indicador pasa a llamarse
**«Pagos de servicios digitales y productividad»** y desaparece el lenguaje de
capitalización e inversión digital del rótulo, de la descripción pública, de la
descripción de la dimensión y de los comentarios del código.

La sigla `icip` se conserva como identificador —no hay razón para romper la
serie y los tableros por un acrónimo— pero **su expansión cambia** y queda
declarada donde corresponde.

La opción B es el rediseño sustantivo y la auditoría misma pide no implementarlo
sin diseño previo: exige elegir una fuente de cuentas nacionales, resolver su
frecuencia y su rezago, y recalibrar la banda entera.

### Consecuencias

- **El valor, la fórmula, la banda y el peso no cambian.**
- La descripción de la dimensión `inversion` también se corrige: decía
  «inversión física y capitalización digital e intangible», y ahora distingue
  inversión física de **gasto** en servicios digitales.
- Queda anotado que el indicador combina dos cosas heterogéneas —pagos al
  exterior y productividad laboral— y que esa mezcla es anterior a esta
  corrección. No se toca acá.

### Confirmación

`tests/test_constructos_no_prometen_de_mas.py`:

- **«capitalización inteligente» y «capitalización digital» no pueden afirmarse**
  en el código ni en la capa pública;
- el rótulo habla de pagos y no de inversión;
- la razón —que son consumo intermedio— está dicha donde alguien la va a leer.

Probado rompiéndolo: repuesto el rótulo «Capitalización digital (ICIP)», fallan
dos guardas.

## Pros y contras de las opciones

### A — Renombrar

- Bueno, porque el nombre pasa a describir el insumo, y el dato se conserva.
- Malo, porque la sigla `icip` queda como un acrónimo cuya expansión cambió: hay
  que leer la ficha para saber qué significa hoy.

### B — Cambiar el insumo a cuentas nacionales

- Bueno, porque mediría inversión digital de verdad.
- Malo, porque es un indicador nuevo: otra fuente, otra frecuencia, otro rezago
  y otra banda. Sin ese diseño hecho, cambiar el insumo es peor que cambiar el
  nombre.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_macro.md`.
