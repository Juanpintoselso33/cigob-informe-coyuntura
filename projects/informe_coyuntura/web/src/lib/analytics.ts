/**
 * Envoltorio de GA4 (gtag.js).
 *
 * `gtag` solo existe si PUBLIC_GA_ID está cargada — ver Layout.astro. En dev
 * local, en previews y en cualquier build sin la variable, `track()` no hace
 * nada. Medir nunca debe poder romper la página: si algo falla acá, la
 * interacción del usuario sigue.
 *
 * Convenciones de GA4 que respetan los nombres de este archivo:
 * - nombres de evento y de parámetro en snake_case, máx. 40 caracteres
 * - máx. 25 parámetros por evento
 * - un parámetro solo sirve en informes si además está dado de alta como
 *   dimensión personalizada en GA4 (Administrar → Definiciones personalizadas).
 *   Las de este proyecto: indicador, cinturon, dimension, estado.
 *
 * Ojo con `estado`: es el badge de badgeEstado() — "Automático" | "Carga
 * manual" | "Estimación", o sea CÓMO se obtiene el dato. No confundir con el
 * campo `estado` del cinturón en el snapshot (estable/en_tension/tensionado),
 * que es el semáforo y no se envía a GA4.
 */

type ValorParam = string | number | boolean | null | undefined;

declare global {
  interface Window {
    gtag?: (comando: string, ...args: unknown[]) => void;
  }
}

export function track(evento: string, params: Record<string, ValorParam> = {}): void {
  if (typeof window === "undefined" || typeof window.gtag !== "function") return;

  // Los valores vacíos se descartan: en los informes aparecerían como
  // "(not set)" y ensucian los desgloses sin aportar nada.
  const limpio: Record<string, string | number | boolean> = {};
  for (const [clave, valor] of Object.entries(params)) {
    if (valor !== undefined && valor !== null && valor !== "") limpio[clave] = valor;
  }

  try {
    window.gtag("event", evento, limpio);
  } catch {
    /* medir es best-effort; nunca interrumpe al usuario */
  }
}
