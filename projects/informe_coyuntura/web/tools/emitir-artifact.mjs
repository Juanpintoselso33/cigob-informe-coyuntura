#!/usr/bin/env node
/**
 * emitir-artifact.mjs — colapsa el informe en un HTML único, interactivo y autocontenido.
 *
 * Toma lo que `astro build` dejó en `web/dist/` y arma un solo archivo con las secciones del
 * informe, los gráficos de ApexCharts y las fórmulas de KaTeX funcionando, sin un solo pedido
 * a la red. Se abre con doble clic y se puede pasar entero.
 *
 * ── Lo que hay que saber antes de tocar esto ──────────────────────────────────────────────
 *
 * **1. Acá no hay view transitions.** El sitio navega a la vieja usanza, así que cada script
 * de página fue escrito dando por sentado que es el único documento: busca `cg-det-modal`,
 * `cg-dim-groups` y compañía por id fijo. Apiladas cuatro secciones en un documento, esas ids
 * se repiten y `getElementById` devuelve siempre la primera.
 *
 * La salida no es renombrar ids —el JS los tiene literales— sino **envolver cada módulo en
 * una función que recibe un `document` acotado a su sección**. Como el parámetro se llama
 * `document`, tapa al global dentro de ese scope y el código sigue sin enterarse. Es la razón
 * de que este archivo no parchee ni una línea de la lógica del informe.
 *
 * **2. Vite carga ApexCharts y KaTeX con `import()` dinámico.** Un `import()` con ruta
 * relativa dentro de un `<script>` inline no resuelve contra nada. Los especificadores son
 * literales, así que se reescriben a una promesa ya resuelta contra el global correspondiente.
 *
 * **3. `hoisted.DJFWlTNo.js` es `@vercel/analytics`** y pide
 * `https://va.vercel-scripts.com/v1/script.debug.js`. No se empotra: se descarta. Es la única
 * llamada a un tercero del build, y un archivo que se reparte no puede fichar a quien lo abre.
 *
 * ── El límite que conviene saber de entrada ───────────────────────────────────────────────
 * El completo ronda el millón de tokens: sirve para abrir y navegar, **no** para pegarlo en
 * una conversación. El 83 % de cada página son las series en `<script>` inline, así que ni
 * sacando las bibliotecas entra. Para eso están `output/informe.md` y `output/fichas/*.md`.
 *
 * Uso:
 *   npm run build                                   # primero, para tener dist/
 *   node tools/emitir-artifact.mjs                  # completo  → dist-artifact/informe-artifact.html
 *   node tools/emitir-artifact.mjs --lite           # ApexCharts por CDN, sin fórmulas ni fuentes
 *   node tools/emitir-artifact.mjs --sin metodologia
 *   node tools/emitir-artifact.mjs --con-fichas     # suma las ~70 fichas de metodología
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const WEB = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DIST = path.join(WEB, 'dist');
const ASSETS = path.join(DIST, '_assets');
const SALIDA_DIR = path.join(WEB, 'dist-artifact');

const args = process.argv.slice(2);
const opcion = (nombre, pordefecto) => {
  const i = args.indexOf(`--${nombre}`);
  return i >= 0 && args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : pordefecto;
};

/**
 * `--lite`: ApexCharts desde cdnjs y sin KaTeX ni sus 19 fuentes.
 *
 * No alcanza para que entre en el contexto de un modelo —nada alcanza, ver arriba— pero baja
 * el archivo a la mitad y lo vuelve manejable para mandarlo por mail o abrirlo en un teléfono.
 * cdnjs es de los orígenes que el sandbox de artifacts de claude.ai admite.
 */
const LITE = args.includes('--lite');
const APEX_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/apexcharts/3.54.1/apexcharts.min.js';

/** Las ~70 fichas de metodología son 1,2 MB aparte: van sólo si se piden. */
const CON_FICHAS = args.includes('--con-fichas');
const EXCLUIDAS = new Set((opcion('sin', '') || '').split(',').map(s => s.trim()).filter(Boolean));

if (!fs.existsSync(DIST)) {
  console.error('✗ falta web/dist/. Corré primero:  npm run build');
  process.exit(1);
}

const leer = p => fs.readFileSync(p, 'utf8');
const existe = p => fs.existsSync(p);
/** Los bundles de Vite llevan hash en el nombre; se los busca por prefijo. */
const assetQueEmpieza = pre => {
  const f = fs.readdirSync(ASSETS).find(n => n.startsWith(pre) && n.endsWith('.js'));
  return f ? path.join(ASSETS, f) : null;
};

// ── Extractores ───────────────────────────────────────────────────────────────────────────
// Astro emite todo en una línea y sin anidar estos elementos: alcanza con cortar entre marcas.

const entre = (html, apertura, cierre) => {
  const i = html.indexOf(apertura);
  if (i < 0) return null;
  const j = html.indexOf(cierre, i);
  return j < 0 ? null : html.slice(i, j + cierre.length);
};

/**
 * El cuerpo de una página es todo lo que va entre el `</nav>` y el cierre del body. El
 * `<vercel-analytics>` que Astro deja antes de `</body>` se corta acá y no llega a la salida.
 */
const cuerpoDe = html => {
  const i = html.indexOf('</nav>');
  if (i < 0) return null;
  let resto = html.slice(i + '</nav>'.length);
  const corte = resto.indexOf('<vercel-analytics');
  if (corte >= 0) resto = resto.slice(0, corte);
  else resto = resto.slice(0, resto.indexOf('</body>'));
  return resto;
};

// ── Qué secciones entran, y en qué orden ──────────────────────────────────────────────────
// El orden sale del propio nav: si mañana se agrega una sección al sitio, aparece acá sola.
const paginaMuestra = leer(path.join(DIST, 'macro', 'index.html'));
const navCrudo = entre(paginaMuestra, '<nav class="cg-nav"', '</nav>');
if (!navCrudo) { console.error('✗ no encontré el <nav class="cg-nav"> en dist/macro/index.html'); process.exit(1); }

/** `/` → `inicio`; `/macro/` → `macro`. Sólo los enlaces internos del menú de secciones. */
const bloqueLinks = entre(navCrudo, '<div class="cg-nav-links"', '</div>') || navCrudo;
const rutas = [...bloqueLinks.matchAll(/href="(\/[^"]*)"/g)].map(m => m[1]);
const claveDe = ruta => ruta.replace(/^\/+|\/+$/g, '') || 'inicio';

const archivoDe = clave => clave === 'inicio'
  ? path.join(DIST, 'index.html')
  : path.join(DIST, clave, 'index.html');

const paginas = [];
for (const ruta of rutas) {
  const clave = claveDe(ruta);
  if (EXCLUIDAS.has(clave) || paginas.some(p => p.clave === clave)) continue;
  const archivo = archivoDe(clave);
  if (!existe(archivo)) { console.warn(`  ⚠ sin archivo: ${clave}`); continue; }
  const cuerpo = cuerpoDe(leer(archivo));
  if (cuerpo == null) { console.warn(`  ⚠ sin cuerpo: ${clave}`); continue; }
  paginas.push({ clave, cuerpo, entrada: entradaDe(leer(archivo)) });
}

/** Cada página declara un único módulo de entrada; se lo identifica por su nombre de archivo. */
function entradaDe(html) {
  const m = html.match(/src="\/_assets\/(hoisted\.[^"]+\.js)"/);
  return m ? m[1] : null;
}

// Las fichas de metodología son sub-páginas: mismo tratamiento, otra entrada.
if (CON_FICHAS && !EXCLUIDAS.has('metodologia')) {
  const dirMet = path.join(DIST, 'metodologia');
  for (const sub of fs.readdirSync(dirMet).filter(d => existe(path.join(dirMet, d, 'index.html')))) {
    const html = leer(path.join(dirMet, sub, 'index.html'));
    const cuerpo = cuerpoDe(html);
    if (cuerpo != null) paginas.push({ clave: `metodologia-${sub}`, cuerpo, entrada: entradaDe(html), ficha: true });
  }
}

if (!paginas.length) { console.error('✗ no quedó ninguna sección'); process.exit(1); }

// ── Reescritura del markup ────────────────────────────────────────────────────────────────
const anclar = html => html
  // `/#snapshot` y `/metodologia/#marco`: apuntan a un ancla dentro de otra sección. Se
  // conserva el ancla y se descarta la ruta — el runtime sabe encontrar en qué sección vive.
  .replace(/href="\/[a-z0-9_/-]*#([a-zA-Z0-9_-]+)"/g, 'href="#$1"')
  .replace(/href="\/metodologia\/([a-z0-9_-]+)\/?"/g, CON_FICHAS ? 'href="#metodologia-$1"' : 'href="#metodologia"')
  .replace(/href="\/([a-z0-9_-]+)\/?"/g, 'href="#$1"')
  .replace(/href="\/"/g, 'href="#inicio"');

/** Los `<script src>` ya viajan empotrados más abajo; dejarlos sería pedir archivos que no hay. */
const sinScriptsExternos = html => html
  .replace(/<script[^>]*\ssrc="\/[^"]*"[^>]*><\/script>/g, '')
  .replace(/<vercel-analytics[^>]*><\/vercel-analytics>/g, '');

/** Las imágenes del sitio son cuatro y chicas: se empotran en base64. */
const imagenes = new Map();
for (const img of ['cigob-icono.png', 'favicon.png', 'logo-cigob.png']) {
  const p = path.join(DIST, img);
  if (existe(p)) imagenes.set(`/${img}`, `data:image/png;base64,${fs.readFileSync(p).toString('base64')}`);
}
const empotrarImagenes = html => {
  let out = html;
  for (const [ruta, datos] of imagenes) out = out.replaceAll(`"${ruta}"`, `"${datos}"`);
  return out;
};

const limpiar = frag => empotrarImagenes(sinScriptsExternos(anclar(frag)));

// El nav pierde el resaltado del servidor: lo recalcula la navegación por hash.
let nav = limpiar(navCrudo).replace(/\sclass="active"|\saria-current="page"/g, '');
for (const clave of EXCLUIDAS) {
  nav = nav.replace(new RegExp(`<a href="#${clave}"[^>]*>[\\s\\S]*?</a>`, 'g'), '');
}

// ── CSS ───────────────────────────────────────────────────────────────────────────────────
const hojas = [path.join(DIST, 'marca.css'), path.join(DIST, 'dashboard.css'), path.join(DIST, 'overrides.css')];
for (const f of fs.readdirSync(ASSETS).filter(n => n.endsWith('.css'))) {
  if (LITE && n_esMath(f)) continue;
  hojas.push(path.join(ASSETS, f));
}
function n_esMath(nombre) { return nombre.startsWith('math.'); }

let css = hojas.filter(existe).map(leer).join('\n');

if (LITE) {
  // Sin KaTeX no hay para qué pedir sus fuentes.
  css = css.replace(/@font-face\{[^}]*KaTeX[^}]*\}/g, '');
} else {
  /**
   * Cada @font-face de KaTeX ofrece woff2, woff y ttf. Se conserva sólo el woff2 empotrado:
   * los tres formatos serían 1,2 MB para que el navegador use uno.
   */
  css = css.replace(/url\(\/_assets\/([^)]+?)\)\s*format\("(woff2)"\)/g, (todo, nombre) => {
    const f = path.join(ASSETS, nombre);
    if (!existe(f)) return todo;
    return `url(data:font/woff2;base64,${fs.readFileSync(f).toString('base64')}) format("woff2")`;
  });
  // Los formatos viejos se descartan: si quedaran, serían pedidos a archivos inexistentes.
  css = css.replace(/,\s*url\(\/_assets\/[^)]+\)\s*format\("(woff|truetype|ttf)"\)/g, '');
}
// Cualquier url() a un asset que no se empotró apuntaría al vacío.
css = css.replace(/url\(\/_assets\/[^)]+\)/g, 'none');

css += `
/* ── Añadido por tools/emitir-artifact.mjs ── */
.cg-pagina{display:none}
.cg-pagina.es-activa{display:block}
.cg-artifact-aviso{margin:0;padding:8px 16px;background:#f4f1ea;border-bottom:1px solid #ece6da;font-size:12.5px;color:#5b635f;text-align:center}
`;

// ── JavaScript ────────────────────────────────────────────────────────────────────────────
/**
 * El orden importa: cada módulo se empotra después de aquello de lo que depende, porque los
 * imports pasaron a ser lecturas de globales y un global se lee cuando ya se escribió.
 */
const modulos = [];
const problemasJs = [];

/** Reescribe un export nombrado de Rollup a una asignación global. Ojo con los `$` y `_`. */
const exportarComo = (src, alias, global) => {
  const m = src.match(new RegExp(`export\\{([$\\w]+) as ${alias}\\}`));
  if (!m) { problemasJs.push(`no encontré \`export{… as ${alias}}\``); return src; }
  return src.replace(m[0], `${global}=${m[1]}`);
};

// ApexCharts: empotrado, o traído por CDN y sólo renombrado.
if (LITE) {
  modulos.push({ nombre: 'apex-cdn', src: 'window.__cgApex=window.ApexCharts;' });
} else {
  const f = assetQueEmpieza('vendor-apexcharts.');
  if (!f) problemasJs.push('falta el bundle de ApexCharts');
  else modulos.push({ nombre: 'apexcharts', src: exportarComo(leer(f), 'A', 'window.__cgApex') });
}

// KaTeX: en lite no viaja, y las fórmulas caen a su LaTeX crudo (ver el shim de abajo).
const fMath = assetQueEmpieza('math.');
if (!LITE && fMath) {
  modulos.push({ nombre: 'math', src: exportarComo(leer(fMath), 'renderFormula', 'window.__cgMath') });
} else {
  modulos.push({
    nombre: 'math-fallback',
    src: 'window.__cgMath=(el,latex)=>{el.textContent=latex;el.classList.add("cg-formula-cruda");};',
  });
}

/** Las reescrituras comunes a todo módulo de página. */
const desimportar = src => src
  // El helper de preload de Vite no tiene nada que precargar acá.
  .replace(/import\{_ as ([$\w]+)\}from"\.\/hoisted\.[^"]+"/g, 'const $1=(f)=>Promise.resolve(f())')
  // Analytics: se neutraliza en vez de empotrarse.
  .replace(/import\{t as ([$\w]+)\}from"\.\/analytics\.[^"]+"/g, 'const $1=()=>{}')
  // `@vercel/analytics`, el único pedido a un tercero del build.
  .replace(/import"\.\/hoisted\.[^"]+";?/g, '')
  .replace(/import\{renderFormula as ([$\w]+)\}from"\.\/math\.[^"]+"/g, 'const $1=window.__cgMath')
  // Los `import()` dinámicos: el especificador es literal, así que se resuelve contra el global.
  .replace(/import\("\.\/charts\.[^"]+"\)/g, 'Promise.resolve(window.__cgCharts)')
  .replace(/import\("\.\/math\.[^"]+"\)/g, 'Promise.resolve({renderFormula:window.__cgMath})')
  // La portada exporta el helper de preload (`export{J as _}`). Nadie se lo pide acá, y un
  // `export` dentro de la función que envuelve al módulo directamente no compila.
  .replace(/export\{[^}]*\};?/g, '');

// charts.js expone diez funciones que los módulos de página piden por destructuring.
const fCharts = assetQueEmpieza('charts.');
if (!fCharts) problemasJs.push('falta charts.js');
else {
  // El export se captura del original: `desimportar` borra los `export{…}`, y acá el export
  // es justamente lo que hay que conservar — convertido en objeto global.
  const crudo = leer(fCharts);
  const m = crudo.match(/export\{([^}]*)\}/);
  if (!m) problemasJs.push('charts.js no exporta nada reconocible');
  else {
    // `export{$ as COLOR_CINTURON,j as barChart,…}` → un objeto con esos mismos nombres.
    const pares = m[1].split(',').map(p => p.trim().split(/\s+as\s+/)).filter(p => p.length === 2);
    const src = desimportar(crudo)
      .replace(/import\{A as ([$\w]+)\}from"\.\/vendor-apexcharts\.[^"]+"/, 'const $1=window.__cgApex')
      + `\nwindow.__cgCharts={${pares.map(([local, exp]) => `${exp}:${local}`).join(',')}};`;
    modulos.push({ nombre: 'charts', src });
  }
}

/**
 * Los módulos de página se envuelven en una función por sección. El parámetro `document` tapa
 * al global dentro del scope, así que el código de la página sigue creyendo que está solo en
 * su documento — que es exactamente el supuesto con el que fue escrito.
 */
const entradas = new Map();
/**
 * `hoisted.DJFWlTNo.js` es `@vercel/analytics` entero, y resulta ser la entrada declarada de
 * Frontada y Metodología — que no tienen otra lógica. Empotrarlo metería la llamada a
 * `va.vercel-scripts.com` en el archivo, así que esas dos secciones se quedan sin entrada:
 * no pierden nada, porque no hacían nada más.
 */
const esAnalytics = nombre => {
  const f = path.join(ASSETS, nombre);
  return existe(f) && /va\.vercel-scripts|@vercel\/analytics/.test(leer(f));
};

for (const pagina of paginas) {
  const { entrada } = pagina;
  if (!entrada) continue;
  if (esAnalytics(entrada)) { pagina.entrada = null; continue; }
  if (entradas.has(entrada)) continue;
  const f = path.join(ASSETS, entrada);
  if (!existe(f)) { problemasJs.push(`falta ${entrada}`); continue; }
  entradas.set(entrada, desimportar(leer(f)));
}

const iniciadores = [...entradas].map(([nombre, src]) =>
  `window.__cgInit[${JSON.stringify(nombre)}]=function(document){\n${src}\n};`,
).join('\n');

/**
 * La navegación por hash, el scope por sección y el arranque diferido de cada una.
 *
 * Se emite como `type="module"` y último, no por gusto: los módulos son diferidos y corren en
 * orden de aparición, así que siendo el último tiene garantizado que ApexCharts, KaTeX y
 * charts ya quedaron en `window`. Como script clásico corría *antes* que todos ellos — hoy no
 * se notaría, porque los gráficos se piden dentro de callbacks, pero la primera sección que
 * necesitara un gráfico al inicializarse se rompería sin hacer ruido.
 */
const runtime = `
window.__cgInit = {};
${iniciadores}
(function () {
  var paginas = Array.prototype.slice.call(document.querySelectorAll('.cg-pagina'));
  var links = Array.prototype.slice.call(document.querySelectorAll('.cg-nav-links a[href^="#"]'));
  var real = document;

  // El document acotado: busca primero dentro de la sección y cae al real para todo lo demás
  // (document.body, addEventListener, createElement…), que sí son globales de verdad.
  function scope(seccion) {
    return new Proxy(real, {
      get: function (t, k) {
        if (k === 'getElementById') return function (id) {
          return seccion.querySelector('[id="' + String(id).replace(/"/g, '\\\\"') + '"]') || real.getElementById(id);
        };
        if (k === 'querySelector') return function (s) { return seccion.querySelector(s) || real.querySelector(s); };
        if (k === 'querySelectorAll') return function (s) { return seccion.querySelectorAll(s); };
        var v = t[k];
        return typeof v === 'function' ? v.bind(t) : v;
      },
    });
  }

  // Un hash puede ser una sección ("#macro") o un punto dentro de una ("#snapshot", que en el
  // sitio era "/#snapshot"). En el segundo caso hay que activar la sección que lo contiene y
  // recién después bajar hasta él, porque mientras está oculta no tiene posición.
  function ubicar(clave) {
    var seccion = real.getElementById('p-' + clave);
    if (seccion) return { seccion: seccion, foco: null };
    var el = real.querySelector('[id="' + String(clave).replace(/"/g, '\\\\"') + '"]');
    var cont = el && el.closest ? el.closest('.cg-pagina') : null;
    return cont ? { seccion: cont, foco: el } : null;
  }

  function activar(clave, empujar) {
    var ubic = ubicar(clave);
    var destino = ubic ? ubic.seccion : paginas[0];
    if (!ubic) clave = destino.id.slice(2);

    paginas.forEach(function (p) { p.classList.toggle('es-activa', p === destino); });
    var claveSeccion = destino.id.slice(2);
    links.forEach(function (a) {
      var suya = (a.getAttribute('href') || '').slice(1);
      var activa = suya === claveSeccion;
      a.classList.toggle('active', activa);
      if (activa) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });

    // Cada sección corre su módulo una sola vez, y recién cuando se la ve: los gráficos de
    // ApexCharts miden el contenedor al construirse y uno oculto mide cero.
    var entrada = destino.dataset.entrada;
    if (entrada && destino.dataset.iniciada !== '1' && window.__cgInit[entrada]) {
      destino.dataset.iniciada = '1';
      try { window.__cgInit[entrada](scope(destino)); }
      catch (e) { console.error('[artifact] falló la sección ' + clave, e); }
    }

    if (empujar && location.hash.slice(1) !== clave) history.replaceState(null, '', '#' + clave);

    if (ubic && ubic.foco) ubic.foco.scrollIntoView({ block: 'start' });
    else window.scrollTo(0, 0);
  }

  real.addEventListener('click', function (ev) {
    var a = ev.target.closest ? ev.target.closest('a[href^="#"]') : null;
    if (!a) return;
    var clave = a.getAttribute('href').slice(1);
    if (!clave || !ubicar(clave)) return; // anclas que no llevan a ninguna sección
    ev.preventDefault();
    activar(clave, true);
  });

  window.addEventListener('hashchange', function () { activar(location.hash.slice(1) || 'inicio', false); });
  activar(location.hash.slice(1) || 'inicio', false);
})();
`;

if (problemasJs.length) {
  console.error('✗ no pude reescribir los módulos:');
  for (const p of problemasJs) console.error(`    · ${p}`);
  process.exit(1);
}

// ── Ensamblado ────────────────────────────────────────────────────────────────────────────
const cuerpo = paginas.map(({ clave, cuerpo, entrada }) =>
  `<div class="cg-pagina" id="p-${clave}"${entrada ? ` data-entrada="${entrada}"` : ''}>${limpiar(cuerpo)}</div>`,
).join('\n');

const aviso = LITE
  ? 'Archivo único. Los gráficos cargan ApexCharts desde cdnjs, así que necesitan conexión. Sin fórmulas tipografiadas.'
  : 'Archivo único y autocontenido: no hace un solo pedido a la red.';

const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monitor del Plan de Gobierno · CiGob</title>
<meta name="generator" content="web/tools/emitir-artifact.mjs — desde web/dist">
<style>${css}</style>
</head>
<body>
${nav}
<p class="cg-artifact-aviso">${aviso}</p>
${cuerpo}
${LITE ? `<script src="${APEX_CDN}"></script>` : ''}
${modulos.map(m => `<script type="module">${m.src}</script>`).join('\n')}
<script type="module">${runtime}</script>
</body>
</html>
`;

// ── Control ───────────────────────────────────────────────────────────────────────────────
// "Autocontenido" es la promesa del archivo y se rompe en silencio: una ruta sin empotrar no
// molesta hasta que alguien lo abre sin servidor, y un `export` que sobrevive al inline voltea
// un módulo entero sin decir nada.
const problemas = [];

const rutasVivas = [...new Set([...html.matchAll(/\s(?:src|href)="(\/[^"]*)"/g)].map(m => m[1]))];
if (rutasVivas.length) problemas.push(`rutas absolutas sin empotrar: ${rutasVivas.slice(0, 6).join(', ')}`);
if (/export\{/.test(html)) problemas.push('quedó un `export{…}` en un <script type="module"> inline: ese módulo no ejecuta');
const importesVivos = [...new Set([...html.matchAll(/import[\s{(]["'.][^"']*from"(\.[^"]*)"/g)].map(m => m[1]))];
if (importesVivos.length) problemas.push(`imports relativos sin resolver: ${importesVivos.join(', ')}`);
if (/import\("\.\//.test(html)) problemas.push('quedó un import() dinámico con ruta relativa');
if (!/window\.__cgApex=/.test(html)) problemas.push('ApexCharts no quedó expuesto: ningún gráfico va a pintar');

const externas = [...new Set([...html.matchAll(/https?:\/\/[a-z0-9.-]+/gi)].map(m => m[0]))]
  .filter(u => !u.startsWith('http://www.w3.org'));
const terceros = externas.filter(u => /va\.vercel-scripts|googletagmanager|google-analytics|fonts\.googleapis|fonts\.gstatic/.test(u));
if (terceros.length) problemas.push(`quedaron llamadas a terceros: ${terceros.join(', ')}`);

const ids = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]));
const anclasMuertas = [...new Set([...html.matchAll(/href="#([^"]+)"/g)].map(m => m[1]))]
  .filter(a => a && !ids.has(a) && !ids.has(`p-${a}`));
if (anclasMuertas.length) problemas.push(`enlaces a anclas que no existen: ${anclasMuertas.slice(0, 8).join(', ')}`);

if (problemas.length) {
  console.error('✗ el artifact no quedó autocontenido:');
  for (const p of problemas) console.error(`    · ${p}`);
  process.exit(1);
}

fs.mkdirSync(SALIDA_DIR, { recursive: true });
const nombre = `informe-artifact${LITE ? '-lite' : ''}.html`;
fs.writeFileSync(path.join(SALIDA_DIR, nombre), html);

console.log(`Emitido dist-artifact/${nombre} — ${paginas.length} secciones, ${Math.round(html.length / 1024)} KB. ✓`);
console.log(`  ApexCharts ${LITE ? 'por CDN' : 'empotrado'} · fórmulas ${LITE ? 'en LaTeX crudo' : 'con KaTeX'} · vercel-analytics descartado`);
console.log(externas.length ? `  pedidos a la red: ${externas.join(', ')}` : '  pedidos a la red: ninguno — funciona sin conexión.');
