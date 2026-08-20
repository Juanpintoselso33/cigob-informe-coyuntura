---
madr: 4
id: '0213'
estado: 'aceptado'
fecha: 2026-08-20
cinturon: 'transversal'
archivos: ['web/src/components/MarcoTension.astro', 'web/src/components/Hero.astro', 'tests/test_marco_conceptual.py']
modifica: ['0200']
relacionado: ['0194', '0199']
ambito: 'El bloque "Qué es la tensión" de la portada y la bajada del hero'
origen: 'Devolución de Luis Babino sobre el artifact de agosto, agosto de 2026'
---

# ADR-0213 — La portada dice qué mide cada cinturón, y la escala se explica en metodología

## Contexto y planteo del problema

[[0200-la-portada-tambien-dice-que-es-la-tension]] puso en la portada un bloque
de dos párrafos: el primero define la tensión, el segundo explica la dirección
de la escala —"0 es un cinturón aflojado y 10 uno apretado"—. La razón era
concreta: la portada muestra cinco agujas que publican un número sobre diez, y
mandar a otra página para entender la pantalla en la que ya estás es un clic de
más.

La devolución editorial de agosto de 2026 reemplazó el segundo párrafo. No lo
borró para dejar el hueco: lo cambió por la definición de **qué mide cada uno
de los cuatro cinturones** —macro, la sustentabilidad intertemporal del
proyecto; política, la capacidad de validar las normas que el proyecto
necesita; gestión, la de cumplir sus compromisos; impacto social, la de ser
validado en las urnas—.

El cambio contesta una pregunta anterior a la de la escala. Un lector que ve
cuatro agujas necesita saber primero qué son esas cuatro cosas y recién después
cómo se lee el número. Y el nombre de un cinturón no alcanza para deducirlo:
"gestión" o "impacto social" no dicen por sí solos qué capacidad del proyecto
está midiendo el índice.

El costo es real y hay que declararlo: la portada deja de explicar la escala,
que es lo que ADR-0200 fue a arreglar.

La misma devolución cambió la bajada del hero, que hasta ahora se calculaba
—contaba cinturones en rojo y armaba la frase— por una línea fija que dice qué
es el producto: *"Monitor de evaluación de Proyectos de Gobierno basado en la
metodología CIGOB-MATUS"*.

## Factores de decisión

- **La portada no puede publicar una escala muda.** Es exactamente el agujero
  que abrió [[0194-la-aguja-es-la-lectura-primaria]] y que ADR-0199 y ADR-0200
  cerraron: durante un día el sitio publicó una tensión 0-10 sin que ninguna
  página dijera qué era.
- **El bloque tiene un largo útil.** Es un aside al lado de las agujas, no un
  capítulo: sumar las cuatro definiciones y conservar los dos párrafos lo
  convierte en el párrafo institucional de seis líneas que ADR-0194 sacó con
  razón.
- **Qué mide cada cinturón no está dicho en ninguna otra parte de la portada.**
  Las cards publican el nombre y el número, no la capacidad que evalúan.
- **La bajada del hero ya no tiene que narrar el mes**: eso pasó a ser la
  lectura editorial de [[0211-la-lectura-del-mes-la-escribe-el-equipo]], y dos
  textos consecutivos contando lo mismo es la duplicación que la revisión
  adversarial del 2026-07-11 ya sacó de este mismo tramo de la página.

## Opciones consideradas

1. Las cuatro definiciones reemplazan al párrafo de la escala.
2. Conservar los dos párrafos y sumar las definiciones como tercero.
3. Las definiciones sí, y la escala comprimida a media frase.
4. Dejar el bloque como estaba.

## Decisión

**Opción 1.** El bloque de la portada queda con un solo párrafo: define la
tensión y dice qué mide cada uno de los cuatro cinturones. La dirección de la
escala **sale de la portada** y queda explicada en `/metodologia#marco`, que ya
la publica, y en la leyenda del semáforo, que publica los umbrales desde
`semaforo_cortes` ([[0181-el-color-es-la-tension-que-ya-se-publica]]).

Esto **modifica** a ADR-0200: su primera mitad —que la portada defina la
tensión por su cuenta— sigue en pie y sigue vigilada; su segunda mitad —que
explique la escala— se retira.

La bajada del hero pasa a ser fija y posicional. Con eso, `cinturonesRojos` deja
de usarse en `Hero.astro`; el chip de alerta sigue leyendo
`alerta_multicinturon`, que es otra cosa.

### Consecuencias

- Un lector que entra por la portada, mira una aguja en 4,2 y no baja a
  metodología, no tiene en pantalla qué significa ese 4,2. Es el costo aceptado.
- A cambio, ese mismo lector sabe qué mide cada cinturón sin salir de la
  portada, que antes no estaba dicho en ningún lado del home.
- La bajada del hero deja de reaccionar al tablero: si mañana hay tres
  cinturones tensionados, la portada no lo dice en el hero. Lo dicen la aguja,
  el chip de alerta y la lectura del mes.

### Confirmación

`tests/test_marco_conceptual.py` se movió con la decisión en vez de aflojarse:
sigue exigiendo que la portada defina la tensión, suma un test que exige que
**los cuatro** cinturones estén nombrados con lo que miden —con tres, la
portada define a medias un tablero de cuatro— y traslada el guard de la escala
a `/metodologia`. Si esa frase también se cayera de metodología, el test falla:
lo que no puede pasar es que no quede **ninguna** página que lo diga.

## Pros y contras de las opciones

**1. Reemplazar.** A favor: contesta la pregunta anterior sin alargar el
bloque; la escala queda explicada a un clic y con sus umbrales reales. En
contra: la portada publica un número /10 sin su referencia en pantalla.

**2. Los dos párrafos más las definiciones.** A favor: no se pierde nada. En
contra: reconstruye el bloque institucional largo que ADR-0194 sacó del hero
por ilegible, y lo pone justo donde el lector pasa de "cómo viene el mes" a
cinco números.

**3. Escala comprimida.** A favor: parece el punto medio. En contra: media
frase sobre la dirección de una escala, sin los cortes, es la clase de
explicación que ocupa lugar y no alcanza para leer el número igual.

**4. Dejarlo como estaba.** A favor: cero trabajo, ADR-0200 intacto. En
contra: deja sin decir qué mide cada cinturón, que es lo que el editor pidió y
lo que un lector nuevo pregunta primero.

## Más información

- El texto de las cuatro definiciones es el que volvió del editor, palabra por
  palabra.
- [[0199-el-marco-conceptual-vuelve-en-metodologia]] es el ADR que trajo el
  encuadre a `/metodologia`, y por eso el traslado del guard tiene destino.
