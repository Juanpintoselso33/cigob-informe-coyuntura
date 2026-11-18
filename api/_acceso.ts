// La cookie que recuerda que alguien ya pasó el muro (ADR-0342, persistencia).
// La escribe SIEMPRE el servidor: si la reescribiera JavaScript, Safari le
// pondría el tope de 7 días. No es HttpOnly a propósito: el script de <head>
// de Layout.astro la lee antes de pintar. 400 días es el tope de Chrome, por
// eso se renueva en cada visita (api/acceso.ts).
export const COOKIE = "cigob_lector";

// El valor dice por dónde pasó (18-nov-2026): `m` dejó el mail; `d` entró sólo
// por el link de una difusión, sin dejarlo. A `d` el muro le sigue pidiendo el
// mail (con la cruz para cerrarlo): el link de difusión ya no lo saltea, porque
// así no se juntaba el mail de nadie que llegara por WhatsApp. El `1` de antes
// no distingue y se lee como `m`.
export type ValorAcceso = "m" | "d";

export function cookieDeAcceso(valor: ValorAcceso = "m"): string {
  return `${COOKIE}=${valor}; Max-Age=34560000; Path=/; Secure; SameSite=Lax`;
}

/** El valor de la cookie que trae el pedido, o "" si no la trae. */
export function valorActual(req: any): string {
  const m = String(req.headers?.cookie ?? "").match(new RegExp(`(?:^|;\\s*)${COOKIE}=([^;]*)`));
  return m ? m[1] : "";
}
