// Genera coordenadas para sparklines y charts SVG a partir de una serie de valores.
export interface PuntoSerie { fecha: string; valor: number; }

export interface SparkPaths {
  linea: string;   // "M x,y L x,y ..."
  area: string;    // path cerrado para el relleno
  ultimo: { x: number; y: number } | null;
  vacio: boolean;
}

// Tope de puntos que dibuja una sparkline de lista. Antes se pasaba la serie
// COMPLETA a 60x22px, así que las más largas comprimían ocho años en 60 píxeles
// (brecha_obra_publica tiene 100 puntos contra una mediana de 32 por card) y dos
// filas del mismo ancho podían cubrir períodos muy distintos sin que nada lo
// indicara.
//
// No iguala los períodos —eso exigiría recortar todas al largo de la más corta—
// sino que ACOTA los casos extremos: ninguna card comprime más de cuatro años.
//
// Va acá y no en un componente porque hay DOS caminos de render: las filas de la
// home (Sparkline.astro) y las tiles de las páginas de cinturón
// (IndicadorTile.astro, que llama a esta función directo). Puesto en uno solo,
// el mismo indicador quedaba con 48 puntos en un lado y 100 en el otro.
//
// No recorta el DATO: el gráfico del modal usa ApexCharts, y su tabla y su CSV
// descargable siguen con la serie entera.
//
// Al 29-jul-2026 ninguna card renderiza más de 33 puntos, así que esto todavía
// no cambia nada visible: entra a jugar cuando el cron publique las series que
// se registraron el mismo día (`alquiler_real` 59 puntos, `indice_lider` 60).
export const VENTANA_SPARK = 48;

// w/h en unidades de viewBox; pad vertical para que la línea no toque los bordes.
export function sparkline(serie: PuntoSerie[], w = 60, h = 22, pad = 3): SparkPaths {
  const vals = serie.slice(-VENTANA_SPARK).map(p => p.valor);
  if (vals.length < 2) return { linea: "", area: "", ultimo: null, vacio: true };
  const min = Math.min(...vals), max = Math.max(...vals);
  const span = max - min || 1;
  const stepX = w / (vals.length - 1);
  const pts = vals.map((v, i) => ({
    x: +(i * stepX).toFixed(2),
    y: +(h - pad - ((v - min) / span) * (h - 2 * pad)).toFixed(2),
  }));
  const linea = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x},${p.y}`).join(" ");
  const area = `${linea} L${pts[pts.length - 1].x},${h} L${pts[0].x},${h} Z`;
  return { linea, area, ultimo: pts[pts.length - 1], vacio: false };
}

// Variante para el gráfico grande / minis (mismo cálculo, distinto tamaño).
export function chartPath(serie: PuntoSerie[], w: number, h: number, pad = 6): SparkPaths {
  return sparkline(serie, w, h, pad);
}
