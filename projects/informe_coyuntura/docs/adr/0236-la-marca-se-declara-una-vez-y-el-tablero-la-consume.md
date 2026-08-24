---
madr: 4
id: '0236'
estado: 'aceptado'
fecha: 2026-08-24
cinturon: 'transversal'
archivos: ['web/public/marca.css', 'web/public/dashboard.css', 'web/public/overrides.css', 'web/src/layouts/Layout.astro', 'web/src/lib/charts.ts', 'web/src/components/Footer.astro', 'web/src/pages/frontada.astro', 'web/src/pages/[slug].astro', 'web/tools/emitir-artifact.mjs']
ambito: 'Identidad visual del informe · paleta y sistema tipográfico del Manual de Marca de CiGob (21-ago-2026) · qué queda deliberadamente fuera de la marca'
origen: 'La fundación publicó su manual de marca y el informe seguía con una paleta aproximada a ojo desde cigob.org en junio de 2026'
---

# ADR-0236 — La marca se declara una vez y el tablero la consume

## Contexto y planteo del problema

Hasta hoy la identidad visual del informe era una **aproximación**: en junio de
2026 se tomaron a ojo un celeste y un verde de `cigob.org` y se escribieron
directo en `dashboard.css` (`--teal: #4998DB`, `--cta: #3E9486`), con la
tipografía Montserrat para todo el texto y JetBrains Mono para los números.
Funcionaba, pero no había ninguna fuente contra la cual verificarlo.

El 21 de agosto de 2026 la fundación publicó el **Manual de Marca para la Web
de CiGob**, que fija nueve colores en tres gamas y cinco familias tipográficas
con funciones **exclusivas** —el manual es explícito en que no se intercambian—.
La landing institucional ya lo aplicó. El informe no.

El problema de fondo no era el valor de cada color sino que **no existía un
lugar donde la marca estuviera declarada**. Los valores vivían mezclados con
2.500 líneas de reglas de presentación, así que cualquier cambio futuro del
manual obligaba a buscar y reemplazar hex a mano, sin garantía de completitud.

## Factores de decisión

- **La marca tiene que ser auditable.** Debe poder leerse en un archivo y
  compararse con el `.docx` sin abrir el resto del CSS.
- **No es un rediseño.** El informe ya estaba a ~80% de la identidad de CiGob
  (celeste + verde sobre fondo claro). Lo que corresponde es armonizar, no
  reconstruir: ninguna regla de layout, grilla o jerarquía cambia.
- **El manual no cubre todo lo que el tablero pinta.** Un informe tiene
  elementos cuyo color es *información*, no identidad, y el manual no los
  contempla porque una landing no los tiene.
- **La accesibilidad no puede empeorar.** El repo arrastra correcciones de
  contraste documentadas (ADR de la pista de referencia, la rampa de grises de
  impresión); aplicar la marca no puede pisarlas.

## Opciones consideradas

1. **Reemplazar los hex uno por uno en `dashboard.css`.** Es lo más rápido y no
   agrega archivos. Deja la marca disuelta entre las reglas: el problema de
   fondo queda igual y el próximo manual vuelve a costar lo mismo.
2. **Un archivo de tokens que el CSS histórico consume** (elegida).
3. **Tokens + sellado con huella sha256**, como en la landing. Aporta una
   guarda real contra ediciones accidentales, pero suma un paso a la CI del
   informe y una fricción que hoy nadie pidió.

## Decisión

Se agrega **`web/public/marca.css`**: los nueve colores y las cinco familias
del manual, más un puñado de derivados marcados como tales. `dashboard.css`
conserva sus nombres históricos (`--teal`, `--cta`, `--dark`…) pero ya **no
guarda valores**: cada uno apunta a su token de marca. Las ~2.500 reglas siguen
escritas igual y el color se mueve desde un solo lugar.

Los nombres viejos se conservan a propósito. `--teal` es un nombre equivocado
—la gama principal del manual es azul— pero renombrarlo tocaría cientos de
reglas sin cambiar un pixel, y ese diff escondería los cambios que sí importan.

### Reparto tipográfico

Cada familia recibe la función que el manual le asigna y ninguna otra:

| Familia | Función en el informe |
|---|---|
| Garet Bold | wordmark «CiGob» del nav y firma del pie |
| Lora | H1/H2 y encabezados de sección |
| Lato | cuerpos y párrafos |
| Inter | menú, botones, píldoras, etiquetas |
| Work Sans | valores de los índices, números de card, celdas numéricas |

**Garet no está en Google Fonts** —es comercial— así que se declara con
`@font-face` apuntando a `public/fuentes/` y un stack de reserva geométrico.
Mientras el archivo con licencia web no exista, el wordmark cae al reserva y no
se rompe nada. Está documentado en `web/public/fuentes/LEEME.md`.

### Qué queda fuera de la marca, a propósito

Dos familias de color **no** se armonizan, y no es una omisión:

- **El semáforo** (verde/amarillo/naranja/rojo). Codifica el nivel de tensión y
  se apoya en una convención universal. Teñirlo de azul y verde CiGob volvería
  el tablero ilegible.
- **Los identificadores de cinturón** (`--c-macro`, `--c-politica`…). Son
  categorías que tienen que distinguirse **entre sí** de un vistazo, y cinco
  tonos dentro de dos gamas no se distinguen.

La regla general: **el manual gobierna la identidad, no la codificación.** Un
color que porta un dato responde a la legibilidad de ese dato.

También queda intacta la **rampa de grises de `@media print`**: en papel el
color no se puede dar por hecho, y esa rampa tiene contraste propio calculado.

### Una corrección de contraste que el manual habilita

El azul base del manual (`#3D9AD1`) da **3,1:1 sobre blanco** — por debajo del
4,5:1 que WCAG pide para texto chico. El celeste anterior daba 3,17:1, así que
el déficit **venía de antes** y no lo introduce este cambio.

El manual trae tres azules justamente porque no todos sirven para lo mismo. Se
agrega el rol que faltaba, `--teal-ink` = azul oscuro (`#2878AB`, **4,81:1**),
y las 30 reglas donde el azul era **color de texto** pasan a usarlo. El azul
base queda para lo que es gráfico: fondos, trazos, bordes y barras.

Por la misma razón el énfasis (`<em>`) y un chip sobre verde claro pasan al
verde profundo del manual: 2,8:1 → 5,9:1.

### Consecuencias

- El manual se verifica leyendo un archivo de 100 líneas.
- Un cambio futuro del manual se aplica en `marca.css` y baja solo.
- Nada garantiza todavía que alguien no escriba un hex suelto en `overrides.css`.
  Esa guarda es la opción 3 y quedó afuera; si el problema aparece, se agrega.

### Confirmación

- `npx tsc --noEmit` y `npm run build` en verde; la suite completa (2.634 tests)
  pasa sin cambios.
- Revisión visual de portada, página de cinturón y ficha metodológica: ningún
  corrimiento de layout.
- Grep de la paleta anterior (`#4998DB`, `#3E9486`, Montserrat, JetBrains Mono):
  sin ocurrencias fuera de comentarios históricos.

## Pros y contras de las opciones

### Opción 1 — reemplazo directo de hex

- Bueno: cero archivos nuevos, diff mínimo.
- Malo: la marca sigue sin existir como objeto; el próximo manual cuesta igual.
- Malo: ninguna forma de auditar completitud.

### Opción 2 — tokens consumidos por el CSS histórico (elegida)

- Bueno: la marca queda declarada, aislada y legible.
- Bueno: el diff de las reglas es casi nulo — cambia el valor, no la estructura.
- Malo: un archivo CSS más que servir.
- Malo: el orden de carga importa, y romperlo no falla ruidosamente.

### Opción 3 — tokens sellados con sha256

- Bueno: guarda real contra ediciones accidentales de la marca.
- Malo: suma un paso a la CI y fricción para un problema que todavía no ocurrió.

## Más información

- Manual de Marca para la Web de CiGob, 21 de agosto de 2026.
- `web/public/marca.css` — los tokens y sus comentarios.
- `web/public/fuentes/LEEME.md` — qué falta para que Garet cargue de verdad.
- El emisor de HTML único (`web/tools/emitir-artifact.mjs`) lista las hojas por
  nombre: `marca.css` tuvo que agregarse ahí o el artifact salía con todos los
  `var()` sin definir.
