---
madr: 4
id: '0133'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'transversal'
archivos: ['gate_calidad.py', 'data-pipeline.yml', 'requirements.txt']
relacionado: ['0172', '0176', '0191', '0210']
continuado_por: ['0173', '0174', '0227']
ambito: '`gate_calidad.py` · `data-pipeline.yml` · `requirements.txt`'
origen: 'El cron falló tres noches seguidas; planteo del editor'
---

# ADR-0133 — Una fuente demorada no puede tirar abajo el pipeline

## Contexto y planteo del problema

### Lo que pasó

El pipeline nocturno venía fallando **tres noches seguidas** (24, 25 y 26 de
julio). Cada vez, la falla aparecía en el paso de pytest y **el commit del
snapshot no llegaba a ejecutarse: no se publicaba nada**.

La causa de anoche fue mía, del mismo día: incorporé `pypdf` y `pymupdf` para
leer los informes del Ministerio de Desregulación (ADR-0125) y **nunca los
agregué a `requirements.txt`**. En CI:

1. `gestion.py` reventaba con `ModuleNotFoundError`,
2. el paso de colectores **igual daba OK** —captura el exit code pero nunca
   corta—,
3. la serie de desregulación quedaba vacía,
4. y la falla aparecía **tres pasos después** como
   `la matriz publicada mide 73 pares y la reconstrucción da 61`.

Un error de dependencia se presentó como una discrepancia de matriz. Es el peor
tipo de síntoma: no apunta a la causa y manda a investigar al lugar equivocado
—cosa que efectivamente pasó la noche anterior, cuando diagnostiqué el problema
de la matriz sin ver que abajo había un crash.

## Opciones consideradas

- **Que el gate distinga integridad de demora** — elegida.
- **Que cualquier falla del gate corte la publicación** — descartada: incluía G2, una fuente que publicó tarde, que no compromete la integridad de nada.
- **Agregar `pypdf` y `pymupdf` a `requirements.txt`** — sin eso el indicador de desregulación nunca funcionó en CI, sólo en la máquina donde se desarrolló.

### Confirmación

`test_gate_bloqueante_vs_demora.py` verifica que G2 quede fuera de los
bloqueantes y que una demora sola devuelva 0. **Si alguien vuelve a meter la
frescura entre las fallas que cortan, el pipeline entero vuelve a caerse porque
una fuente publicó tarde, y el test lo marca antes.**

## Decisión

### Tres cambios

### 1. Las dependencias que faltaban

`pypdf` y `pymupdf` entran a `requirements.txt`. Sin eso el indicador de
desregulación **nunca funcionó en CI**, sólo en la máquina local donde se
desarrolló.

### 2. El gate distingue integridad de demora

Hasta ahora **cualquier** falla del gate cortaba la publicación. Eso incluye
G2 —una fuente que publicó tarde—, que no tiene nada que ver con que el
snapshot esté bien o mal armado.

| tipo | ejemplo | ¿corta? |
|---|---|---|
| **Integridad** | G1 indicador sin valor · G3 card ≠ serie · G6 jerga interna en texto público | **sí** |
| **Demora** | G2 una fuente atrasada respecto de su tope | **no** |

> **Corrección (ADR-0227, 21-ago-2026).** El párrafo que sigue es **falso** en
> su premisa, aunque la decisión que justifica sigue siendo la correcta. Una
> fuente que se atrasa **no** deja al indicador marcado `desactualizado`: ese
> flag lo escribe el colector cuando el fetch falla y sirve caché, y una card
> demorada con el fetch sano lo tiene en `false`. No hay carry-forward. El
> motivo real por el que la demora no debe bloquear es otro y es más simple:
> **el valor publicado es el último que la fuente llegó a sacar**, no un valor
> arrastrado. Ver [[0227-demorada-no-es-desactualizada]].

El razonamiento: cuando una fuente se atrasa, el indicador **ya queda marcado
`desactualizado`**, `publicar.py` hace carry-forward del último valor bueno y el
tablero lo muestra como viejo. **El lector no se entera de nada falso.** Frenar
la publicación entera por eso deja el informe sin actualizar *nada* —incluidos
los sesenta y tres indicadores que sí están frescos—, que es estrictamente peor
que mostrar un dato viejo señalado como viejo.

Lo que sí bloquea es que el snapshot **afirme algo que no es cierto**: un
indicador sin valor, una card que no coincide con su propia serie, jerga interna
filtrada al texto público.

### 3. Un crash de script deja de disfrazarse de dato

Los colectores usan sus exit codes como información, no como error:
`0` todo fresco · `1` mixto · `2` todo caché. Una fuente caída es normal.

**Un código mayor a 2 no es una condición de datos: es un crash.** Ahora se
distinguen: el paso emite `::error::` señalando qué script se cayó y corta ahí
mismo, en vez de dejar que el efecto aparezca disfrazado tres pasos más abajo.

## Más información

### Lo que esto NO arregla

- **No hace resiliente al colector.** Si `gestion.py` crashea, se sigue
  perdiendo la actualización de todo ese cinturón. Lo que cambia es que ahora se
  ve *dónde* y *por qué*, en vez de descubrirlo por un síntoma lejano.
- **No revisa las demás dependencias.** `requirements.txt` se corrigió con las
  dos que faltaban hoy; no se auditó si hay otras usadas sólo en local.
- **El gate sigue siendo binario por indicador.** Un indicador o pasa o no; no
  hay grados.
