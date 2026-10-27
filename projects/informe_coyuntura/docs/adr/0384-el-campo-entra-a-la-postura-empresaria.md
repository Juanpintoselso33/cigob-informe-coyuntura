---
madr: 4
id: '0384'
estado: 'parcial'
nota_estado: 'El código, el registro y el rótulo están; el indicador apoyo_campo queda suspendido (INDICADORES_SUSPENDIDOS) hasta que una persona adjudique los 82 desacuerdos de data/politica/apoyo_campo_desacuerdos.json. Ningún agente adjudicó ninguno.'
fecha: 2026-10-27
cinturon: 'politica'
indice: 'ITCP'
indicadores: [apoyo_campo]
archivos: ['scripts/politica.py', 'scripts/itcp.py', 'scripts/descargar_series.py', 'scripts/procedencia_anclas.py', 'scripts/publicar.py', 'data/politica/apoyo_campo_codificacion.json', 'data/politica/apoyo_campo_desacuerdos.json', 'data/politica/apoyo_campo_novedades.json', 'data/politica/apoyo_camaras_relevamiento.json', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
relacionado: ['0131', '0150', '0245', '0310', '0380']
ambito: 'Cinturón político · ITCP · dimensión Sector privado'
origen: 'Reunión del 26-oct-2026: sumar otras cámaras además de la UIA; criterio de Luis Babino de 4 comunicados con postura en 12 meses. ADR-0380 dejó el campo como «próxima tanda».'
---

# ADR-0384 — El campo entra a la postura empresaria, pendiente de adjudicación

## Contexto y planteo del problema

[[0380-mas-camaras-en-la-postura-empresaria]] sumó el comercio y dejó al campo
(Coninagro, SRA, CRA) como candidato: la SRA no tenía archivo antes de 2025, el
listado de la CRA no pagina y Coninagro no estaba clasificado. Esta tanda baja
los tres corpus, los clasifica con el protocolo de 0380 y aplica el criterio de
entrada de Luis (mínimo de 4 comunicados dirigidos al Ejecutivo nacional con
postura en 12 meses calendario). La FAA no tiene sección de prensa.

## Factores de decisión

- Mismo protocolo que 0380: manual v2, dos lectores ciegos de modelos distintos,
  kappa mínimo 0,7, **adjudicación de los desacuerdos por una persona** (en 0380
  la hizo un agente y quedó marcada como pendiente de revisión; acá no se repite).
- El puntaje no puede depender de un caso sin resolver.
- Un indicador que no puntúa no es card ([[0245-suspender-libera-el-peso-y-el-indice-renormaliza-solo]] y el mecanismo de `INDICADORES_SUSPENDIDOS`).

## Opciones consideradas

- **Dejar `apoyo_campo` registrado y suspendido hasta la adjudicación (elegida).**
- Adjudicar los desacuerdos con otro agente (descartada: es lo que 0380 dejó pendiente de revisión humana).
- Entrar al índice con solo los casos en que los lectores coinciden (descartada: el puntaje cambia según cómo se resuelvan 13 casos).
- No cambiar nada.

## Decisión

**Corpus** (desde el 10-dic-2023, o desde donde llega cada sitio):

| Cámara | Descargadas | Archivadas (informes) | Clasificadas | Archivo desde |
|---|---|---|---|---|
| Coninagro | 264 | 92 | 172 | dic-2023 (API WordPress; no separa comunicados de notas) |
| SRA | 231 | 3 (páginas técnicas) | 228 | **21-ene-2025** (el sitio previo no responde) |
| CRA | 360 | 0 | 360 | dic-2023 (sección Prensa, ids enumerados; «Actualidad» no entra) |

La regla de informes estadísticos es por título y se escribió antes de clasificar
(`APOYO_CAMPO_ESTADISTICO`). Título y cuerpo salen del mismo registro (API de
Coninagro, JSON-LD de la CRA) o se verifican contra la tarjeta (SRA); no apareció
ningún «título no corresponde».

**Concordancia** (dos lectores ciegos, Sonnet y Opus, un agente por modelo y tramo
de cámara): kappa de postura 0,849 y de destinatario 0,903 sobre 760 notas
(Coninagro 0,851 y 0,929; SRA 0,965 y 0,966; CRA 0,796 y 0,858). Superan el piso de 0,7.

**Criterio de entrada** (ventana nov-2025 a oct-2026, solo notas donde los lectores
coinciden): Coninagro 5 (2 apoyos, 3 críticas), SRA 7 (6 y 1), CRA 34 (1 y 33). Las
tres lo cumplen.

**Desacuerdos: 82** (Coninagro 15, SRA 5, CRA 62), listados con texto, URL y las dos
lecturas en `data/politica/apoyo_campo_desacuerdos.json` para una persona. **13 caen
en la ventana en una nota que alguna de las dos lecturas clasifica como dirigida al
Ejecutivo con postura** (Coninagro 3, SRA 1, CRA 9): el puntaje depende de ellos. Por
lo tanto ninguna cámara entra al cálculo todavía: `apoyo_campo` está en
`INDICADORES_SUSPENDIDOS`, la dimensión de sector privado sigue entre industria y
comercio (50/50 efectivo) y reponerlo es sacar esa entrada. Los 82 casos están en el
registro con `postura` y `destinatario` en null y `concordancia: pendiente_adjudicacion`,
así que no cuentan para nada.

**Diseño listo para entrar**: `apoyo_campo` = mismo saldo, mismas bandas, mismo mínimo
de tres y mismo corpus cerrado que `apoyo_comercio` (una sola implementación,
`_apoyo_saldo_serie`), con las tres cámaras sumadas por nota; sector privado en tercios
(industria, comercio, campo). Como el sitio de la SRA empieza el 21-ene-2025, la serie
arranca en enero de 2026, el primer mes cuya ventana cae entera dentro de todos los
archivos (`APOYO_CAMPO_ARCHIVO_DESDE`). Detector propio para las tres cámaras
(`detectar_novedades_campo`).

### Consecuencias

- **Índice sin cambios con el snapshot actual**: sector privado 70,0 y ITCP 74,3.
- Efecto si entrara con solo los casos coincidentes (no es un dato publicado): saldo
  −0,609 sobre 46 pronunciamientos (9 apoyos, 37 críticas), puntaje 10; sector privado
  70,0 → 50,0 e ITCP 74,3 → 71,5. El resultado es el contrario del comercio.
- Las tres cámaras se suman por nota y no por cámara: la CRA aporta 34 de los 46 y
  domina el saldo. Un reparto por cámara es una decisión pendiente de Luis.
- Los 13 casos que importan son en su mayoría discursos de dirigentes en exposiciones
  rurales; sus lecturas oscilan entre neutro y crítica.

### Confirmación

`tests/test_politica_apoyo_campo.py` (sin red): kappa recalculado del registro,
casos pendientes sin postura, que el indicador siga suspendido mientras haya un
desacuerdo que afecte el puntaje, criterio de entrada, regla de informes, textos
no repetidos, card = último punto de la serie, cobertura de la SRA, bandas iguales,
tercios en la dimensión, detector y extractores.

## Más información

- **Límites declarados.** (1) Los lectores son agentes de IA. (2) Coninagro publica
  entrevistas y declaraciones junto con los comunicados y no hay forma de separarlas por
  título; se clasificaron todas. (3) Las notas de más de 4.000 caracteres se leyeron
  truncadas (el registro guarda el texto completo). (4) 161 ids de la CRA dan 404 y unos
  100 son redirecciones a PDF o enlaces; no son notas. (5) Falta dic-2023 a ene-2025 de la
  SRA. (6) El manual está escrito para la UIA y los lectores señalaron huecos que valen
  para el campo: reunión con un funcionario que incluye un reclamo, destinatario mixto
  nación-provincia, discursos largos sin una medida que dé título. No se tocó el manual.
- Pendiente: adjudicar; decidir si el saldo se reparte por cámara; la FAA no tiene prensa.
