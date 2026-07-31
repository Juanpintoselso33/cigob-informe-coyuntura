---
madr: 4
id: '0017'
estado: 'superado'
nota_estado: 'Superado por ADR-0051'
fecha: 2026-07-03
cinturon: 'gestion'
archivos: ['scripts/gestion.py', 'scripts/descargar_series.py', 'data/gestion/protestas_caba.json']
superado_por: ['0051']
ambito: '`scripts/gestion.py` · `scripts/descargar_series.py` · `data/gestion/protestas_caba.json` · web'
---

# ADR-0017 — Protestas en CABA vía ACLED (contexto): la protesta no bajó, los cortes sí

## Contexto y planteo del problema

`protocolo_antipiquetes` quedó como única carga manual del cinturón (ADR-0014:
el registro histórico de cortes del GCBA está muerto; la serie propia GTFS-RT
recién nace). Se buscó una "fuente posta" con historia y se encontró **ACLED**
(Armed Conflict Location & Event Data): eventos de protesta geolocalizados,
Argentina desde 2018, actualización semanal, uso permitido con atribución.

## Opciones consideradas

- **`protestas_caba` como indicador de contexto**, que no puntúa — elegida.
- **Que puntúe dentro del ITCG** — no: entra como contexto.
- **`protocolo_antipiquetes`** sigue manual hasta que su serie madure.

## Decisión

- Nuevo indicador de **CONTEXTO `protestas_caba`** (no puntúa): eventos de
  protesta en CABA acumulados 12 meses (excluyendo el mes parcial del
  archivo), con la variación vs 2023 en la ficha y **serie mensual completa
  2018→hoy**. El colector loguea la sesión, baja el agregado y persiste la
  serie en `data/gestion/protestas_caba.json` (descargar_series lee el store,
  no re-baja los 8 MB).
- **`protocolo_antipiquetes` sigue manual y sigue puntuando**: mide CORTES
  (la promesa del gobierno), que ACLED no aísla. Puntuarlo con ACLED sería
  medir otra cosa (la protesta total, constitucionalmente protegida, que
  además no bajó).
- Credenciales fuera del repo: secrets `ACLED_USERNAME`/`ACLED_PASSWORD` +
  `.env` local. Atribución a ACLED en ficha y fuente.

### Consecuencias

- El cinturón gana la lectura de orden público completa: cortes ↓ (protocolo)
  + protesta ≈/↑ (ACLED) + alertas GTFS-RT (cobertura propia hacia adelante).
- Si CIGOB obtiene tier Research (email institucional + pedido a
  access@acleddata.com), la API de eventos permitiría filtrar por notas
  (%corte%/%roadblock%) y ahí sí evaluar si reemplaza al manual — ADR nuevo.
- **Riesgos**: el flujo depende del login Drupal y del nombre rotativo del
  XLSX (regex sobre la página); ACLED puede cambiar tiers/paths. Fallback:
  store versionado (serie no se pierde) + capa nacional HDX.

## Más información

### Verificación de acceso (2026-07-02/03)

- La API vieja key+email **murió** (sep-2025; api.acleddata.com sin DNS). La
  nueva usa **OAuth** (`POST acleddata.com/oauth/token`, token 24 h).
- Cuenta del analista (juan@ott.law): el token se emite OK pero la **API de
  eventos devuelve 403** — el tier de la cuenta (Open) no la incluye.
- **Lo que SÍ incluye el tier Open** (verificado end-to-end): el **agregado
  semanal × provincia × tipo de evento** por región, vía sesión web (login
  Drupal `user/login` con form_build_id → página
  `/aggregated/aggregated-data-latin-america-caribbean` → XLSX de ~8 MB,
  nombre de archivo rotativo por semana). Gotcha: el XLSX declara dimensiones
  1×1 → `reset_dimensions()` de openpyxl.
- Capa sin cuenta (fallback documentado): CSV de HDX con manifestaciones
  mensuales de Argentina (solo nivel nacional).

### El hallazgo que define el diseño

Serie CABA (Protests+Riots, ACLED): **2023: 240 · 2024: 226 · 2025: 260 ·
2026 ene-jun: 148 (~296 anualizado)** — los eventos de protesta en CABA **no
cayeron** respecto de 2023. Diagnóstico Político (la fuente del 55% de
reducción) cuenta **cortes de calle**; ACLED cuenta **eventos de protesta**
(marchas, concentraciones — no hay sub-tipo "corte", verificado en el
agregado). Leídos juntos: la protesta se **reconvirtió** de piquete a marcha
sin corte — que es exactamente lo que el protocolo pretendía inducir.
