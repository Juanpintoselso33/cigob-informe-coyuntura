// Render de fórmulas LaTeX con KaTeX (cargado on-demand desde el modal, como
// ApexCharts: no pesa en la carga de página si nadie abre un indicador).
import "katex/dist/katex.min.css";
import katex from "katex";

export function renderFormula(el: HTMLElement, latex: string) {
  katex.render(latex, el, { displayMode: true, throwOnError: false });
}
