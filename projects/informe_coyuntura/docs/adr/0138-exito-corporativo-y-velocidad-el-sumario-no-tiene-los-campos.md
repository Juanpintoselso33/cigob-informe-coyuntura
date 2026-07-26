# ADR-0138 — Éxito corporativo y velocidad: el sumario no tiene los campos

- **Estado**: Aceptado
- **Fecha**: 2026-07-26
- **Ámbito**: cinturón político (ITCP), bloque judicial
- **Relacionados**: ADR-0135 (cautelares: no hay censo de causas), ADR-0131

## Contexto

Cierra los dos últimos indicadores judiciales del aporte externo:

- **Éxito Corporativo** — con qué frecuencia las grandes empresas ganan sus
  pleitos contra el Estado. ADR-0131 anotó que faltaba «scraper + listado de
  razones sociales».
- **Velocidad de Resolución** — cuánto tarda la Justicia en resolver causas
  sensibles. Faltaba «scraper + definición de causa sensible».

Los dos dependen del universo de causas que ADR-0135 ya evaluó. Este ADR agrega
lo que faltaba verificar: **qué campos trae realmente un documento de SAIJ**, y
si hay estadística de duración publicada en otro lado.

## Lo que se encontró

### El sumario de SAIJ no tiene los campos que hacen falta

Inspeccionados los documentos de la consulta de cautelares contra el Estado, el
`documentAbstract` trae exactamente esto:

```
numero-sumario · fecha · titulo · texto · descriptores
jurisdiccion · tipo-tribunal · fecha-umod · uuid · friendly-url
```

**No hay carátula. No hay partes. No hay fecha de inicio de la causa. No hay
campo de resultado.** Y el `titulo` no es el nombre del caso: es la lista de
descriptores concatenada («Medidas cautelares, Estado Nacional, interés público,
deberes del juez»).

Las consecuencias son directas:

- **Velocidad de Resolución es estructuralmente imposible desde SAIJ.** Hay una
  sola fecha, la de la sentencia. Una duración necesita dos.
- **Éxito Corporativo no tiene de dónde sacar ni la empresa ni el resultado.**
  Ambos habría que inferirlos leyendo el `texto` libre de cada sumario, sobre la
  base curada y no censal que ya documentó ADR-0135.

### No hay estadística de duración publicada

- **`csjn.gov.ar/transparencia/estadisticas`** responde 200 pero es una página de
  navegación: **cero archivos descargables**, y lo que enlaza es presupuesto,
  recursos, adquisiciones y contrataciones. Transparencia presupuestaria, no
  estadística de causas.
- **`consejomagistratura.gov.ar/index.php/estadisticas/`** tiene 18 PDF, y son
  reglamentos, digestos, resoluciones y listados de magistrados. El único con
  cara de estadística es `analisis-estadisticos-gastos-e-inversiones-pjn.pdf`
  — **gastos**, no duración.
- **`Oralidad en los procesos civiles`** (datos.jus / datos.gob), el único
  dataset que aparece buscando «duración», es de justicia civil y comercial
  **provincial** (Buenos Aires, Santa Fe, Entre Ríos, Córdoba, San Juan,
  Santiago del Estero). No es el fuero ni el fenómeno.
- Búsquedas por «duración», «tiempo resolución», «pendientes tribunales» y
  «expedientes duración» en ambos portales: nada más.

## Decisión

**No se construye ninguno de los dos.** Se registra el negativo con las consultas
hechas, para que sea auditable y nadie repita el camino:

| indicador | bloqueo |
|---|---|
| Velocidad de Resolución | **estructural**: no existe fecha de inicio de causa en ninguna fuente consultable, y no hay estadística de duración publicada para el fuero federal/nacional |
| Éxito Corporativo | sin campo de partes ni de resultado; habría que inferir ambos del texto libre, sobre la base curada y no censal de ADR-0135 |

Con esto queda **cerrado el bloque judicial del aporte externo**: de los cinco
indicadores judiciales, uno resultó construible (`cobertura_judicial`, ADR-0126,
ya en el índice), uno quedó relevado y a la espera de decisión editorial
(parálisis de denuncias, ADR-0134), uno es construible con salvedad
(judicialización, ADR-0135) y tres no se pueden con las fuentes disponibles
(veto de constitucionalidad —ADR-0131—, bloqueo cautelar y estos dos).

## Consecuencias

- **Lo que destrabaría a los tres es lo mismo**: un censo de causas del fuero
  contencioso administrativo federal con carátula, fechas de inicio y de
  resolución, y resultado. Hoy no existe públicamente. Si en algún momento el
  PJN publica su datastore de causas, los tres se reabren juntos — conviene que
  quede escrito acá y no descubrirlo de nuevo.
- **No se descarta la vía de pedido de acceso a la información pública.** El
  Consejo de la Magistratura publica solicitudes de acceso; nada impide pedir la
  estadística de causas del fuero. Es una vía con plazos y sin garantía, o sea
  incompatible con un indicador de actualización mensual, pero sirve para una
  nota metodológica o un informe puntual.
