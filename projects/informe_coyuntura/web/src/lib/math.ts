// Render de fórmulas LaTeX con KaTeX (cargado on-demand desde el modal, como
// ApexCharts: no pesa en la carga de página si nadie abre un indicador).
import "katex/dist/katex.min.css";
import katex from "katex";

// Auto-ajuste (mobile): si la fórmula es más ancha que su caja, se escala el
// font-size (KaTeX dimensiona todo en em) para que entre SIN scroll, con un
// piso de legibilidad; por debajo del piso queda el scroll de red. El modal
// puede estar todavía display:none al renderizar (clientWidth 0): se
// reintenta por frames hasta que sea visible.
// El ancho REAL pintado: scrollWidth miente con KaTeX (las etiquetas de los
// underbrace viven en vlists con márgenes negativos que pintan fuera de la
// caja de layout) — se mide la extensión de las bounding boxes de todos los
// nodos de la fórmula.
function anchoPintado(el: HTMLElement): number {
  let min = Infinity, max = -Infinity;
  // SOLO la capa visual (.katex-html): la capa MathML de accesibilidad está
  // clipeada pero reporta bounding boxes gigantes. Y de los SVG (llaves
  // estirables) se mide el contenedor, no los <path> internos (reportan su
  // geometría sin el recorte del viewBox).
  for (const n of el.querySelectorAll(".katex-html, .katex-html *")) {
    if (n instanceof SVGElement && n.tagName.toLowerCase() !== "svg") continue;
    const r = (n as Element).getBoundingClientRect();
    if (r.width === 0) continue;
    if (r.left < min) min = r.left;
    if (r.right > max) max = r.right;
  }
  return max > min ? max - min : 0;
}

function ajustarAncho(el: HTMLElement, intentos = 20) {
  const disponible = el.clientWidth;
  if (disponible === 0) {
    if (intentos > 0) requestAnimationFrame(() => ajustarAncho(el, intentos - 1));
    return;
  }
  // Iterativo: KaTeX no escala perfectamente lineal con el font-size
  // (espesores y espacios con mínimos en px), así que una sola pasada
  // deja residuo — se refina midiendo de nuevo hasta converger.
  let refinos = 4;
  const paso = () => {
    const ancho = anchoPintado(el);
    if (ancho <= disponible + 1 || refinos-- <= 0) return;
    const actual = parseFloat(el.style.fontSize) || 1;
    const factor = Math.max(0.5, actual * (disponible / ancho) * 0.99);
    if (factor >= actual) return;
    el.style.fontSize = factor.toFixed(3) + "em";
    requestAnimationFrame(paso);
  };
  paso();
}

export function renderFormula(el: HTMLElement, latex: string) {
  el.style.fontSize = "";
  katex.render(latex, el, { displayMode: true, throwOnError: false });
  ajustarAncho(el);
  // Primer modal de la página: las webfonts de KaTeX pueden no estar cargadas
  // al medir (la fallback es más angosta y el swap ensancha) — re-ajustar
  // cuando el set de fuentes esté listo.
  if (document.fonts?.ready) {
    document.fonts.ready.then(() => ajustarAncho(el));
  }
}
