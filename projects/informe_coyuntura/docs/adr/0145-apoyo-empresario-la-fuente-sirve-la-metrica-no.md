---
madr: 4
id: '0145'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'politica'
indicadores: [sector_privado, apoyo_empresario]
corregido_por: ['0148']
ambito: 'cinturón político (ITCP) · dimensión `sector_privado`'
---

# ADR-0145 — Apoyo empresario: la fuente sirve, la métrica no

- **Relacionados**: ADR-0131 (protocolo), ADR-0139 (AEA como fuente), ADR-0136
  (por qué ADEBA no servía), ADR-0088 (`sector_privado`)

> **⚠️ CORREGIDO POR ADR-0148.** La conclusión de este ADR («no sirve») fue
> revertida al hacer lo que él mismo señalaba como único camino: **sumar
> cámaras**. Con UIA —57 comunicados desde dic-2023, en `uia.org.ar/prensa/{id}/`—
> los computables pasan de 2 a 16, los meses con `n=1` de 20 a **cero** y los
> meses vacíos de 5 a **cero**. El método de este ADR fue correcto; lo que
> faltaba era volumen. Leer ADR-0148.

## Contexto y planteo del problema

### Qué se hizo

Se construyó el indicador **Apoyo Público** de la revisión externa, siguiendo el
protocolo de ADR-0131 en orden: **reglas de inclusión escritas antes de ver los
datos**, universo relevado, primera pasada de codificación completa, métrica
calculada. Recién entonces se evaluó si servía.

**No sirve**, y conviene decir con precisión por qué: no falló la fuente, ni las
reglas, ni la codificación. Falló la **frecuencia del fenómeno**.

## Opciones consideradas

- **Conservar la fuente y buscarle otra métrica** — elegida: no falló la fuente.
- **Publicar la métrica de apoyo empresario sólo con AEA** — descartada por sus propios números, en vez de sostenerse porque ya estaba construida.

## Decisión

1. **No se incorpora al ITCP.** `sector_privado` sigue con
   `brecha_obra_publica` como único indicador.
2. **La fuente y el registro quedan versionados** —`apoyo_empresario_reglas.json`
   y `apoyo_empresario_codificacion.json`, con los 46 casos, su codificación y
   su motivo—, porque son reutilizables y porque el negativo tiene que ser
   auditable.
3. **No se pidió la segunda pasada.** El kappa habría medido la concordancia de
   una métrica que ya se sabe inservible; hacerle gastar el tiempo a otra persona
   para eso no se justifica. Si el punto se retoma con más cámaras, la segunda
   pasada vuelve a ser obligatoria.

### Consecuencias

46 comunicados de AEA entre mar-2020 y mar-2026, codificados en dos ejes
—postura y destinatario— como exige ADR-0136:

| postura | | destinatario | |
|---|---|---|---|
| neutro | 28 | externo o propio | 19 |
| crítica | 12 | **ejecutivo nacional** | **18** |
| apoyo | 5 | provincias/municipios | 4 |
| dudoso | 1 | congreso | 3 |
| | | judicial | 2 |

**Computables** (Ejecutivo nacional **y** con postura): **13 en seis años**, y
**sólo 2 bajo este gobierno** (Pacto de Mayo mar-2024, acuerdo con el FMI
abr-2025).

La serie de saldo en ventana de 12 meses lo muestra sin ambigüedad:

- **20 de 32 meses dan exactamente +1,00, y en todos `n = 1`.** El «saldo de
  postura» no es un saldo: es el eco del único comunicado que quedó dentro de la
  ventana.
- **Los últimos cuatro meses están vacíos.** El indicador no tiene valor actual.

Un indicador cuyo valor lo decide la presencia o ausencia de un solo documento
no mide postura empresaria: mide el calendario de publicación de una entidad.

## Más información

### Las reglas mordieron, y ése era el punto

Tres casos donde la regla escrita de antemano contradijo la expectativa. Se
registran porque son la prueba de que el protocolo sirve:

1. **«AEA felicita al Presidente electo Javier Milei» quedó NEUTRO.** La regla
   dice que una felicitación electoral no comenta una medida de gobierno. Es el
   comunicado más citable del período y no computa.
2. **«Un paso muy importante» (Ley Bases aprobada en Diputados) quedó con
   destinatario CONGRESO**, por la regla de «dónde se resuelve el asunto». Es el
   apoyo más visible a la agenda del Gobierno y tampoco computa.
3. **El consenso fiscal de dic-2021 quedó como PROVINCIAS**, por gravar Ingresos
   Brutos. Es exactamente el error que hundió a ADEBA en ADR-0136 —contar como
   crítica al Gobierno una crítica a los distritos— y acá no ocurrió porque el
   eje destinatario es obligatorio.

Sin esas tres reglas el indicador habría «funcionado» mucho mejor y habría estado
midiendo otra cosa.

### El único camino que queda, y lo que cuesta

**Sumar cámaras.** UIA, CAMARCO y SRA tienen secciones de prensa vivas (ADR-0139;
SRA está en `sra.ar`, no en el dominio viejo). Con cuatro o cinco entidades el
volumen computable podría multiplicarse por cuatro, lo que bajo este gobierno
daría del orden de diez eventos en vez de dos. Sigue siendo poco, pero deja de
ser una serie de `n = 1`.

Es trabajo real: scraping por sitio, y una pasada de codificación completa por
cámara con su segunda pasada correspondiente. **No se hace ahora**, y queda dicho
que el resultado tampoco está garantizado — puede que el conjunto siga siendo
demasiado infrecuente.

### Lo que este ADR deja probado, más allá del indicador

Que el protocolo de ADR-0131 funciona como control y no como trámite: escribir
las reglas antes evitó tres decisiones que habrían inflado el indicador, y la
métrica se descartó por sus propios números en vez de sostenerse porque ya estaba
construida.
