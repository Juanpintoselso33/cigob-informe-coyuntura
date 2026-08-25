---
madr: 4
id: '0240'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'politica'
indicadores: [cobertura_judicial]
archivos: ['scripts/politica.py', 'tests/test_politica_judicial.py']
relacionado: ['0126', '0220']
ambito: 'Cinturón política · ITCP · `cobertura_judicial` · qué numerador, qué denominador y a qué fecha'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «604 cargos cubiertos sobre 955, que equivale a 63,25%, no 69,63%»'
---

# ADR-0240 — El numerador viaja con su fecha

## Contexto y planteo del problema

La card de `cobertura_judicial` publicaba **69,63%** y, debajo, esta
explicación: «604 de 955 cargos de juez habilitados tienen titular designado».
604 sobre 955 es **63,25%**. El número y su explicación no eran el mismo número,
y llevaban meses así.

No era un redondeo ni un error de tipeo. Eran **dos definiciones y dos cortes**
conviviendo en la misma card:

|  | Definición | Fecha | Resultado |
|---|---|---|---|
| El porcentaje | `cargo_vacante = NO`, movido con designaciones y renuncias | corte de la corrida (25-ago-2026) | 665 / 955 = **69,63%** |
| El texto | `cargo_cobertura = Titular` | fecha del padrón (5-jun-2026) | 604 / 955 = **63,25%** |

Los dos campos existen en el padrón del Ministerio de Justicia y **no miden lo
mismo**: en el padrón del 5-jun hay 610 cargos no vacantes y 604 con titular,
porque seis tienen titular designado pero con licencia y figuran cubiertos por
subrogante. A eso se le suma que el porcentaje se mueve desde la foto del padrón
hasta hoy con 60 designaciones y 5 renuncias, mientras el texto se quedaba en la
foto.

Ninguna guarda podía verlo: `gate_calidad.py` compara la card contra el último
punto de la serie —y ahí coincidían, porque salen del mismo cálculo— pero nada
compara **una frase con el número que dice explicar**. Es la misma clase de
problema que [[0220-la-ficha-se-ata-al-colector-y-al-adr]] resolvió para las
fichas, una capa más abajo.

## Factores de decisión

- **Un porcentaje sin numerador publicado no es auditable.** Fue lo que permitió
  que las dos fechas convivieran sin que se notara.
- **El numerador y el denominador tienen que salir del mismo corte.**
- **La composición del padrón sigue siendo informativa** y no hay que tirarla:
  hay que fecharla y decir de qué es partición.
- **La reconstrucción hacia adelante necesita su inventario a la vista**, o el
  salto entre la foto y el valor parece salido de la nada.

## Opciones consideradas

- **A — Publicar 63,25%**: quedarse en la foto del padrón y no reconstruir.
- **B — Corregir sólo el texto** para que diga 665 en vez de 604.
- **C — Publicar numerador, denominador y fecha de cada cifra**, y el inventario
  de movimientos que explica la distancia entre las dos fechas.

## Decisión

**Opción C.** El valor sigue saliendo de `cargo_vacante` movido hasta el corte
—es el campo que se corresponde con lo que dice la unidad, «cargos de juez con
juez designado», y el único que los registros de designaciones y renuncias saben
mover—, pero ahora la card publica:

- `cargos_con_juez` y `cargos_totales`: el numerador y el denominador **del
  valor**;
- `fecha_corte`: la fecha de ese numerador;
- `padron_con_juez`, `padron_titular`, `padron_subrogante`, `padron_sin_cubrir`
  y `fecha_padron`: la foto de la que parte, con su propia fecha;
- `designaciones_desde_padron` y `renuncias_desde_padron`: el inventario que
  cierra la cuenta `610 + 60 − 5 = 665`.

La opción A tira una reconstrucción que está bien hecha y respaldada por dos
datasets oficiales fechados. La B arregla el síntoma y deja el porcentaje sin
numerador publicado, que es la causa.

De paso, se descartan los registros con **fecha posterior a hoy**: el dataset de
designaciones trae fechas futuras, y contarlas publicaría como cubierto un cargo
que todavía no lo está. El error no se veía porque hoy queda fuera de la
ventana; habría entrado solo el día que esa fecha llegue.

### Consecuencias

- El valor **no cambia**: sigue siendo 69,63%. Lo que cambia es que ahora se
  puede verificar sin abrir el código.
- El texto de la card pasa a describir el número que acompaña.
- Los campos `cargos_titular` / `cargos_subrogante` / `cargos_sin_cubrir` se
  renombran con el prefijo `padron_`, porque eso es lo que son.

### Confirmación

`tests/test_politica_judicial.py`, contra un padrón sintético que reproduce la
trampa real —seis cargos no vacantes con cobertura de subrogante—:

- `valor == 100 · numerador / denominador`, los dos del mismo corte;
- 665 y 604 no pueden volver a ser el mismo campo;
- 63,25% no puede volver a publicarse como explicación de 69,63%;
- las dos fechas se publican y las dos aparecen en el texto;
- `610 + 60 − 5 == 665`;
- la composición del padrón suma el **denominador**, no el numerador;
- una designación con fecha futura no adelanta cobertura;
- los órganos no habilitados quedan fuera del denominador.

Probado rompiéndolo: si el numerador vuelve a salir de `cargo_cobertura`, fallan
cuatro de las guardas.

## Pros y contras de las opciones

### A — Publicar 63,25%

- Bueno, porque el número queda atado a una foto oficial sin reconstrucción.
- Malo, porque descarta dos datasets oficiales fechados que sí describen lo que
  pasó después, y deja el indicador dos meses atrasado por diseño.

### B — Corregir sólo el texto

- Bueno, porque es una línea.
- Malo, porque el porcentaje seguiría publicándose sin numerador, que es lo que
  hizo posible el error.

### C — Numerador, denominador y fecha de cada cifra

- Bueno, porque cualquiera reproduce el número con lo que la card publica.
- Bueno, porque el desacople entre texto y valor pasa a ser testeable.
- Malo, porque la card tiene más campos y el texto es más largo.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_politica.md`.
- [[0126-el-itcp-abre-la-dimension-poder-judicial]] define el indicador y su dimensión.
