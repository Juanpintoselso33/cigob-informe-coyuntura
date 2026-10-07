// La cookie que recuerda que alguien ya pasó el muro (ADR-0342, persistencia).
// La escribe SIEMPRE el servidor: si la reescribiera JavaScript, Safari le
// pondría el tope de 7 días. No es HttpOnly a propósito: el script de <head>
// de Layout.astro la lee antes de pintar. 400 días es el tope de Chrome, por
// eso se renueva en cada visita (api/acceso.ts).
export const COOKIE = "cigob_lector";

export function cookieDeAcceso(): string {
  return `${COOKIE}=1; Max-Age=34560000; Path=/; Secure; SameSite=Lax`;
}
