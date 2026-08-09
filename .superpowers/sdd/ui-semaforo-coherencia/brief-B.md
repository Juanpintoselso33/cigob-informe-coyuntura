# Tanda B — El color se explica donde la gente pregunta

La tanda A ya está mergeada: la paleta significa una sola cosa, el punto es
accesible y hay leyenda. Esta tanda cierra el agujero de comprensión.

## B1 — El modal no menciona el color. En absoluto.

`grep semaforo web/src/components/IndicadorModal.astro` devuelve **cero**.
Verificado en producción: clic en "Consumo de carne" —punto naranja— y el modal
muestra último valor, unidad, dimensión, frecuencia, actualización, fuente, qué
aporta, cómo se construye y cómo entra al ITVC. Del color, nada.

El modal es el drill-down principal del tablero. La ficha de `/metodologia` es
otra página y mucho menos descubrible. Hoy el color aparece sin explicación en
la card, y al hacer clic **sigue sin explicación**.

**Qué hacer:** un bloque de semáforo en el modal, con el color **nombrado en
texto** —no sólo pintado— más el `por_que` que `publicar.py` ya genera, y la
tabla de umbrales en unidad propia cuando el indicador la tenga.

Todo el dato ya está publicado en `ind.semaforo` (`{color, tension, umbrales,
unidad, por_que}`); no hay que calcular nada. Ojo con la forma:

- `umbrales` y `unidad` son `null` en los indicadores sin escala puntuable
  (vida cotidiana, espíritu de época): esos reciben color pero no tabla.
- `umbrales` es una **lista de tramos, no un mapa**: un color puede aparecer
  más de una vez. `costo_financiamiento_tesoro` es no monótono y tiene dos
  tramos de amarillo y dos de naranja, con el verde como intervalo cerrado.
  Renderizá la lista tal cual; si tu código deduplica por color, está mal.
- Algunos indicadores **no tienen bloque `semaforo`** (`asistencia_directa`
  está fuera del índice a propósito). Chequeá antes de renderizar: la sección
  no debe aparecer vacía ni inventar un color.

Que nombrar el color en texto no es decorativo: es lo que hace que el color
deje de ser el único portador de la información para quien no lo distingue.

`web/src/pages/metodologia/[id].astro` ya resuelve este mismo problema y su
helper `rangoLegible` ya maneja extremos abiertos y el menos tipográfico.
Reusá lo que puedas en vez de escribir una segunda versión que se desincronice.

## B2 — La ficha muestra dos tablas de umbrales seguidas, con cortes distintos, y no dice por qué

En `/metodologia/costo_financiamiento_tesoro`, una debajo de la otra:

| Tabla | Cortes |
|---|---|
| "Cómo entra al ITCM" | −5 · 0 · 6 · 12 · 20 |
| "Semáforo" | −3,57 · −1,89 · 12,5 · 16,67 · 19,33 |

Mismo indicador, mismo eje, números que no coinciden y ninguna explicación. Un
lector cuidadoso concluye que algo está mal.

**Qué hacer:** una línea en la sección de semáforo que explique la relación —
la primera tabla son las **anclas** que convierten el valor en puntaje, y la
segunda son los valores donde ese puntaje cruza los cortes de color. No es una
escala nueva ni una segunda opinión: es la misma escala leída al revés. Decilo
en llano, sin jerga y sin números de ADR (las fichas públicas no los muestran;
hay un gate que lo verifica).

## B3 — El `idc` arrastra dos vocabularios de color en la misma línea

`scripts/publicar.py:454` arma el texto del modal de `idc` metiéndole
`ind.get('banda_idc', '')`, que hoy sale como un `(amarillo)` pelado. Es una
lectura de z-score, escala distinta de la del semáforo, y queda al lado de un
punto de color que sale del puntaje ITCM. Hoy coinciden por casualidad; con
z = −0,6 el texto diría rojo junto a un punto de otra escala.

**Qué hacer:** decidilo vos y justificá. Las opciones razonables son etiquetar
el paréntesis para que se lea como lo que es (una lectura del propio IDC, no el
semáforo), o sacarlo del texto ahora que el punto y el bloque nuevo del modal
cubren el estado. Lo que no puede quedar es un color suelto sin dueño.

Ojo: `output/cache/macro.json` puede tener todavía la clave vieja `semaforo` en
vez de `banda_idc` si el colector no corrió; degrada a paréntesis vacío.

## Restricciones

- Trabajar desde `F:\dev\trabajo\CIGOB\Analisis CIGOB\projects\informe_coyuntura`.
- Copy en **castellano**, para lector no técnico. Sin números de ADR en páginas
  públicas.
- Los cortes viven sólo en `parametrica.CORTES_SEMAFORO`. Ningún `.ts` ni
  `.astro` con 4/6/8, 60/40/20 ni 105/95/85 escritos.
- No tocar bandas, pesos, índices, `UMBRALES` ni `_estado()`.
- No tocar el chip de 3 colores del cinturón (`verdictDeCinturon` /
  `cg-verdict`): es otro concepto, deliberado y documentado.
- `web/public/` es fuente; `web/dist/` es build.
- **Nunca `git add -A` ni `git add .`** — OneDrive restaura snapshots viejos.
- **No commitear snapshot.** Si regenerás para ver, restaurá `output/*`,
  `web/src/data/*` y `data/historico/*` byte a byte y probalo con
  `git status --short`.

## Verificación

`npx tsc --noEmit`, `npm run build`, `python -m pytest tests -q`.

Fallo preexistente y ajeno:
`test_series_ventanas_calendario.py::test_el_valor_vigente_del_ipi_no_cambio`.
Cualquier otra cosa es nueva.

**Abrí el modal de verdad** en tres casos y reportá lo que viste:

- uno con tabla de umbrales (p. ej. un indicador de gestión o macro),
- `costo_financiamiento_tesoro`, el no monótono — amarillo y naranja tienen
  que aparecer **dos veces cada uno**,
- uno de vida cotidiana, sin tabla — con color pero sin sección vacía.
