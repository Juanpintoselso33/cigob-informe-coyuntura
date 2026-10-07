// Reconocer a quien ya pasó el muro (ADR-0342, persistencia). Dos usos:
//
// 1. Con ?t=<token>: el link de una difusión por WhatsApp pasa por acá (el
//    redirect /r/ del bot). Si el bot reconoce el token, la persona ya está en
//    la lista: se deja la cookie y se la manda a la página, sin el token en la
//    URL. Funciona en cualquier dispositivo, también en incógnito y en el
//    navegador interno de WhatsApp. Si el token no es válido, igual se la manda
//    a la página: el muro le pedirá el mail como a cualquiera.
// 2. Sin token: renueva la cookie de alguien que el navegador ya reconoce
//    (cookie o localStorage). Chrome corta toda cookie a los 400 días de
//    escrita, y quien tenía sólo el localStorage de antes pasa a tener cookie.
//    El muro es blando: no hay nada que proteger en esta renovación.
import { cookieDeAcceso } from "./_acceso";

const BOT = "https://cigob-bot.vercel.app/api/acceso";

/** Sólo rutas internas del sitio: nunca redirigir afuera con lo que venga en la URL. */
function destinoSeguro(next: unknown): string {
  const n = String(next ?? "/");
  return n.startsWith("/") && !n.startsWith("//") && !n.startsWith("/\\") ? n : "/";
}

export default async function handler(req: any, res: any) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
  const token = String(req.query?.t ?? "").replace(/[^A-Za-z0-9_-]/g, "");
  if (!token) {
    res.setHeader("Set-Cookie", cookieDeAcceso());
    res.status(204).end();
    return;
  }
  let ok = false;
  try {
    const r = await fetch(`${BOT}?t=${encodeURIComponent(token)}`, { signal: AbortSignal.timeout(6000) });
    ok = Boolean(((await r.json()) as { ok?: boolean }).ok);
  } catch (e) {
    console.error("[acceso] el bot no respondió:", e);
  }
  if (ok) res.setHeader("Set-Cookie", cookieDeAcceso());
  res.redirect(302, destinoSeguro(req.query?.next));
}
