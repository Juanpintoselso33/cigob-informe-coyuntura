---
madr: 4
id: '0180'
estado: 'aceptado'
fecha: 2026-08-06
cinturon: 'transversal'
indice: 'todos'
archivos: ['web/src/lib/analytics.ts', 'web/src/layouts/Layout.astro', 'web/src/components/IndicadorModal.astro', 'web/public/robots.txt', 'web/astro.config.mjs', 'scripts/ga4_dimensiones.py', 'scripts/bigquery_export.py']
ambito: 'Plataforma Google · medición de uso, indexación y warehouse histórico'
origen: 'El informe se publica hace meses y no había ninguna medición: no se sabía si alguien lo leía, qué indicadores miraba, ni si Google lo estaba indexando'
---

# ADR-0180 — Integración con la plataforma Google: medición, indexación y warehouse

## Contexto y planteo del problema

El informe se publica en `informe.cigob.org` desde julio de 2026 y **no tenía
ninguna instrumentación**. No se sabía si alguien lo leía, qué indicadores
miraba, por qué búsquedas llegaba, ni si Google lo indexaba. Search Console
además reportaba que el sitio no tenía `robots.txt` ni sitemap.

En paralelo, todo el análisis que produce el pipeline —pesos, puntajes, bandas,
composición de cada dimensión, correlaciones, sensibilidad— existe sólo como
"la versión de hoy" en `web/src/data/informe.json` y `output/*.json`, más el
historial de git. Preguntar *cómo cambió la composición del ITCM en seis meses*
requiere leer diffs, no consultar.

Son dos problemas distintos y se resolvieron juntos porque comparten
infraestructura de credenciales.

## Factores de decisión

- **El ADC de gcloud es un único archivo global** y no se aísla por
  `gcloud config configurations`. Cualquier `application-default login` para
  CIGOB pisaría las credenciales que usa el proyecto Lufindo en la misma
  máquina.
- Los outputs versionados son un audit trail deliberado y los gates G1-G7 más
  la suite de tests protegen los números publicados. Nada nuevo puede abrir un
  camino que los esquive.
- Medir no puede romper la página: un error en la instrumentación no debe
  interrumpir una interacción del usuario.
- En GA4, **un parámetro que no está dado de alta como dimensión personalizada
  se guarda pero no se puede usar en ningún informe**. Es una falla silenciosa:
  los datos parecen estar y son inservibles.

## Opciones consideradas

- **Sólo Vercel Web Analytics.** Cero fricción, sin cookies ni banner. Pero no
  permite eventos propios ni desgloses por indicador.
- **Sólo GA4.** Cubre todo lo anterior, pero deja fuera métricas de entrega del
  sitio y obliga a mirar dos tableros igual.
- **Ambos** (elegida). Vercel para tráfico y entrega, GA4 para comportamiento.
- Para credenciales: **ADC compartido** (descartado, pisa Lufindo) contra
  **service account dedicado** (elegido).
- Para el warehouse: **subir todo a BigQuery** contra **dejarlo en los CSV**. Se
  planteó que 6.227 filas no justifican un warehouse; se eligió subirlo igual
  por decisión explícita del equipo, para poder explorar con SQL.

## Decisión

**Medición.** Vercel Web Analytics y GA4 (`G-WCRYLCT7R0`) en el `Layout.astro`
compartido, que cubre las 81 páginas. GA4 se inyecta **sólo si `PUBLIC_GA_ID`
está definida**, y se valida que tenga forma `G-XXXXXXXXXX` antes de
interpolarla en el `<script>`: sin la variable el sitio no pide `gtag.js` ni
escribe cookies, y una variable mal cargada no puede inyectar código.

**Eventos.** Seis, vía `web/src/lib/analytics.ts`, que no hace nada si `gtag`
no existe: `ver_indicador`, `ver_dimension`, `descargar_csv`, `fijar_dimension`,
`ver_cinturon`, `ver_ficha`. Se descartó un séptimo (`ver_formula`) al ver que
`mostrarFormula()` se llama al abrir el modal: habría sido un duplicado exacto
de `ver_indicador`.

**Dimensiones personalizadas.** `indicador`, `cinturon`, `dimension`, `estado`.
Se declaran en `scripts/ga4_dimensiones.py` y se sincronizan por Admin API. **No
se tocan por la UI**: se crearon a mano primero y corregir una sola descripción
implicó tantear coordenadas y escribir en el campo equivocado.

**Indexación.** `robots.txt` con referencia a `/sitemap-index.xml`, y
`@astrojs/sitemap` generando las 81 URLs. Se excluye
`/metodologia/dolarizacion_depositos/`: es un redirect, y un sitemap no debe
listar URLs que redirigen porque Search Console las reporta como error.

**Warehouse.** `scripts/bigquery_export.py` espeja 20 tablas en
`cigob-analytics.informe_coyuntura` (región `southamerica-east1`). Las de
snapshot llevan `generated_at` como clave de corrida y **se acumulan**: eso
convierte la historia del modelo —no sólo de los valores— en algo consultable.

**BigQuery es aguas abajo y de una sola dirección.** Lee los artefactos ya
publicados, después de los gates. El pipeline nunca lee de BigQuery. Es lo que
impide que se vuelva un camino paralelo capaz de esquivar los controles.

**Credenciales.** Un service account dedicado,
`ga4-informe@cigob-analytics.iam.gserviceaccount.com`, con la clave fuera del
repo. El ADC no se toca nunca.

**Un solo proyecto GCP: `cigob-analytics`.** Configuración de analytics y
warehouse conviven ahí. Llegar a eso costó un rodeo que conviene dejar anotado
porque se puede repetir: la cuenta de facturación `019461-23424F-0DF322` estaba
en su **cuota de proyectos vinculables**, así que `cigob-analytics` no podía
salir del sandbox de BigQuery —donde las tablas expiran a 60 días y no se
permite DML— y el warehouse se armó primero en `mcp-cigob`, que sí tenía
facturación. Se liberó un cupo desvinculando `sound-works-463815-m2` (el "My
First Project" que crea Google: verificado sin buckets, compute, Cloud Run,
functions, SQL, repos, service accounts ni datasets) y se movió todo.

`mcp-cigob` quedó exactamente como estaba: sin el dataset y sin los roles de
BigQuery que se le habían dado al service account.

Al habilitar facturación, **BigQuery tarda unos minutos en verla**: `gcloud`
reporta `billingEnabled: true` mientras la API sigue devolviendo 403. Además el
`default_table_expiration` de 60 días queda pegado al **dataset**, así que hay
que limpiarlo ahí y no sólo por tabla — si no, cada tabla nueva lo hereda.

### Consecuencias

- Se puede responder qué indicadores mira la gente, y cruzarlo con cuáles están
  desactualizados: eso da un criterio para priorizar qué colector arreglar.
- Los pesos y la composición de cada corrida quedan consultables con SQL.
- **La verificación de Search Console tiene dos métodos, a propósito.** Se
  verificó primero por "Google Analytics", lo que la dejaba colgando del
  `gtag.js`: sacar la etiqueta no costaba sólo la medición, costaba la
  titularidad de la propiedad —y con ella los datos de búsqueda y el export a
  BigQuery—. Se sumó `web/public/google9458216d8c787831.html`, un archivo
  estático independiente de cualquier lógica de plantilla, que sobrevive a que
  se toque `Layout.astro` (que es justo donde vive el gtag). **Ninguno de los
  dos archivos se borra.**
- Un parámetro nuevo en `analytics.ts` exige agregarlo también en
  `ga4_dimensiones.py`, o los datos se guardan y no se pueden usar.

### Confirmación

- Build: sin `PUBLIC_GA_ID`, 0 de 81 páginas con `gtag`; con un ID válido, las
  81; con un ID malformado (`'); alert(1); //`), 0.
- Producción: `gtag/js?id=G-WCRYLCT7R0` y `<vercel-analytics>` presentes en la
  home y en `/macro/`; `/_vercel/insights/script.js` responde 200.
- Eventos leídos del `dataLayer` en producción:
  `ver_cinturon {cinturon: "macro"}` y
  `ver_indicador {indicador: "ipc_total", cinturon: "macro", estado: "Automático"}`.
- Sitemap enviado a Search Console: status **Valid**, 0 errores, 81 URLs.
- `ga4_dimensiones.py --dry-run` detecta sólo la deriva real; tras aplicar, la
  re-corrida da 4 sin cambios.
- BigQuery: 20 tablas, 8.454 filas, 669 KB, **0 tablas con expiración**, sin
  duplicados.

## Más información

### Dos trampas que costaron tiempo

**`estado` no es lo que parece.** El parámetro sale de `badgeEstado()` y vale
`Automático` / `Carga manual` / `Estimación` — el modo de obtención del dato. Se
documentó primero como "fresco vs carry-forward" por confusión con el campo
homónimo del cinturón (`estable`/`en_tension`/`tensionado`), que es el semáforo
y no se envía a GA4. El error se detectó leyendo el `dataLayer` en producción,
no revisando el código.

**El free tier de BigQuery no permite DML.** La primera versión del export hacía
`except Exception: pass` alrededor del `DELETE` que limpia la corrida. Sin
facturación, ese `DELETE` devuelve `403 billingNotEnabled` y el script imprimía
"listo" mientras **duplicaba cada fila**. Ahora el error se propaga y aborta.
Mismo antipatrón que ADR-0173 documentó para los fetchers.

### Limitaciones

- **Las dimensiones personalizadas no son retroactivas.** Aplican desde su
  creación; los desgloses tardan 24-48 h en poblarse.
- El navegador del equipo tiene uBlock Origin sirviendo un stub falso de Google
  Analytics: `gtag/js` responde 200 pero no sale ningún hit. La navegación
  propia no se mide.
- Los dos exports nativos son **forward-only y sin backfill**: lo anterior a su
  activación no existe y no se puede recuperar.
- **La verificación por DNS quedó pendiente y no depende del equipo.** Es el
  método más robusto porque sobrevive incluso a que el sitio se caiga o se mude,
  pero el DNS de `cigob.org` está en Wix (`ns14`/`ns15.wixdns.net`) y la cuenta
  disponible es **colaboradora** del sitio, no propietaria: Wix responde
  "Necesitas permiso para administrar los dominios de este sitio". Hay que
  pedirle al propietario que agregue este TXT en `informe.cigob.org`:
  `google-site-verification=hOZhj7-L7Vg7REYSyUIEnkqXqg7YEqVRHors3uGrXaw`
- El export de datos de usuario de GA4 quedó **desactivado a propósito**: genera
  una tabla con atributos por usuario, que es más dato personal del necesario
  para un sitio público. Los eventos ya traen el id pseudónimo para los cruces.

### Los tres flujos que llenan BigQuery

Todo aterriza en `cigob-analytics`, y los tres datasets están en
**`southamerica-east1`**. No es cosmético: **BigQuery no permite joins entre
regiones**, así que si alguno hubiera quedado en el default US, cruzar búsquedas
con indicadores sería imposible — y la ubicación no se puede cambiar sin
rehacer el export.

| origen | dataset | frecuencia |
| --- | --- | --- |
| pipeline propio (`bigquery_export.py`) | `informe_coyuntura` | nocturna, tras los gates |
| GA4 (export nativo) | `analytics_548827028` | diaria |
| Search Console (bulk export) | `searchconsole` | diaria |

Se eligió el batch diario de GA4 y **no** el streaming: el tiempo real tiene un
cargo aparte por GB y a este volumen no aporta nada.

Search Console exige, antes de configurar el export, darle a
`search-console-data-export@system.gserviceaccount.com` los roles
`bigquery.jobUser` y `bigquery.dataEditor` sobre el proyecto. Si ese permiso se
quita, el export deja de escribir.
