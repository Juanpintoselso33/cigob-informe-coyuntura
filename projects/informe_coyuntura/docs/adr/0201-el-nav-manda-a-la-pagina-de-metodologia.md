---
madr: 4
id: '0201'
estado: 'aceptado'
fecha: 2026-08-13
cinturon: 'transversal'
archivos: ['web/src/components/Nav.astro', 'web/src/components/Footer.astro', 'tests/test_marco_conceptual.py']
relacionado: ['0199', '0200']
ambito: 'Navegación del sitio — a dónde manda el ítem «Metodología»'
origen: 'Deuda declarada en ADR-0199 y 0200; el editor pidió cerrarla'
---

# ADR-0201 — El Nav manda a la página de metodología, no al ancla de la portada

## Contexto y planteo del problema

El ítem «Metodología» del Nav apuntaba a `/#metodologia`: la sección de la
portada, que muestra el recorrido del dato y los cuatro índices, y cierra con un
CTA al diccionario. O sea que el lector que navega por el Nav llegaba a un
resumen y tenía que dar un segundo clic para llegar a `/metodologia`, donde
viven las 73 fichas y —desde [[0199-el-marco-conceptual-vuelve-en-metodologia]]—
el marco conceptual del informe.

Las dos ADR de hoy lo dejaron anotado como deuda en vez de resolverlo, para no
mezclar navegación con contenido. Esta la cierra.

Había un segundo síntoma, más chico: el ítem declaraba `seg: '__none__'`, un
valor especial que hacía que `isActive()` devolviera `false` siempre. El único
ítem del Nav que nunca podía encenderse era, justamente, el de la única rama del
sitio con subpáginas.

## Factores de decisión

- La sección de la portada no se toca: sigue existiendo con su CTA. Lo único
  que cambia es a dónde manda el Nav.
- El ítem tiene que encenderse en toda la rama `/metodologia`, no sólo en el
  índice: cada ficha es una página propia y el lector no deja la sección al
  abrirla.
- Sin casos especiales por ítem si se puede evitar.

## Opciones consideradas

- **A. Apuntar a `/metodologia/` y encender por rama.**
- **B. Apuntar a `/metodologia/` dejando la coincidencia exacta.**
- **C. Dos ítems**, uno al ancla de la portada y otro a la página.
- **D. Dejarlo como estaba** y confiar en el CTA de la portada.

## Decisión

**Opción A.** El ítem apunta a `${base}/metodologia/` con `seg: 'metodologia'`,
y `isActive()` pasa de comparación exacta a coincidencia por rama:

```ts
return path === destino || path.startsWith(`${destino}/`);
```

Con eso desaparece el valor especial `'__none__'` —ya no lo usa nadie— y el
comportamiento para los cinco cinturones queda idéntico al anterior: no tienen
subpáginas, así que la rama y la coincidencia exacta dan lo mismo. Si alguna vez
las tienen, el ítem se comporta bien sin tocar nada.

El Footer arrastraba el mismo enlace **dos veces**, así que va en la misma
decisión: un rótulo «Metodología» no puede llevar a dos lugares distintos según
desde dónde se lo toque.

- Columna «El observatorio»: «Metodología» pasa al mismo destino que el Nav.
- Columna «Para investigadores»: eran «Metodología» (al ancla de la portada) y
  «Fichas metodológicas» — un resumen y el detalle, con el marco en ningún
  lado. Pasan a ser **«Marco metodológico»** (`/metodologia/#marco`) y «Fichas
  metodológicas» (`/metodologia/`): los dos destinos que efectivamente le
  sirven a quien viene a auditar.

### Consecuencias

- El marco conceptual queda a **un** clic desde cualquier página del sitio.
- «Metodología» se enciende también dentro de cada ficha
  (`/metodologia/itcm`, `/metodologia/ipc_total`, …), que es donde antes el
  lector perdía toda referencia de dónde estaba parado.
- La sección `#metodologia` de la portada deja de tener un enlace entrante desde
  el Nav. Sigue en la portada, se ve al scrollear y conserva su CTA; no queda
  huérfana, sí menos visitada por navegación directa.

### Confirmación

`tests/test_marco_conceptual.py::test_el_nav_manda_a_la_pagina_de_metodologia`:
el Nav no puede volver al ancla de la portada, y tiene que seguir teniendo un
ítem que apunte a `/metodologia/`. Es el mismo archivo que ya protege que el
marco esté publicado en las dos superficies: acá lo que se protege es que se
pueda llegar.

## Pros y contras de las opciones

- **A. Rama.** A favor: un clic, el ítem se enciende donde corresponde y no
  agrega casos especiales — al contrario, borra uno. En contra: cambia el
  comportamiento de `isActive()` para todos los ítems, aunque hoy sea un no-op
  para los cinturones.
- **B. Exacta.** A favor: cambio de una línea. En contra: el ítem se apaga
  apenas se abre una ficha, que es la mitad de la navegación de esa sección.
- **C. Dos ítems.** A favor: no se pierde el acceso directo a la sección de la
  portada. En contra: un Nav de siete ítems pasa a ocho, dos con el mismo
  nombre y destinos distintos — se explica peor de lo que resuelve.
- **D. Dejarlo.** A favor: cero cambios. En contra: es la deuda que 0199 y 0200
  declararon, y el pedido explícito del editor.

## Más información

- La sección de la portada la montó [[0194-la-aguja-es-la-lectura-primaria]] y
  la recortó el mismo día el refactor que mudó los controles de credibilidad a
  `/metodologia`.
- Queda abierto lo otro que anotó 0199: el h1 de `/metodologia` sigue diciendo
  «Diccionario de indicadores» cuando la página ya es el marco más el
  diccionario. Ahora que el Nav la llama «Metodología», la diferencia entre el
  rótulo del Nav y el título de la página se nota más.
