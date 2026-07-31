---
madr: 4
id: '0140'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'politica'
corrige: ['0131']
ambito: 'cinturón político (ITCP), bloque judicial'
origen: 'el editor pidió buscar alternativas en lugar de aceptar el cierre.'
---

# ADR-0140 — El dato existe y está mejor modelado de lo que suponíamos

- **Corrige el encuadre de**: ADR-0131 (veto de constitucionalidad), ADR-0135 y
  ADR-0138 (bloqueo cautelar, éxito corporativo), ADR-0139

## Opciones consideradas

- **`sj.csjn.gov.ar`** — elegida: es el sucesor que señala el propio archivo.
- **El CIJ** — descartado como fuente viva: está congelado, y cualquier indicador construido sobre él se corta.

## Decisión

1. **No se construye ningún indicador de conteo todavía.** Tres puertas, las tres
   cerradas del mismo modo: el buscador de fallos por CAPTCHA, el de causas del
   PJN por CAPTCHA, y el JSON abierto por un tope de 10 registros. No se resuelven
   CAPTCHAs ni se buscan rodeos: es el organismo diciendo que el acceso es para
   consumo humano.
2. **Se corrige el encuadre.** El estado de los tres indicadores no es «no hay
   fuente» ni «el dato no existe» sino **«el dato existe, está bien modelado y el
   acceso está limitado»**. La diferencia es operativa, no retórica: cambia qué
   hay que hacer para destrabarlos.
3. **Queda planteado un pedido de acceso a la información pública que ahora puede
   ser preciso**, porque se conoce el modelo: *cantidad de fallos con el atributo
   `inconstitucional = true` por año, 1994-2026*, o *exposición del resultado del
   buscador de fallos en formato JSON*. Es pedible justamente porque el campo ya
   existe y el organismo ya lo calcula — no se le pide que construya nada.
4. **Hay algo construible ya**: un **detector** sobre el endpoint JSON abierto,
   que vigile las novedades y marque las que traen `inconstitucional = true` o
   carátula con el Estado como parte. No es un contador y no puede serlo con 10
   registros, pero es el mismo patrón de ADR-0129 (privatizaciones): elimina el
   riesgo de omisión y deja la clasificación al analista.

### Consecuencias

- **`sjconsulta` no estaba roto.** ADR-0138 lo dio por caído con un HTTP 500 sobre
  `buscar.html`, que es el destino del POST, no la página de consulta. Tercera vez
  que un negativo sale de una URL adivinada — ya está en
  `feedback_no_declarar_fuente_inexistente` y se refuerza acá.
- **El CIJ hay que sacarlo de cualquier plan futuro**: está disuelto.
- Mapa de acceso completo, con endpoints, parámetros, campos y límites
  verificados, en `data/politica/csjn_jurisprudencia_mapa_de_acceso.json`, para
  que quien retome esto no vuelva a recorrer el camino.

## Más información

### Resumen

**El modelo de datos de la CSJN contiene exactamente lo que los tres indicadores
bloqueados necesitan.** Lo que está limitado es el acceso público, no la
existencia ni la calidad del dato. Es una conclusión distinta de «no hay fuente»
y apunta a un desbloqueo concreto y pedible.

### El CIJ murió, y eso hay que saberlo

El Centro de Información Judicial fue creado por Acordada 17/2006 y **disuelto
por la Acordada 10/2025**, que convierte el sitio en un repositorio histórico
congelado. Cualquier indicador construido sobre el CIJ se corta. Queda descartado
como fuente viva — y el propio archivo señala al sucesor: `sj.csjn.gov.ar`.

De paso: ADR-0138 probó `sjconsulta.csjn.gov.ar/sjconsulta/consultaSumarios/`
**`buscar.html`** y obtuvo HTTP 500, del que concluyó que el buscador de la CSJN
estaba roto. La ruta es **`consulta.html`**; `buscar.html` es el destino del POST.
Otro negativo por una URL adivinada.

### Lo que sí está publicado

### El buscador de fallos completos tiene el campo exacto

`sjconsulta.csjn.gov.ar/sjconsulta/fallos/consulta.html` cubre **FALLOS COMPLETOS
1994-2026**, actualizado al 07/07/2026, con un formulario que incluye:

| campo | para qué sirve |
|---|---|
| **`inconstitucional`** | casilla «Sentencias que declaran Inconstitucionalidad» |
| `arbitraria` | sentencia arbitraria |
| **`partes`** | búsqueda por partes del juicio |
| **`sentidoPronunciamiento`** | el sentido del fallo, o sea el resultado |
| `camara`, `jurisdiccion`, `tipoRecurso` | recorte por fuero |
| `fechaDesde` / `fechaHasta` | ventana temporal |

**Esto obliga a reencuadrar ADR-0131.** Ese ADR concluyó que el veto de
constitucionalidad «no puede ser un conteo» porque la búsqueda de texto en SAIJ
traía pagarés, honorarios y un remedio procesal provincial. El problema era **la
búsqueda de texto**, no el concepto: la Secretaría de Jurisprudencia de la CSJN
tiene «sentencia que declara inconstitucionalidad» como **atributo controlado del
fallo**. El indicador que propuso el aporte externo está oficialmente
operacionalizado.

El formulario lleva `g-recaptcha-response`, y el POST sin token devuelve HTTP 500.
Gate aplicado; ahí se detiene el trabajo automatizado.

### Y hay un endpoint JSON sin CAPTCHA

`POST /sjconsulta/novedades/buscar.html` (tomando sesión con un GET previo a
`/novedades/consulta.html` y con `X-Requested-With: XMLHttpRequest`) devuelve
jTable limpio:

```json
{"idAnalisis":"830107",
 "identificadorExpediente":"CAF 024580/2022/1/RH001",
 "fecha":"07/07/2026",
 "caratula":"EN-M ECONOMIA Y OTRO c/ BUNGE ARGENTINA SA s/INHIBITORIA",
 "materia":"ADMINISTRATIVO - COMPETENCIA - TRIBUTARIO/ADUANERO",
 "inconstitucional": false, "sentenciaArbitraria": true, ...}
```

Trae **carátula con las partes**, **prefijo de fuero** en el expediente (CAF =
Contencioso Administrativo Federal), fecha, materia, síntesis, y los **booleanos
`inconstitucional` y `sentenciaArbitraria`**. Es decir: todo lo que ADR-0138
declaró inexistente («no hay carátula, no hay partes, no hay resultado») existe
—en la CSJN, no en SAIJ— y viene en JSON.

Los endpoints de detalle `getSintesisAnalisis.html?idAnalisis=N` y
`getSumariosHoldingByAnalisis.html?idAnalisis=N` también responden sin CAPTCHA,
con `voces` del tesauro controlado.

**El límite**: devuelve como máximo **10 registros**, y `TotalRecordCount`
siempre informa 10. Es el módulo de *novedades* (últimos destacados), no un
buscador del corpus. La búsqueda por texto discrimina —consultas distintas traen
fallos distintos— pero no se puede contar ni paginar: se probaron
`jtStartIndex`/`jtPageSize`, `start`/`length` y `pagina`, sin efecto. Los IDs
tampoco se pueden barrer: 829902 responde y 829901 devuelve lista vacía.
