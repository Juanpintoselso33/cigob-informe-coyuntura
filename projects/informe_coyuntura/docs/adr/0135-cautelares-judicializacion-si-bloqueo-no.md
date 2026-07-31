---
madr: 4
id: '0135'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'politica'
ambito: 'cinturón político (ITCP), bloque judicial'
---

# ADR-0135 — Cautelares: judicialización sí, bloqueo cautelar no

- **Relacionados**: ADR-0131 (protocolo del bloque judicial, y **corrección** a su
  anexo), ADR-0042 (nacer discriminando), ADR-0134 (parálisis de denuncias)

## Contexto y planteo del problema

El aporte externo propone dos indicadores que ADR-0131 dejó pendientes y anotó
como «CSJN/Cámaras (sin API)», señalando que **comparten el universo de causas**:

- **Bloqueo Cautelar** — cuánto frena la Justicia las políticas del Gobierno por
  vía de medidas cautelares.
- **Judicialización** — cuánta de la agenda pública termina dirimiéndose en
  tribunales.

Ese «sin API» era una anotación mía sin verificar a fondo. Este ADR la reemplaza
por un relevamiento hecho: se probaron SAIJ, la consulta de sumarios de la CSJN,
el sistema de consulta de causas del PJN, el CIJ y datos.jus.gob.ar.

### El conteo crudo mide a SAIJ, no a la Justicia

Sumarios de jurisprudencia que mencionan «medida cautelar», por año:

```
2016:  69      2019: 185      2022: 258      2025: 309
2017: 122      2020: 249      2023: 346      2026: 113 (parcial)
2018: 195      2021: 350      2024: 339
```

Las cautelares no se quintuplicaron entre 2016 y 2021. **SAIJ publica sumarios
curados, no el universo de sentencias**, y lo que se mueve ahí es cuánto sumarió
cada año. Cualquier indicador que cuente documentos de SAIJ sin dividir por la
cobertura del año mide productividad editorial del organismo.

### Hay una faceta de jurisdicción, y resuelve el problema de ADR-0131

SAIJ facetea por `Jurisdicción` (Local / Federal / Nacional / Internacional).
Eso separa directamente la contaminación provincial que arruinó el caso del veto
en ADR-0131, donde «recurso de inconstitucionalidad» resultó ser un remedio
procesal provincial.

En cambio **no existe faceta de descriptor**, aunque cada documento traiga su
tesauro controlado en el abstract. Sólo hay texto libre. Es una limitación de la
fuente, no del protocolo.

### Normalizado y restringido a jurisdicción federal, queda una serie usable

Sumarios con «medida cautelar» sobre el total de sumarios, ambos en jurisdicción
Federal + Nacional:

| año | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| densidad | 0,56% | 0,61% | 1,03% | 0,91% | 1,53% | 1,60% | 1,52% | 1,51% | **1,95%** | 1,71% | 1,78% |

Rango ×3,5, movimiento suave, y el máximo cae en **2024**, el año del DNU 70/2023
y la Ley Bases. Como es un cociente, el año en curso sigue siendo comparable: el
numerador y el denominador se recortan juntos.

### Pero el numerador específico contra el Estado es demasiado fino

Sumarios que además mencionan «estado nacional»: entre **3 y 25 por año**
(3 en 2018, 25 en 2024). Sobre una base curada, un solo documento mueve la serie
varios puntos. No alcanza para un indicador, y sin faceta de descriptor no hay
forma de identificar al Estado como demandado con precisión.

### Las alternativas no dan un censo

- **`sjconsulta.csjn.gov.ar`** (sumarios de la CSJN): el buscador devuelve HTTP 500.
- **`scw.pjn.gov.ar`** (consulta de causas del PJN): responde, pero exige número
  de causa o parte. No es enumerable: no hay universo del cual contar.
- **`cij.gov.ar`**: página de novedades con enlaces a fallos y apenas fechas. Es
  un servicio de prensa, no una base consultable.
- **`datos.jus.gob.ar`**: no hay dataset de cautelares. «Causas no penales» es de
  poderes judiciales **provinciales**.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

1. **Judicialización: viable.** La densidad cautelar normalizada en jurisdicción
   Federal + Nacional es una serie que **nace discriminando** (ADR-0042): rango
   ×3,5, historia desde 2016 para calibrar bandas con datos reales, y no depende
   del volumen editorial de SAIJ. Queda como candidata construible.
2. **Bloqueo Cautelar: no es viable desde estas fuentes.** No es que no haya
   fuente: es que la única fuente consultable es un muestreo curado y el
   numerador específico da 3-25 documentos anuales. Construirlo igual sería
   publicar ruido con cara de indicador.
3. **No se incorpora nada al ITCP todavía.** Igual que en ADR-0134, falta la
   decisión editorial de orientación: más judicialización no es evidentemente
   mejor ni peor para la capacidad política del Gobierno, y el ITCP quedó cerrado
   con auditoría 7/7 el 20-jul-2026 — sumar un indicador obliga a reponderar y a
   rehacer la validación contra el EPU.

### Consecuencias

- Se cae el supuesto del aporte externo de que ambos indicadores **comparten
  infraestructura**: comparten fuente, pero uno es construible y el otro no. No
  hay un scraper único que los resuelva a los dos.
- **Limitación declarada y no resuelta**: la normalización divide el *volumen*
  editorial de SAIJ, pero no un eventual cambio en su *mezcla*. Si SAIJ empezara
  a sumariar proporcionalmente más fallos procesales, la densidad subiría sin que
  cambiara el fenómeno. No se puede descartar con datos del propio SAIJ; haría
  falta un contraste externo, y eso es condición para publicarlo, no un detalle.
- Relevamiento versionado en `data/politica/cautelares_saij_relevamiento.json`,
  con la consulta exacta, las facetas que existen y las que no, las series y las
  cuatro fuentes alternativas probadas con su resultado — para que el negativo
  sea auditable y nadie repita el camino.

## Más información

### Corrección al anexo de ADR-0131

El anexo dice que el conteo total sale de la faceta `Total` → `facetHits`. **Es
el hijo `total` en minúscula el que trae el número; el padre siempre devuelve 0.**
Y `totalSearchResults` **no** es el total: viene topeado por el `pageSize`, así
que una consulta con `p=5` informa 5 aunque haya miles. Quien lea el anexo tal
como estaba obtiene ceros en todo y concluye que la fuente no sirve. Corregido
acá y en `data/politica/cautelares_saij_relevamiento.json`.
