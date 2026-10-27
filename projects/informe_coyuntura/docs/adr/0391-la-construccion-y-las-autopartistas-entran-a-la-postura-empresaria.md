---
madr: 4
id: '0391'
estado: 'aceptado'
nota_estado: 'Los 7 desacuerdos adjudicados (bancos 2, CAMARCO 2, AFAC 3) los resolvió Juan el 27-oct-2026. Los otros 42 (CAMARCO 40, bancos 2) no afectan el puntaje y siguen pendientes de una persona.'
fecha: 2026-10-27
cinturon: 'politica'
indice: 'ITCP'
indicadores: [apoyo_empresario, apoyo_construccion, apoyo_comercio, apoyo_campo]
archivos: ['scripts/politica.py', 'scripts/itcp.py', 'scripts/descargar_series.py', 'scripts/procedencia_anclas.py', 'scripts/publicar.py', 'data/politica/apoyo_construccion_codificacion.json', 'data/politica/apoyo_bancos_codificacion.json', 'data/politica/apoyo_industria_codificacion.json', 'data/politica/apoyo_afac_corpus.json', 'data/politica/apoyo_industria_novedades.json', 'data/politica/apoyo_construccion_novedades.json', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
relacionado: ['0380', '0384', '0359']
ambito: 'Cinturón político · ITCP · dimensión Sector privado'
origen: 'Decisiones de Juan, 27-oct-2026: CAMARCO entra como sector nuevo (construcción); AFAC entra dentro de la industria, promediada por cámara con la UIA; los informes estadísticos de AFAC se archivan por título; la crónica de un acto ya cubierto por su declaración no se cuenta de nuevo; sector privado en cuartos; los bancos (ADEBA, ABA, ABAPPRA) quedan clasificados fuera del cálculo; adjudicación de los desacuerdos que decidían el puntaje. Criterio de entrada de Luis Babino (reunión del 26-oct-2026): 4 comunicados con postura dirigidos al Ejecutivo nacional en 12 meses.'
---

# ADR-0391 — La construcción y las autopartistas entran a la postura empresaria

## Contexto y planteo del problema

[[0380-mas-camaras-en-la-postura-empresaria]] sumó el comercio y
[[0384-el-campo-entra-a-la-postura-empresaria]] el campo, con el mismo protocolo:
manual v2, dos lectores ciegos de modelos distintos, kappa mínimo 0,7, adjudicación
humana de los desacuerdos que deciden el puntaje y el criterio de entrada de Luis
(mínimo de 4 comunicados dirigidos al Ejecutivo nacional con postura en 12 meses
calendario). Esta tanda aplica lo mismo a tres grupos nuevos: los bancos (ADEBA, ABA
y ABAPPRA, como un solo sector), la Cámara Argentina de la Construcción (CAMARCO) y
la Asociación de Fábricas Argentinas de Componentes (AFAC, autopartistas). El corpus
de bancos y CAMARCO ya estaba bajado y deduplicado (`apoyo_bancos_camarco_corpus.json`);
el de AFAC se bajó de la API pública del sitio.

## Factores de decisión

- Sumar un sector no toca el registro de otro (0380): la UIA no se toca.
- El puntaje no puede depender de un caso sin resolver (0384).
- Un mismo hecho no puede contar dos veces: CAMARCO publica la declaración de cada
  Consejo Federal y, un día después, la crónica del encuentro, que la repite.
- La regla de títulos de informes periódicos de la CAC y CAME (0380) se aplica igual
  a cualquier cámara que publique un tablero propio.

## Opciones consideradas

- **AFAC dentro de la industria, promediada por cámara con la UIA; CAMARCO como cuarto
  sector; bancos clasificados fuera (elegida, decisión de Juan).**
- AFAC como sector propio: descartada, es industria.
- Bancos dentro del cálculo con 3 comunicados: descartada, no llega al mínimo de Luis.
- No cambiar nada.

## Decisión

**Corpus** (desde el 10-dic-2023):

| Entidad | Descargadas | Archivadas | Clasificadas | Fuente |
|---|---|---|---|---|
| Bancos (ADEBA + ABA + ABAPPRA) | 68 (57 tras deduplicar) | 1 | 56 | WordPress de ADEBA y ABA, página única de ABAPPRA; un comunicado conjunto es una sola entrada con todas sus firmantes |
| CAMARCO | 891 | 291 | 600 | WordPress del sitio; archiva series periódicas por título y formación/divulgación por categoría |
| AFAC | 41 (de 171 en el listado) | 20 | 21 | API `Noticias/GetByFilter` (sección 2) y `Noticias/GetById`, más el PDF adjunto |

**1. Informes estadísticos de AFAC.** «Informe de Actividad…», «Comercio Exterior
Autopartista…» (y su variante «Comercio Exterior de Autopartes…») e «Informe de
Comercio Exterior…» son los informes periódicos de la cámara y se archivan sin
clasificar por título, con la misma regla que la CAC y CAME (`APOYO_AFAC_ESTADISTICO`).
Son 20: 5486, 5543, 5558, 5566, 5574, 5587, 5610, 5623, 5695, 5740, 5818, 5994, 6070,
6087, 6106, 6107, 6139, 6203, 6208, 6244. Los tres desacuerdos entre lectores que caían
en esas notas (6244, 6087, 5695) no se adjudican: se archivan. Cada archivado guarda
las dos lecturas descartadas para auditarlo. «Flota vehicular circulante» (anual) no
está en la regla y se clasificó: los dos lectores la leyeron neutra.

**2. Regla nueva, general: la crónica de un acto ya cubierto por su declaración no se
cuenta de nuevo.** Se cuenta una vez, la declaración. Se aplica con un campo explícito
en el registro, `duplica_a`, que nombra la clave de la declaración («CAMARCO|45828»);
no se deduce por fecha ni por título. La crónica conserva sus dos lecturas y entra al
kappa, pero `_apoyo_computable` no la cuenta, en cualquier sector. Casos marcados: las
crónicas del 147° (45869 → 45828), 146° (42782 → 42755), 145° (39936 → 39902) y 144°
(37959 → 37948) Consejo Federal. Sólo la del 147° cambia algo: las dos lecturas la
leyeron como crítica al Ejecutivo, igual que la declaración del día anterior.

**Concordancia** (lector C Sonnet, lector D Opus):

| Entidad | n | kappa postura | kappa destinatario | Desacuerdos | Adjudicados por Juan | Pendientes |
|---|---|---|---|---|---|---|
| Bancos | 56 | 0,943 | 0,918 | 4 | 2 | 2 |
| CAMARCO | 600 | 0,900 | 0,853 | 42 | 2 | 40 |
| AFAC (sin los informes archivados) | 21 | 0,864 | 0,829 | 3 | 3 | 0 |

Sobre las 41 de AFAC con los informes el kappa era 0,805 y 0,773 (6 desacuerdos). Los
lectores usaron «mixta» para notas que apoyan una medida y critican otra; el manual v2
manda «dudoso» en ese caso. Las dos etiquetas tienen el mismo efecto (no cuentan) y se
conservan como las escribieron.

**Adjudicación de Juan** (27-oct-2026, motivo en cada caso del registro): bancos
`abappra-2024-07-08` neutro/ejecutivo (documento programático) y `adeba-44450` apoyo/
ejecutivo (valorar un acuerdo firmado por el Gobierno; caía en la ventana y decidía el
conteo); CAMARCO 38128 neutro/provincias (crónica de un acto) y 40769 neutro/ejecutivo
(reclamo programático); AFAC 5549 crítica/Congreso (las retenciones estaban en la Ley
Ómnibus ya ingresada), 5679 neutro/ejecutivo (el título no resuelve) y 5785 mixta/
externo (responde a un columnista). Los 42 desacuerdos restantes no afectan el puntaje y
quedan pendientes, con postura y destinatario en null y concordancia
«pendiente_adjudicacion», como en 0384.

**Criterio de entrada** (ventana nov-2025 a oct-2026, cada comunicado una vez):

| Entidad | Comunicados | Apoyos | Críticas | Entra |
|---|---|---|---|---|
| CAMARCO | 4 (5 sin la regla de la crónica) | 3 | 1 | sí, como `apoyo_construccion` |
| AFAC | 4 | 1 | 3 | sí, dentro de `apoyo_empresario` |
| Bancos | 3 | 3 | 0 | no |

**3. La industria promedia por cámara la UIA y AFAC.** `apoyo_empresario` sigue
siendo la card «Postura pública de la industria»; desde ahora su saldo es el promedio
simple de los saldos de 12 meses de cada cámara con al menos tres pronunciamientos
computables en la ventana (la regla de 0384). Si una no llega ese mes, cuenta la otra.
AFAC tiene su propio registro (`apoyo_industria_codificacion.json`) y su propio detector
(`detectar_novedades_industria`); los pendientes de los dos inventarios cortan la serie.

**4. La construcción entra como sector nuevo**: `apoyo_construccion`, card «Postura
pública de la construcción», mismo saldo, mismo mínimo, mismas bandas y mismo corpus
cerrado (`apoyo_construccion_codificacion.json`, `detectar_novedades_construccion`).

**5. Sector privado en cuartos**: industria, comercio, campo y construcción, 0,25 cada
uno. El peso de la dimensión no cambia (0,1398).

**6. Los bancos quedan clasificados fuera del cálculo**, como CAME y AEA:
`APOYO_BANCOS_CAMARAS = ()`. Nombrarlos ahí repone su saldo (`apoyo_bancos_serie`);
sumarlos a la dimensión es además una decisión de peso (quintos en `DIMENSIONES_ITCP`)
con sus textos de la web y un detector, y lleva su propio ADR.

### Consecuencias

- Con el snapshot del 27-oct-2026: industria −0,400 (UIA sola) → **−0,450** (UIA
  −0,400 con 3 apoyos y 7 críticas; AFAC −0,500 con 1 y 3), puntaje 40,0 → **32,5**;
  construcción **+0,500** (3 y 1), puntaje **92,5**; comercio 100 y campo 55,8 sin cambio.
  Sector privado 65,3 → **70,2**; ITCP 75,0 → **75,7**; tensión política 2,5 → 2,4.
- La serie de la construcción tiene 32 puntos (feb-2024 a oct-2026) y va de −0,43 a
  +1,0. La de la industria pasa de 20 a 23 puntos (desde ago-2024).
- El cinturón político pasa de 16 a 17 indicadores en el índice.
- Por ser método, llega a la edición mensual y al archivo ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_politica_apoyo_construccion_y_afac.py` (sin red): kappa recalculado de los
tres registros (y el de las 41 de AFAC), las siete adjudicaciones de Juan, los 42
pendientes que no deciden el puntaje, la regla de la crónica duplicada (en el registro y
con un caso sintético que no mira la fecha), el archivo de informes de AFAC y que sus
desacuerdos no se adjudiquen, el conteo de 12 meses (CAMARCO 4, AFAC 4, bancos 3), el
promedio UIA+AFAC, cuartos que suman 1, bancos fuera del cálculo y su reposición, card =
último punto de la serie, bandas, detectores con fixtures (`afac_getbyfilter_chico.json`,
`afac_getbyid_chico.json`, `camarco_posts_chico.json`), el `git add` del cron y los textos
de la web.

## Pros y contras de las opciones

- **Elegida**: cada sector es un voto y cada cámara pesa lo mismo dentro de su sector;
  AFAC, que critica más de lo que apoya, baja la industria. Pero las dos cámaras nuevas
  se pronuncian poco (4 en la ventana): un comunicado más mueve mucho su saldo.
- **AFAC como sector propio**: le daría a los autopartistas el mismo peso que a todo el
  comercio o todo el campo.
- **Bancos dentro**: con 3 comunicados, todos de apoyo, el sector estaría en +1,0 sobre
  una base que el criterio de Luis declara insuficiente.
- **No cambiar**: la dimensión seguiría sin la construcción teniendo una cámara que
  cumple el mínimo.

## Más información

- **Límites declarados.** (1) Los lectores son agentes de IA; los desacuerdos que
  importaban los adjudicó una persona. (2) La regla de informes de AFAC mira el título:
  cinco informes que los dos lectores leían como crítica al Ejecutivo quedan afuera (es la
  regla de 0380). (3) La regla de la crónica la aplica una persona al registrar el caso;
  el detector no la deduce. (4) Los comunicados del G6 se publican en los sitios de los
  bancos y de CAMARCO y cuentan en cada sector que los publica (`g6: true` en el corpus).
  (5) El detector de AFAC no lee el PDF adjunto: deja su URL para quien clasifique.
- Pendiente: adjudicar los 42 desacuerdos restantes (no cambian el puntaje de hoy, pero sí
  pueden cambiar meses anteriores de la serie de la construcción).
