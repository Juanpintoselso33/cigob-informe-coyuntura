---
madr: 4
id: '0384'
estado: 'aceptado'
nota_estado: 'Los 13 desacuerdos que decidían el puntaje los adjudicó Juan el 27-oct-2026. Los otros 69 no afectan el puntaje y siguen pendientes de una persona.'
fecha: 2026-10-27
cinturon: 'politica'
indice: 'ITCP'
indicadores: [apoyo_campo]
archivos: ['scripts/politica.py', 'scripts/itcp.py', 'scripts/descargar_series.py', 'scripts/procedencia_anclas.py', 'scripts/publicar.py', 'data/politica/apoyo_campo_codificacion.json', 'data/politica/apoyo_campo_desacuerdos.json', 'data/politica/apoyo_campo_novedades.json', 'data/politica/apoyo_camaras_relevamiento.json', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
relacionado: ['0131', '0150', '0245', '0310', '0380']
ambito: 'Cinturón político · ITCP · dimensión Sector privado'
origen: 'Reunión del 26-oct-2026: sumar otras cámaras además de la UIA; criterio de Luis Babino de 4 comunicados con postura en 12 meses. ADR-0380 dejó el campo como «próxima tanda». Adjudicación de Juan y criterio de suma de Luis, 27-oct-2026.'
---

# ADR-0384 — El campo entra a la postura empresaria

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
- Con tres entidades de volumen muy distinto, sumar todas las notas juntas deja
  que la que más publica decida sola.

## Opciones consideradas

- **Saldo = promedio simple de los saldos de cada cámara con el mínimo de comunicados (elegida, propuesta de Luis: «promediando entidades»).**
- Saldo de todas las notas juntas (la cuenta de la industria y el comercio): descartada, la CRA aporta 39 de los 52 pronunciamientos de la ventana y decide sola.
- Dejar el indicador suspendido (ADR-0245) hasta adjudicar: fue el estado intermedio de esta tanda, hasta que Juan adjudicó.
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
coincidían): Coninagro 5, SRA 7, CRA 34. Las tres lo cumplen.

**Adjudicación humana.** Hubo 82 desacuerdos (Coninagro 15, SRA 5, CRA 62). 13 caían
en la ventana en una nota que alguna de las dos lecturas clasificaba como dirigida al
Ejecutivo con postura (Coninagro 3, SRA 1, CRA 9): decidían el puntaje. **Los adjudicó
Juan el 27-oct-2026**, todos con destinatario ejecutivo_nacional: Coninagro, tres
neutros; SRA, una crítica; CRA, cuatro apoyos, una crítica y cuatro neutros
(la lista caso por caso está en `apoyo_campo_desacuerdos.json`, campo `adjudicacion`, y
en el registro con motivo «adjudicación humana de Juan, 27-oct-2026»). Los 69
restantes no afectan el puntaje y quedan pendientes (postura nula, no cuentan).

**Cómo se suma** (propuesta de Luis, «promediando entidades»). Cada cámara tiene su
saldo de doce meses, (apoyos − críticas) / (apoyos + críticas). El indicador
`apoyo_campo` es el **promedio simple de los saldos de las cámaras que tienen al menos
tres pronunciamientos computables en la ventana** (el mismo mínimo de `apoyo_empresario`
y `apoyo_comercio`); no es el saldo de todas las notas juntas. Cada entidad vale lo
mismo, publique mucho o poco. Un mes en que ninguna llega al mínimo queda sin valor.

**Integración.** `apoyo_campo` sale de `INDICADORES_SUSPENDIDOS` y las tres cámaras
entran al cálculo. Mismas bandas, mismo corpus cerrado y mismo detector que el comercio
(`detectar_novedades_campo`). Sector privado en tercios: industria, comercio y campo.
Como el sitio de la SRA empieza el 21-ene-2025, la serie arranca en enero de 2026, el
primer mes cuya ventana cae entera dentro de todos los archivos
(`APOYO_CAMPO_ARCHIVO_DESDE`).

### Consecuencias

- Con el snapshot del 27-oct-2026: saldos por cámara Coninagro −0,200 (2 apoyos, 3
  críticas), CRA −0,744 (5 y 34), SRA +0,500 (6 y 2); compuesto **−0,148** sobre 52
  pronunciamientos; puntaje **55,8**. Sector privado 70,0 → 65,3 e ITCP 74,3 → 73,6.
- Con el saldo de todas las notas juntas habría sido −0,50 (13 apoyos y 39 críticas; puntaje 25,0). El promedio
  por cámara no es neutro: favorece a las cámaras que publican poco.
- La serie tiene 10 puntos (ene a oct de 2026) y va de −0,54 a −0,12.
- El indicador pasa de 15 a 16 en el cinturón político (suspendido, no contaba).
- Por ser método, llega a la edición mensual y al archivo ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_politica_apoyo_campo.py` (sin red): kappa recalculado del registro,
adjudicación de los 13 casos, pendientes sin postura, que ningún desacuerdo
pendiente afecte el puntaje, criterio de entrada, promedio por cámara (distinto del
saldo de todas las notas), cobertura de la SRA, card = último punto de la serie,
bandas iguales, tercios en la dimensión, detector y extractores.

## Más información

- **Límites declarados.** (1) Los lectores son agentes de IA; la adjudicación de los
  casos que importaban fue humana. (2) Coninagro publica entrevistas y declaraciones
  junto con los comunicados y no hay forma de separarlas por título; se clasificaron
  todas. (3) Las notas de más de 4.000 caracteres se leyeron truncadas (el registro
  guarda el texto completo). (4) 161 ids de la CRA dan 404 y unos 100 son
  redirecciones a PDF o enlaces; no son notas. (5) Falta dic-2023 a ene-2025 de la SRA.
  (6) El manual está escrito para la UIA y los lectores señalaron huecos que valen para
  el campo: reunión con un funcionario que incluye un reclamo, destinatario mixto
  nación-provincia, discursos largos sin una medida que dé título. No se tocó el manual.
- Pendiente: adjudicar los 69 restantes (no cambian el puntaje de hoy, pero sí podrían
  cambiar el de otros meses de la serie); la FAA no tiene prensa.
