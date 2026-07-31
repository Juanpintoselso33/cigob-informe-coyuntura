---
madr: 4
id: '0101'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'gestion'
indicadores: [privatizaciones]
complementado_por: ['0129']
ambito: 'ITCG · `privatizaciones` · modal del indicador'
origen: 'Auditoría externa del cinturón de gestión (doc 2), punto 3.5'
---

# ADR-0101 — Privatizaciones publica la norma que respalda cada etapa

## Contexto y planteo del problema

> "Es el **único indicador del set sin fuente en vivo** — depende de juicio del
> analista de CIGOB sobre en qué etapa está cada empresa. Esto no lo invalida,
> pero sí lo hace **más vulnerable a cuestionamientos de sesgo** si no se publica
> el detalle empresa por empresa con su norma de respaldo (la ficha dice que ese
> detalle existe en el registro)."

La auditoría también dice, y conviene registrarlo, que el diseño por etapas
verificables "es apropiado porque evita que un anuncio cuente como avance — sólo
cuenta lo que tiene norma de respaldo en el Boletín Oficial. Es el criterio
correcto para «promesa cumplida» vs. «promesa anunciada»".

## Opciones consideradas

- **Publicar la norma que respalda la etapa vigente de cada empresa**, con su fecha — elegida: quien discrepe puede discutir el criterio concreto en vez de sospechar del número.
- **Publicar sólo la etapa** — descartada: deja la asignación más vulnerable a cuestionamientos de sesgo.

## Decisión

La card publica `empresas_detalle`: para cada empresa, su etapa, el mecanismo de
privatización y **la norma que respalda la etapa vigente**, con su fecha. El
modal lo muestra como tabla, encabezada por la advertencia de que la etapa la
asigna el equipo y de que la norma está ahí para que la asignación pueda
verificarse.

| empresa | etapa | norma que la respalda |
|---|---|---|
| Transener | 4/4 | Contrato de compraventa 04-jun-2026; ENReGE Res. 130/2026 (BO 22-jun-2026) |
| AySA | 3/4 | Resolución ME 704/2026 (BO 15-may-2026) |
| Corredores Viales | 3/4 | Resolución ST 80/2025 (BO 19-nov-2025) |
| Enarsa | 2,5/4 | Res. ME 2124/2025 (BO 29-dic-2025) |
| Intercargo | 2,5/4 | Resolución ME 282/2026 (BO 26-mar-2026) |
| Belgrano Cargas | 1,5/4 | Resolución ME 1049/2025 (BO 24-jul-2025) |
| Nucleoeléctrica | 1/4 | Decreto 695/2025 (BO 30-sep-2025) |
| YCRT | 0,5/4 | Ley Bases 27.742 (BO 08-jul-2024), art. 9 |
| SOFSE | 0,5/4 | Ley Bases 27.742 (BO 08-jul-2024), Anexo I |

La norma que se muestra es la de la **última transición registrada que no supera
la etapa vigente**: el acto que respalda dónde está hoy esa empresa.

### El criterio del analista queda a la vista

En Nucleoeléctrica el registro dice: *"La Res. ME 1751/2025 inició el proceso; el
analista la mantiene en etapa 1 hasta que haya llamado"*. Esa nota se publica tal
cual.

Es más transparencia de la que la auditoría pedía: no sólo se muestra la norma,
también se muestra **cuándo el analista decidió ser más conservador que la
norma**. Un lector que discrepe puede discutir el criterio concreto en vez de
sospechar del número.

### Confirmación

`test_privatizaciones_publica_la_norma_de_cada_etapa` exige que el detalle
llegue al snapshot, que cubra a todas las empresas, que **ninguna quede sin
norma publicada**, que las etapas estén en 0-4 y que el promedio publicado se
reproduzca desde el detalle. Si mañana se agrega una empresa sin respaldo
documental, el pipeline se detiene.

## Más información

### Limitaciones

- **Sigue sin haber fuente en vivo.** La etapa se asigna a mano y el registro se
  actualiza a mano. Lo que cambia es que ahora es auditable, no automático.
- **El promedio simple trata a todas las empresas como equivalentes**: Transener
  pesa igual que YCRT. Ponderar por facturación, empleo o activos sería más
  informativo y exigiría una fuente adicional; queda anotado.
- Las etapas intermedias (0,5 · 1,5 · 2,5) expresan situaciones a mitad de
  camino y **su asignación es de criterio**. Están respaldadas por norma, pero la
  decisión de llamar "2,5" a un proceso parcialmente adjudicado es del equipo.

### El detalle existía; lo que faltaba era publicarlo

`data/gestion/privatizaciones_fechas.json` registra **cada transición de etapa
con el acto del Boletín Oficial que la respalda**. La card publicaba la etapa de
cada empresa —un número— pero no el mecanismo, el hito ni la norma.

Es decir: el trabajo de fundamentación estaba hecho y quedaba puertas adentro,
exactamente el mismo patrón que ADR-0093 encontró en la dimensión federal y
ADR-0096 en la ficha de desregulación. **Tercera vez en dos días que la
información que blindaba un indicador existía y vivía donde nadie la lee.**
