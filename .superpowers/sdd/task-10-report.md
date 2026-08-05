# Task 10 — Fichas metodológicas en la web — Reporte

## Estado: DONE_WITH_CONCERNS

Entregado: `cohesion_bloque` actualizada + **2** fichas nuevas (`cohesion_bloque_senado`,
`adhesion_reformas_provincial`) + **1** ficha existente extendida (`protestas_caba`,
cinturón gestión, vía `dobleUso`) en vez de una tercera ficha nueva duplicada. Ver
"Desviación del brief" más abajo — es un hallazgo arquitectónico real, no un atajo.

**Nota:** este archivo (`task-10-report.md`) tenía contenido previo de un Task 10
DISTINTO ("Backfill histórico en descargar_series.py", timestamp 15:19), de una
iteración anterior del plan. Confirmé que `task-10-brief.md` vigente es el de fichas
metodológicas (el que ejecuté) y sobreescribí este archivo con mi reporte.

---

## 1. Estructura real de `fichas.ts` encontrada

`web/src/lib/fichas.ts` exporta `FICHAS: Record<string, Ficha>` donde `Ficha =
FichaIndicador | FichaIndice`. La interfaz `FichaIndicador` (la relevante acá):

```ts
export interface FichaIndicador {
  tipo: "indicador";
  id: string;                       // debe ser IGUAL a la clave del Record
  cinturon: "macro" | "politica" | "vida_cotidiana" | "gestion" | "espiritu_epoca";
  rezago: string;
  fuente: { organismo, operacion, serie?, url?, acceso };
  transformaciones: string[];
  anclas?: AnclasFicha;              // tabla de bandas + interpolación lineal (ITCM/ITCG/ITVC)
  incidenciaTexto?: string[];        // explicación directa cuando NO hay tabla de anclas (todo política)
  dobleUso?: string;                 // dónde MÁS participa el mismo dato en el sistema
  limitaciones: string[];
  faltantes: string;
  revisiones: string;
  cambios: CambioMetodologico[];
}
```

Convención confirmada leyendo `cohesion_bloque` (plantilla) y `gobernadores_alineamiento`
(estimación manual, tono de referencia): sin números de ADR, sin jerga interna, registro
institucional. Los 8 indicadores existentes del cinturón política usan `incidenciaTexto`
(nunca `anclas`) — seguí el mismo patrón para las 3 fichas que toqué.

La página `web/src/pages/metodologia/[id].astro` resuelve `FICHAS[id]` y luego
`cinturon.indicadores[f.id]` contra `informe.json` **en tiempo de build** — el campo
`ind.fecha_dato` se lee SIN guarda en la línea 169. Esto importa para el hallazgo #2.

## 2. Hallazgo — colisión de clave `protestas_caba` (afecta el alcance de "3 fichas nuevas")

`scripts/politica.py` reutiliza literalmente el mismo fetcher e indicador `protestas_caba`
(vía `itcp.py` → `DIMENSIONES_ITCP["conflicto_social"]`) que ya existe como indicador de
CONTEXTO del cinturón gestión. Como `FICHAS` es un `Record` plano indexado por `id`
(la ruta `/metodologia/protestas_caba` solo puede resolver UNA entrada), no se puede crear
una segunda ficha con la misma clave — sería un error de TypeScript (identificador
duplicado) o, si TS no lo bloqueara, la segunda entrada pisaría silenciosamente a la
primera en el objeto literal.

Consulté al asesor (segunda opinión) antes de proceder: renombrar la clave
(`protestas_caba_politica`) tampoco sirve, porque `informe.cinturones.politica.indicadores`
usa la clave literal `protestas_caba` (así está en `itcp.py`) — un id distinto en
`fichas.ts` haría que `ind` quede `undefined` en esa ruta y rompa el build igual.

**Resolución (precedente ya establecido en el archivo):** el mismo patrón que usan
`votometro_ventaja_lla` / `clima_electoral` e `ipc_total` con sus usos derivados —
cuando un mismo dato participa en más de un lugar del sistema, se documenta con el
campo `dobleUso` sobre la ficha CANÓNICA, no con una ficha duplicada. Actualicé
`protestas_caba` (cinturón `gestion`, sin tocar su `cinturon` ni su framing original)
agregando:
- `dobleUso`: explica que el mismo dato integra la dimensión "conflicto social" del
  índice del cinturón política (15% del total, 40% interno junto a `movilizacion_cepa`),
  leído ahí como condición de gobernabilidad — **no** juicio sobre legitimidad de
  protestar (mismo encuadre pedido en el brief).
- Nueva entrada en `cambios` fechada 2026-07-07.

**Consecuencia:** el entregable real es 2 fichas nuevas + 2 fichas actualizadas
(no 3 nuevas). Está declarado explícitamente en el cuerpo del mensaje de commit.

## 3. Texto de las 4 fichas

### `cohesion_bloque` (actualizada)
- `fuente`: pasa de "Elaboración CIGOB (carga manual)" a "Cámara de Diputados de la
  Nación" / scraping automático de `votaciones.hcdn.gob.ar`.
- `transformaciones`/`incidenciaTexto`: reemplaza "% alineado con la posición oficial"
  por una explicación en lenguaje llano de la disparidad de la votación interna del
  bloque LLA (resta afirmativos menos negativos, valor absoluto sobre el total,
  excluye aliados de nombre ambiguo) — **sin nombrar "índice de Rice"**, porque
  verifiqué que ninguna ficha publicada nombra índices epónimos (Gini, Herfindahl,
  etc.); el estándar establecido es explicar el cálculo, no rotularlo.
- Agrega el peso real de la dimensión ("cohesión interna del oficialismo", 20% del
  índice del cinturón; 65% interno vs. 35% del Senado) — verificado línea por línea
  contra `DIMENSIONES_ITCP` en `scripts/itcp.py`.
- `limitaciones`/`faltantes`/`revisiones` reescritas para reflejar el mecanismo real
  (ventana de 90 días, umbral de 10 días sin corrida exitosa para marcar
  desactualizado — el receso legislativo NO cuenta como tal).
- `cambios`: conserva la entrada histórica de mayo (nace como estimación manual) y
  agrega una nueva fechada 2026-07-07 describiendo la redefinición.

### `cohesion_bloque_senado` (nueva)
Mismo criterio de cálculo aplicado al Senado, explícitamente presentado como lectura
COMPLEMENTARIA (no reemplaza a Diputados). Peso real: 35% interno de la misma dimensión
(vs. 65% de Diputados) — porque el bloque propio en el Senado tiene muchas menos bancas.

### `adhesion_reformas_provincial` (nueva)
% de provincias adheridas al RIGI (fuente: tabla del MAGyP). Declara explícitamente que
mide adhesión FISCAL a un régimen puntual, no alineamiento político general — remite al
indicador de gobernadores para esa otra dimensión, tal como pide el brief. Peso real:
30% interno de "alianzas territoriales" (25% del índice), junto a 40%
transferencias federales y 30% alineamiento de gobernadores.

Todos los umbrales de banda (90/75/60/40 para cohesión; 80/60/40/20 para adhesión RIGI)
están tomados literalmente de `BANDAS_ITCP` en `scripts/itcp.py` — no inventados.

## 4. Verificación de build

1. Build baseline (antes de tocar `fichas.ts`): verde, 62 páginas.
2. **Regeneré localmente** (sin scraping en vivo) `output/informe.json` y
   `web/src/data/informe.json` corriendo `python scripts/generar_informe.py` +
   `python scripts/publicar.py` — ambos son agregadores puramente offline (leen
   `output/cache/*.json`, no hacen requests de red) y el caché de política
   (`output/cache/politica.json`) YA tenía `cohesion_bloque_senado` y
   `adhesion_reformas_provincial` con datos reales de una corrida anterior de otro
   agente. Esto era necesario: sin esto, las 2 fichas nuevas hubieran roto el build
   (`[id].astro:169` lee `ind.fecha_dato` sin guarda — si el indicador no existe
   todavía en `informe.json`, `ind` es `undefined` y tira). No commiteé estos JSON
   regenerados (ya estaban sucios de antes; los dejé sin agregar al stage).
3. `npm run build` con mis 4 fichas: **verde, 64 páginas** (+2 rutas nuevas:
   `/metodologia/cohesion_bloque_senado/`, `/metodologia/adhesion_reformas_provincial/`).
4. `tsc --noEmit --strict` standalone sobre `fichas.ts` (usando el `typescript`
   transitivo ya instalado, sin agregar `@astrojs/check`): **sin errores** —
   confirma que no hay duplicado de clave `protestas_caba` ni desajuste de tipos.

## 5. Self-review / concerns

- **Alcance declarado vs. brief**: 2 fichas nuevas + 2 actualizadas, no "3 nuevas"
  literales — justificado en la sección 2, con el precedente ya existente en el
  archivo (`votometro_ventaja_lla`/`clima_electoral`, `ipc_total.dobleUso`).
- **Gap fuera de mi alcance declarado**: `web/src/lib/descripciones.ts` todavía tiene
  `cohesion_bloque.que = "Qué porcentaje de los diputados de LLA vota alineado con la
  posición oficial del bloque."` — la MISMA frase que el brief pide borrar, pero vive en
  otro archivo que el brief no incluyó en "Files: Modify". Tampoco tiene entradas para
  `cohesion_bloque_senado` ni `adhesion_reformas_provincial` (cae al fallback `{que:"",
  aporta:"", frecuencia:"—", tipo:"—"}`, no rompe el build pero deja esas secciones de
  la ficha vacías). `datos.ts` (labels/unidades) y `formulas.ts` (LaTeX + leyenda) tienen
  el mismo gap. Recomiendo una tarea de seguimiento explícita para sincronizar esos 3
  archivos con la redefinición — dejarlos así deja la sección "Qué mide y por qué
  importa" de la ficha de `cohesion_bloque` contradiciendo la sección "Cómo se calcula"
  que sí corregí.
- El repo está en la branch compartida `feature/itcp-cohesion-bloque-politica` (no
  `main`) — ya tenía 2 commits de otro agente (ADR-0036 y el doc del cinturón) antes
  del mío. Mi commit quedó arriba de esos, sin rebasear ni tocar nada de scripts/docs.
- Solo se agregó `web/src/lib/fichas.ts` al commit (`git diff --cached --stat` verificado
  antes de commitear: 1 file changed, 84 insertions, 13 deletions).

## 6. Commit

`b8bfc09` — `feat(web): fichas metodológicas para ITCP — cohesion_bloque actualizada + 3 nuevas`
(el cuerpo del mensaje aclara la desviación de "3 nuevas" a "2 nuevas + dobleUso").
