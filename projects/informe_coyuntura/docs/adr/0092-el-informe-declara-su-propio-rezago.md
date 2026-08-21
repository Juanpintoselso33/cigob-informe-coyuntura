---
madr: 4
id: '0092'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'politica'
archivos: ['publicar._rezago']
relacionado: ['0233']
ambito: 'ITCP · card pública "Rezago del índice" · `publicar._rezago`'
origen: 'Auditoría externa del cinturón político, prioridad 5'
---

# ADR-0092 — El informe declara de cuándo es la foto que muestra

## Contexto y planteo del problema

> "Conviven en el mismo cinturón indicadores casi en tiempo real con otros que
> describen una realidad de hace uno o dos años. Ambos casos están bien
> documentados en sus fichas, pero al combinarse en un único puntaje mensual
> pueden dar la sensación de que **todo el ITCP describe 'julio de 2026' cuando
> en rigor una porción relevante describe 2024-2025**."

La recomendación pedía señalizarlo **en el informe, no sólo en la ficha**.

## Opciones consideradas

- **Declarar el rezago en una card del propio índice** — elegida.
- **Separar el índice en dos lecturas**, una de pulso inmediato y otra estructural, que era lo que ofrecía la auditoría — descartada: publicar tres números donde hoy hay uno, a semanas del lanzamiento, obliga a rehacer la lectura editorial entera y cambia qué significa el número principal.

## Decisión

Se publica una card, **"Rezago del índice"**, en la misma familia visual que
"Consistencia interna": el número grande, una barra de composición del peso en
tres tramos, los indicadores que más tiran del promedio, y la consecuencia
práctica en prosa.

El cálculo vive en el pipeline (`publicar._rezago`), no en el front: los pesos
efectivos cambian cuando cambia el índice, y la card tiene que seguir siendo
cierta sin que nadie se acuerde de actualizar un número a mano.

La conclusión publicada dice lo que hay que decir:

> Un cambio de la coyuntura política no se ve de inmediato en el número. Los
> indicadores rápidos lo registran enseguida y los de ventana larga lo van
> incorporando durante los meses siguientes, de modo que el índice tiende a
> moverse después —y de forma más suave— que los hechos que lo motivan. Leerlo
> como una fotografía del mes en curso sobreestima su inmediatez.

### La opción que se descartó

La auditoría ofrecía como alternativa **separar el índice en dos lecturas**, una
de pulso inmediato y otra estructural. Se descartó: publicar tres números donde
hoy hay uno, a semanas del lanzamiento, obliga a rehacer la lectura editorial
entera y cambia qué significa el número principal. La card resuelve el problema
señalado —que el lector no confunda "dato de julio" con "situación de julio"—
sin ese costo. Queda anotada como opción disponible si el rezago promedio
crece.

### Confirmación

`test_todo_indicador_del_indice_declara_su_rezago` exige que
`REZAGO_MESES_ITCP` cubra exactamente a los indicadores que integran las
dimensiones, en los dos sentidos. Sin eso, un indicador nuevo desaparecería del
promedio y lo sesgaría en silencio hacia abajo: es la misma familia de error que
ADR-0082 —una lista escrita a mano que diverge del índice— y que volvió a
aparecer en ADR-0089 tres días después de declararla erradicada.

## Más información

### Lo que se midió

El rezago relevante no es el retraso de publicación de la fuente —eso ya estaba
en cada ficha— sino el **centroide de la ventana**: un indicador que promedia
los últimos doce meses describe, en promedio, la situación de hace seis, aunque
su último dato sea de ayer.

Los valores se derivan del diseño de cada ventana; no se estiman:

| ventana | centroide |
|---|---|
| móvil de N meses | N/2 |
| cohorte de 12 a 24 meses | 18 |
| stock acumulado | 0 (describe el estado vigente) |

Ponderando por **peso efectivo** —el que el indicador tiene realmente en el
índice una vez renormalizado, no su peso nominal dentro de la dimensión—:

| | |
|---|---|
| **rezago promedio ponderado del ITCP** | **5,8 meses** |
| peso en pulso inmediato (≤ 2 meses) | 39% |
| peso en ventana intermedia | 44% |
| peso estructural (≥ 12 meses) | **17%** |

Los dos que tiran del promedio son `eficacia_legislativa` (18 meses, por la
cohorte madura que ADR-0061 introdujo a propósito para sacar un sesgo) e
`iaf_transferencias` (12 meses, por su comparación anual dic-dic). Ninguno de
los dos es corregible sin romper lo que los hace correctos.

### Alcance y limitaciones

- **Sólo el ITCP.** El mecanismo es genérico y extenderlo a los otros índices
  cuesta declarar el diccionario de rezagos de sus componentes; no se hizo acá
  porque la auditoría que lo pide es la del cinturón político. Los otros
  cinturones tienen el mismo problema en distinta medida.
- El centroide supone que el dato se distribuye **uniformemente** dentro de la
  ventana. Para el votómetro, que pondera por recencia, es una aproximación: su
  centroide efectivo se declaró en 1 mes en lugar de la mitad de su ventana.
- El rezago de **publicación** de cada fuente sigue viviendo en su ficha y no se
  suma acá, salvo en `brecha_obra_publica`, donde el retraso del INDEC es
  material frente al ancho de la ventana.
