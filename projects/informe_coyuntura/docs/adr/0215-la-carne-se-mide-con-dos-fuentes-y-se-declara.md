---
madr: 4
id: '0215'
estado: 'aceptado'
fecha: 2026-08-20
cinturon: 'vida'
indicadores: [consumo_carne, consumo_carnes_total]
archivos: ['scripts/publicar.py', 'scripts/descargar_series.py', 'tests/test_carne_dos_fuentes.py']
relacionado: ['0018', '0119', '0174']
ambito: 'ITCIS · componente A de proteína animal · fuente de la card y de la serie'
origen: 'Auditoría de agosto de 2026: la card salió de SAGYP y la serie quedó en CICCRA sin que nadie lo declarara'
---

# ADR-0215 — La carne se mide con dos fuentes, y eso se declara

## Contexto y planteo del problema

El 12 de agosto de 2026, al adoptar la ficha de proteína animal, se decidió
pasar el **Componente A** —consumo de carne vacuna per cápita— de CICCRA al
tablero de SAGYP. El motivo quedó escrito en `publicar.py`: que A, B y C salgan
del **mismo PDF**, con la misma metodología de promedio móvil y el mismo corte
temporal, porque mezclarlos haría que el ratio bovina/total compare dos fuentes
distintas.

El cambio se aplicó **sólo a la card**. La serie con la que el índice rebasea a
100 = 4T-2023 siguió saliendo de CICCRA. Hoy conviven:

| | Valor | Fuente | Mes |
|---|---|---|---|
| Card de `consumo_carne` | 47,28 | **SAGYP** | junio 2026 |
| Serie que puntúa en el ITCIS | 47,5 | **CICCRA** | mayo 2026 |

No fue una decisión: **no hubo ninguna deliberación sobre la serie**. Se
reconstruyó la sesión de aquel día y el archivo de series se abrió por otro
motivo —un test exigía serie registrada para el indicador nuevo—, se agregó la
del total y la fila de `consumo_carne` quedó intacta como ancla del reemplazo.
Dos turnos después se discutió el puntaje 89,3 sin notar que venía de la fuente
que se estaba abandonando.

**Pero el resultado era forzoso ese día**, y ésa es la parte que importa: el
tablero de SAGYP es una **foto del mes**, no una serie. Publica el promedio
móvil de 12 meses vigente y lo pisa en cada edición. Mover la serie ahí habría
dejado al componente con **un solo punto** y sin nada contra qué rebasear al 4º
trimestre de 2023. CICCRA, en cambio, tiene informes mensuales cacheados desde
octubre de 2023.

Lo que hay que arreglar entonces no es la fuente: es que la divergencia esté
**declarada y vigilada**. Hoy no lo está, y sólo no salta por suerte: G3 compara
card contra serie con una tolerancia del 1% (0,47) y la diferencia entre las dos
fuentes es 0,22. El mes que se separen un poco más, el pipeline va a fallar por
una causa que nadie escribió y va a parecer un bug nuevo.

## Factores de decisión

- **Una card y su serie que salen de fuentes distintas no es ilegítimo, es
  indeclarado.** El repo ya tiene casos exentos de reconciliación con motivo
  documentado (G3_EXCEPCIONES); lo que no puede pasar es que la excepción exista
  sin estar escrita.
- **Un guard que sólo funciona por casualidad no es un guard.** Que dos fuentes
  independientes caigan dentro del 1% es una propiedad del mes, no del diseño.
- **Cambiar el anclaje es más caro que cambiar la fuente.** Los dieciséis
  componentes del índice se rebasean contra el 4T-2023; uno anclado a otra base
  se lee distinto y hay que declararlo aparte.
- **La circularidad ya se evitó una vez acá.** El corte de 112,8 kg que usa
  `_por_que_carne()` se eligió como **ancla externa** (Bolsa de Comercio de
  Rosario) y no como percentil de la propia serie. Sacar la base 2023 del mismo
  tablero de SAGYP sería reintroducir lo que ese criterio descartó.

## Opciones consideradas

1. Declarar el reparto de fuentes y ponerle un guard que avise si divergen.
2. Pasar la serie a SAGYP usando las barras anuales del tablero como base 2023.
3. Volver la card a CICCRA, deshaciendo el cambio del 12 de agosto.
4. Dejarlo como está, sin declarar nada.

## Decisión

**Opción 1.** El reparto queda como está y **se declara**:

- **Card** de `consumo_carne`: tablero de **SAGYP**, que es de donde salen
  también el total (Componente B) y el ratio (Componente C), así que la matriz
  A×B compara peras con peras.
- **Serie** que puntúa en el índice: **CICCRA**, porque es la única con historia
  mensual reconstruible hasta el 4T-2023, que es la base de todo el ITCIS.

`tests/test_carne_dos_fuentes.py` vigila las dos mitades: que cada lado siga
saliendo de donde dice este ADR, y que la distancia entre la card y el último
punto de la serie no crezca. Si crece, el test falla **antes** de que G3 bloquee
la publicación, y con un mensaje que explica por qué existen dos fuentes.

### Cuándo se revisa

No queda abierta sin criterio. Se revisa cuando se cumpla **una** de estas dos:

1. SAGYP publique una serie mensual histórica descargable que llegue al 4º
   trimestre de 2023 — en cuyo caso la serie se muda y este ADR se supersede.
2. La serie acumulada `data/vida/carnes_total_serie.json` alcance **24 puntos
   mensuales** *y* exista una base 2023 tomada de una fuente **distinta de
   SAGYP**. Los dos requisitos juntos: la acumulación empezó el 12-ago-2026 y
   por construcción nunca va a contener el 4T-2023, así que sin una base externa
   no hay contra qué rebasear, y sacarla del propio tablero sería la
   circularidad que el corte de 112,8 evitó a propósito.

Mientras tanto la acumulación sigue corriendo: es barata y es el insumo del
punto 2.

### Consecuencias

- La divergencia deja de ser un accidente silencioso y pasa a ser una excepción
  con nombre, motivo y vigilancia.
- El componente sigue puntuando 89,3 sobre la serie de CICCRA. **Este ADR no
  mueve ningún número**: sólo escribe lo que ya pasaba.
- Queda una asimetría declarada: la card publica junio de 2026 y la serie llega
  a mayo. Es la consecuencia de que las dos fuentes tengan calendarios
  distintos, y el lector ve la fecha de cada una.
- Si alguien vuelve a tocar la fuente de un lado sin el otro, el test lo agarra
  en el acto.

### Confirmación

`tests/test_carne_dos_fuentes.py`, que corre en CI junto al resto: verifica el
mapeo de la serie en `descargar_series.py`, la fuente de la card en el snapshot
publicado, y que la distancia entre ambas no supere el margen que este ADR fija.

## Pros y contras de las opciones

**1. Declarar y vigilar.** A favor: no toca el número publicado, convierte un
riesgo silencioso en uno visible, y deja escrito el criterio de revisión. En
contra: el índice sigue puntuando con una fuente distinta de la que muestra la
card, que es incómodo de explicar aunque esté declarado.

**2. Serie a SAGYP con base anual 2023.** A favor: una sola fuente para los tres
componentes, que era la intención original. En contra: cambia el anclaje de este
componente —año 2023 contra 4T-2023 del resto—, y si la base sale del propio
tablero reintroduce la circularidad que el corte de 112,8 descartó. Es una
decisión de metodología y necesita su ADR, no un arreglo de fuente.

**3. Volver la card a CICCRA.** A favor: reconcilia card y serie de la forma más
barata. En contra: rompe la matriz A×B, que es el aporte real de la ficha de
proteína animal — el ratio bovina/total volvería a comparar dos fuentes.

**4. No declarar nada.** A favor: ninguno. En contra: es el estado actual, y su
único mecanismo de defensa es que dos fuentes independientes sigan cayendo
dentro del 1%.

## Más información

- [[0119-pendientes-de-baja-prioridad-vida]] ya había medido que la vacuna sola
  sigue al total con r=0,970 en niveles y r=0,987 en cambios: distorsiona el
  nivel, no la dirección. Por eso una diferencia de fuentes de este tamaño no
  invalida la lectura, y por eso alcanza con vigilarla.
- [[0174-g3-verifica-cards-frescas]] fija el alcance de G3, que es el gate que
  hoy tapa esta divergencia sin saberlo.
