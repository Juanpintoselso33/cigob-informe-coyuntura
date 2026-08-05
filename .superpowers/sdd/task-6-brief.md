### Task 6: Sync de la capa web (fichas, descripciones, etiquetas)

> **Agregada tras revisión de Task 4** (no en el diseño original): `grep -rn "gobernadores_alineamiento" web/src/` confirma que `web/src/lib/datos.ts` (LABELS, unidades cortas y largas, `BARRA_0_100`), `web/src/lib/descripciones.ts` y `web/src/lib/fichas.ts` referencian el indicador viejo por nombre. `datos.ts::label()` cae a `key.replace(/_/g, " ")` si falta una clave — sin este task, la card pública de `alineamiento_senadores_prov` mostraría el label crudo "alineamiento senadores prov" en vez de un nombre institucional, y su ficha en `/metodologia/alineamiento_senadores_prov` no existiría. Mismo patrón de bug ya encontrado y corregido en Plan2-Task10/11 de este proyecto.

**Files:**
- Modify: `web/src/lib/datos.ts`
- Modify: `web/src/lib/descripciones.ts`
- Modify: `web/src/lib/fichas.ts`

- [ ] **Step 1: Actualizar `datos.ts`**

En el bloque `LABELS` (política), reemplazar la línea de `gobernadores_alineamiento`:

```ts
  gobernadores_alineamiento: "Alineamiento de gobernadores (retirado)", veto_quorum: "Sesiones caídas por quórum",
  alineamiento_senadores_prov: "Alineamiento de senadores por provincia",
```

En el bloque de unidades cortas, reemplazar:

```ts
  gobernadores_alineamiento: "%", veto_quorum: "%", comisiones_caidas: "%",
  alineamiento_senadores_prov: "%",
```

En el bloque de unidades largas, reemplazar:

```ts
  gobernadores_alineamiento: "% de gobernadores (retirado)", veto_quorum: "% de sesiones",
  alineamiento_senadores_prov: "% de senadores no-LLA",
```

En `BARRA_0_100`, reemplazar `"gobernadores_alineamiento"` por `"alineamiento_senadores_prov"` (misma escala 0-100, misma barra de progreso):

```ts
export const BARRA_0_100 = new Set<string>([
  "eficacia_legislativa", "cohesion_bloque", "alineamiento_senadores_prov",
  "veto_quorum", "comisiones_caidas", "movilizacion_cepa",
  "informalidad", "pluriempleo", "sentimiento_digital", "icc_utdt",
]);
```

- [ ] **Step 2: Actualizar `descripciones.ts`**

Reemplazar la entrada `gobernadores_alineamiento` (agregar una nueva, dejar la vieja fuera del objeto — este archivo no tiene precedente de "entradas retiradas", a diferencia de `fichas.ts`, así que se retira limpiamente):

```ts
  alineamiento_senadores_prov: {
    que: "Qué porcentaje de los votos de senadores no alineados con el oficialismo (La Libertad Avanza) coincide con la posición que tomó el bloque oficialista en esa misma votación, promediado entre provincias.",
    aporta: "Mide comportamiento de voto legislativo por provincia, no la postura pública del gobernador (Poder Ejecutivo provincial) — un senador no depende del gobernador de turno. Es la señal automatizable más cercana al apoyo territorial disponible hoy.",
    frecuencia: "Continua (90d)", tipo: "Nivel (%)",
  },
```

También actualizar la referencia cruzada en la entrada `adhesion_reformas_provincial` (que menciona "el indicador de gobernadores" por nombre implícito):

```ts
  adhesion_reformas_provincial: {
    que: "Cuántas de las 24 provincias (incluida CABA) figuran adheridas al Régimen de Incentivo para Grandes Inversiones (RIGI), sobre el total.",
    aporta: "Mide adhesión fiscal a un régimen de promoción de inversiones puntual, no el alineamiento político general de una provincia con la Nación — eso lo mide, con otro método, el indicador de alineamiento de senadores por provincia.",
    frecuencia: "Continua", tipo: "Nivel (%)",
  },
```

- [ ] **Step 3: Actualizar `fichas.ts`**

Agregar una ficha nueva `alineamiento_senadores_prov` inmediatamente después del cierre de la ficha `cohesion_bloque_senado` (antes de `adhesion_reformas_provincial`), siguiendo el mismo molde estructural que esas dos fichas vecinas (mismo tipo de fuente automática por scraping, mismo estilo de `incidenciaTexto` con escalones, SIN mencionar números de ADR por la decisión editorial del 06-jul-2026 ya documentada al inicio del archivo):

```ts
  alineamiento_senadores_prov: {
    tipo: "indicador",
    id: "alineamiento_senadores_prov",
    cinturon: "politica",
    rezago: "El portal de votaciones nominales del Senado registra cada sesión a los pocos días de ocurrida; el informe recalcula el promedio de los últimos 90 días en cada corrida.",
    fuente: {
      organismo: "Senado de la Nación",
      operacion: "Votaciones nominales del Senado — coincidencia de senadores no alineados con la posición del bloque de La Libertad Avanza, por provincia, actas de los últimos 90 días",
      url: "https://www.senado.gob.ar/votaciones/actas",
      acceso: "Automático: scraping directo del portal público de votaciones nominales del Senado; sin carga manual.",
    },
    transformaciones: [
      "Para cada acta, determina la posición del bloque de La Libertad Avanza (el sentido en el que votó la mayoría de sus senadores). Si el bloque queda empatado, esa acta no aporta señal.",
      "Para cada provincia, mide qué proporción de los votos de sus senadores QUE NO son del bloque LLA coincidió con esa posición. Las provincias donde los 3 senadores son de LLA quedan fuera del cálculo: su coincidencia sería automática por definición, no aporta información.",
      "El indicador es el promedio simple de esa proporción entre todas las provincias con al menos un senador no-LLA, sobre las actas de los últimos 90 días.",
    ],
    incidenciaTexto: [
      "Reemplaza, desde julio de 2026, a un indicador de carga manual (\"alineamiento de gobernadores\") que quedó congelado por meses sin una fuente pública estructurada para actualizarlo — dos rondas de búsqueda de fuentes automatizables no encontraron ninguna que midiera directamente la postura del Poder Ejecutivo provincial.",
      "Caveat importante: este indicador mide comportamiento de voto de SENADORES, no la postura pública del gobernador de la provincia — un senador no depende del gobernador de turno, puede responder a la estrategia nacional de su propio partido. Es la mejor señal automatizable disponible hoy, no una medición directa del Poder Ejecutivo provincial.",
      "El puntaje sube en escalones con ese porcentaje: más de 65% de coincidencia → el más alto; entre 45% y 65% → alto; entre 25% y 45% → moderado; entre 10% y 25% → bajo; menos de 10% → el más bajo. Los umbrales son provisorios: se fijaron sin serie histórica propia del indicador y se van a recalibrar cuando la haya.",
      "Integra la dimensión de alianzas territoriales del índice del cinturón (25% del total), donde pesa 30% junto al 40% de las transferencias federales y el 30% de adhesión al RIGI.",
    ],
    limitaciones: [
      "Proxy de comportamiento legislativo, no medición directa de la postura del gobernador (Poder Ejecutivo provincial) — ver caveat arriba.",
      "Incluye votaciones consensuadas (donde todo el Senado vota en el mismo sentido), no solo las genuinamente disputadas — solo se excluyen las actas donde el propio bloque LLA queda internamente empatado.",
      "Bloque LLA chico en el Senado: pocos senadores propios hacen que su 'posición' en un acta dependa de muy pocos votos.",
      "Depende de que el portal público del Senado mantenga su estructura actual: un cambio de diseño del sitio puede interrumpir la lectura automática hasta que se ajuste.",
    ],
    faltantes: "Si el scraping no logra llegar al sitio, se conserva el último promedio calculado en caché; recién se marca desactualizado si pasan más de 10 días sin una corrida que haya llegado al portal — un receso legislativo sin actas nuevas no cuenta como desactualización.",
    revisiones: "El promedio de los últimos 90 días se recalcula completo desde la fuente en cada corrida; no se arrastran promedios previos.",
    cambios: [
      { fecha: "2026-07-08", cambio: "Alta como reemplazo de \"alineamiento de gobernadores\" (indicador de carga manual, sin fuente automatizable encontrada): mide coincidencia de voto de senadores no oficialistas con la posición del bloque de gobierno, por provincia." },
    ],
  },

```

En la ficha `gobernadores_alineamiento` ya existente (queda en el archivo como referencia histórica, mismo criterio que `cohesion_bloque`), agregar una entrada al final de su array `cambios` documentando el retiro:

```ts
    cambios: [
      { fecha: "2026-05", cambio: "Incorporado al cinturón como estimación manual: la relación con los gobernadores es una dimensión del capital político sin fuente estructurada." },
      { fecha: "2026-07-08", cambio: "Retirado del peso del índice: reemplazado por alineamiento_senadores_prov, un proxy automatizable de comportamiento de voto legislativo por provincia. Esta ficha queda como referencia histórica." },
    ],
```

También agregar la misma referencia cruzada actualizada en la ficha `adhesion_reformas_provincial` (su `incidenciaTexto`, primer ítem, menciona "el indicador de gobernadores" por nombre implícito):

```ts
    incidenciaTexto: [
      "Mide adhesión a un régimen fiscal y de promoción de inversiones puntual, no el alineamiento político general de una provincia con la Nación — eso lo mide, con otro método, el indicador de alineamiento de senadores por provincia. Una provincia puede adherir al RIGI por conveniencia fiscal aun con un gobernador crítico del gobierno nacional, y a la inversa.",
      "El puntaje sube en escalones con el porcentaje adherido: más de 80% de provincias adheridas → el más alto; entre 60% y 80% → alto; entre 40% y 60% → moderado; entre 20% y 40% → bajo; menos de 20% → el más bajo. Los umbrales son provisorios: se fijaron sin serie histórica propia del indicador y se van a recalibrar cuando la haya.",
      "Integra la dimensión de alianzas territoriales del índice del cinturón (25% del total), donde pesa 30% junto al 40% de las transferencias federales y el 30% del alineamiento de senadores por provincia.",
    ],
```

- [ ] **Step 4: Verificar el build**

```bash
cd web && npm run build
```
Expected: build limpio, sin errores. Confirmar que `/metodologia/alineamiento_senadores_prov` aparece entre las rutas generadas (buscar en el output de `npm run build` o revisar `dist/metodologia/alineamiento_senadores_prov/index.html` si existe tras el build).

- [ ] **Step 5: Verificar ausencia de referencias sueltas**

```bash
cd projects/informe_coyuntura && grep -rn "gobernadores_alineamiento" web/src/lib/
```
Expected: solo debe aparecer dentro de la ficha histórica en `fichas.ts` (la entrada `gobernadores_alineamiento:` en sí y su changelog) — ninguna referencia suelta en `datos.ts`/`descripciones.ts` fuera de ese archivo.

- [ ] **Step 6: Commit**

```bash
git add web/src/lib/datos.ts web/src/lib/descripciones.ts web/src/lib/fichas.ts
git commit -m "feat(web): sincroniza fichas/descripciones/etiquetas con alineamiento_senadores_prov"
```
