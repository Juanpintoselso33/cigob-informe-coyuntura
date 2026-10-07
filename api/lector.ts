// Muro de acceso del Monitor (ADR-0342): recibe el mail del popup, lo reenvía
// al bot (que lo guarda en Neon) y deja la cookie que recuerda el acceso.
//
// Por qué existe esta función y el popup no le habla directo al bot: Safari
// borra a los 7 días sin visitas todo lo que escribe JavaScript (localStorage y
// cookies de JS), y no deja que un tercero ponga cookies. Una cookie que manda
// el servidor DEL MISMO SITIO no tiene ese tope, y el Monitor se lee una vez por
// mes. Ver docs/261007_muro_persistencia_opciones.md (opción 6).
import { cookieDeAcceso } from "./_acceso";

const BOT = "https://cigob-bot.vercel.app/api/lector";

export default async function handler(req: any, res: any) {
  if (req.method !== "POST") {
    res.status(405).json({ error: "usá POST" });
    return;
  }
  const ip = String(req.headers["x-forwarded-for"] ?? "").split(",")[0].trim();
  let estado = 502;
  let cuerpo: unknown = { error: "No se pudo guardar." };
  try {
    const r = await fetch(BOT, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-lector-ip": ip },
      body: typeof req.body === "string" ? req.body : JSON.stringify(req.body ?? {}),
      // Menos que el corte del navegador (9 s en MuroAcceso.astro): si el bot
      // cuelga, la respuesta con la cookie tiene que llegar antes de que el
      // navegador se rinda y deje entrar sin ella.
      signal: AbortSignal.timeout(4000),
    });
    estado = r.status;
    cuerpo = await r.json().catch(() => ({}));
  } catch (e) {
    console.error("[lector] el bot no respondió:", e);
  }
  // La cookie se deja también si el bot falla: el muro deja entrar igual
  // (ADR-0342) y no tiene sentido volver a pedir el mail el mes que viene por
  // un error nuestro. Sólo un mail mal escrito (400) no la deja.
  if (estado !== 400) res.setHeader("Set-Cookie", cookieDeAcceso());
  res.setHeader("Cache-Control", "no-store");
  res.status(estado).json(cuerpo);
}
