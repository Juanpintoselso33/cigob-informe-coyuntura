// Los links de las difusiones de WhatsApp pasan por acá (el redirect /r/ del bot
// arma /api/acceso?t=<token>&next=<ruta>). Desde que se sacó el muro de acceso
// (ADR-0441) no hay nada que reconocer: sólo se manda a la página, sin el token.

/** Sólo rutas internas del sitio: nunca redirigir afuera con lo que venga en la URL. */
function destinoSeguro(next: unknown): string {
  const n = String(next ?? "/");
  return n.startsWith("/") && !n.startsWith("//") && !n.startsWith("/\\") ? n : "/";
}

export default function handler(req: any, res: any) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
  res.redirect(302, destinoSeguro(req.query?.next));
}
