# Muro de acceso: cómo reconocer a quien ya dejó el mail (7-oct-2026)

Investigación pedida por Juan el 7-oct-2026 para el pendiente «mejorar la persistencia» del muro
(ADR-0342). Tres casos a resolver:

- **(a)** vuelve el mes siguiente en el mismo navegador;
- **(b)** entra desde otro navegador o dispositivo;
- **(c)** entra en incógnito.

Se relevaron 38 opciones y hay una ficha por cada una.

## El hallazgo que cambia el diagnóstico

**Safari** (casi todos los iPhone) **borra el `localStorage` y las cookies escritas por JavaScript
después de 7 días de uso sin visitar el sitio**
([WebKit](https://webkit.org/tracking-prevention/)). El Monitor se lee una vez por mes, así que hoy,
en iPhone, el muro vuelve a aparecer **todos los meses**.

No le pasa lo mismo a una cookie que manda el **servidor del mismo sitio**. Tiene una sola
excepción: que la respuesta venga de otro host o de una IP de terceros («cloaking»).

Chrome limita cualquier cookie a 400 días desde que se escribe
([Chrome](https://developer.chrome.com/blog/cookie-max-age-expires)), así que hay que renovarla.

## Recomendación

1. **Cookie puesta por el servidor, desde el propio dominio del Monitor.** Resuelve **(a)**.
   - Al dejar el mail, `/api/lector` responde con `Set-Cookie` de 400 días, que se renueva en cada
     visita.
   - No puede ser `HttpOnly`, porque el script de `<head>` la lee. **Nunca reescribirla desde JS**:
     una cookie reescrita por JS cuenta como cookie de JS y Safari le aplica el tope de 7 días.
   - La respuesta tiene que salir del propio dominio, de una de dos formas:
     - con un endpoint propio en el proyecto Astro (`@astrojs/vercel`, sólo esa ruta en servidor);
     - con un rewrite de Vercel hacia el bot. Vercel desaconseja `vercel.json` para reescribir rutas
       en Astro, así que esta forma hay que probarla.
2. **Link personal con token en la difusión.** Resuelve **(b)** y **(c)** sin que el lector haga nada.
   - Quien entra por un link de WhatsApp o mail queda reconocido en ese navegador, también en incógnito
     y en el navegador interno de WhatsApp o Gmail.
   - El servidor valida el token, escribe la cookie y redirige a la URL limpia.
   - Beehiiv hace exactamente esto.
3. **«Ya dejé mi mail»: alcanza con el mail, sin verificar.**
   - Si el mail está en `lectores`, la persona pasa y se escribe la cookie.
   - La respuesta no tiene que revelar si el mail existía.
   - El autocompletado del navegador lo deja en un toque.
4. **Más adelante, opcional: Sign in with Google (One Tap/FedCM).** Es un toque en Android y trae el
   mail ya verificado. Los diarios que lo usan reportan subas grandes de registros.
5. **Un solo dominio.** Redirigir `cigob-informe-coyuntura.vercel.app` a `informe.cigob.org`: las
   cookies son por dominio.

Cada vía de reconocimiento manda su evento de GA4 (`muro_reconocido` con `via`), sin datos personales.

### Lo legal mínimo (Ley 25.326)

- **Aviso visible en el muro** (art. 6 y Res. AAIP 14/2018): para qué se usan los datos, quién es el
  responsable, que nombre y teléfono son opcionales, y cómo pedir acceso o supresión.
- **Inscripción** de la base en el Registro Nacional de Bases de Datos.
- **Transferencia a EE.UU.** Neon y Vercel guardan los datos allá, un país sin «legislación
  adecuada» (Disp. 60/2016, Res. AAIP 34/2019). Hace falta consentimiento expreso o cláusulas
  contractuales.
- **La cookie** se informa en la política de privacidad.

## Las 38 opciones

| # | Opción | (a) | (b) | (c) | Veredicto |
|---|---|---|---|---|---|
| 1 | `localStorage` (lo de hoy) | Chrome sí, Safari no | No | No | Queda de respaldo |
| 2 | `sessionStorage` | No | No | Sólo esa sesión | Sólo para «cerrado en esta visita» |
| 3 | IndexedDB / Cache API / Service Worker | Safari no | No | No | No mejora a la 1 |
| 4 | `navigator.storage.persist()` | Impredecible | No | No | Complemento menor |
| 5 | Cookie escrita por JS | Safari 7 días (o 1) | No | No | No mejora a la 1 |
| 6 | **Cookie de servidor desde un endpoint propio** | **Sí** | No | No | **Recomendada** |
| 7 | Rewrite de Vercel al bot | Sí | No | No | Alternativa a la 6; hay que probarla |
| 8 | Middleware de Vercel con cookie | Sí | Con token | Con token | Variante de la 6 + 14 |
| 9 | Cookie en `.cigob.org` por subdominio del bot | Sí, si coinciden los CNAME | No | No | Más riesgosa que la 6 |
| 10 | Cookie de `cigob-bot.vercel.app` (tercero) | No | No | No | Descartada: Safari bloquea terceros |
| 11 | Storage Access API | — | — | — | Descartada: es para iframes |
| 12 | CHIPS (cookies particionadas) | — | — | — | Descartada: es para embeds |
| 13 | **Un solo dominio** | Ayuda | No | No | **Complemento recomendado** |
| 14 | **Link personal con token en la difusión** | **Sí** | **Sí** | **Sí** | **Recomendada** |
| 15 | Escape del navegador interno de WhatsApp/Gmail | Ayuda | No | No | Opcional; detección frágil |
| 16 | Link mágico por mail | Sí | Sí | Sólo en el mismo navegador | Fricción alta; los escáneres de mail «gastan» el link |
| 17 | Código (OTP) por mail | Sí | Sí | Sí | Fricción media; posible a futuro |
| 18 | Código por WhatsApp | Sí | Sí | Sí | Sólo para quien dejó teléfono; se paga por mensaje |
| 19 | **«Ya me registré» con el mail** | **Sí** (con la 6) | **Sí** | **Sí** | **Recomendada** |
| 20 | Autocompletado (`autocomplete=email/name/tel`) | — | Ayuda | Ayuda | Ya está; complemento |
| 21 | Sign in with Google / One Tap (FedCM) | Sí | Sí | Parcial | Opcional más adelante |
| 22 | FedCM sin Google | — | — | — | Descartada: necesita un proveedor de identidad |
| 23 | Sign in with Apple | Sí | Sí | Parcial | Descartada: US$99/año, exige app, «Hide My Email» |
| 24 | Passkeys / WebAuthn | Sí | Sí | Sí | Descartada: infraestructura de más |
| 25 | Credential Management API | — | — | — | Descartada: Safari no la soporta |
| 26 | Cuenta con contraseña | Sí | Sí | Con login | Descartada: fricción máxima |
| 27 | PWA / pantalla de inicio | Sólo quien instala | No | No | No alcanza; en iOS el almacenamiento queda separado de Safari |
| 28 | Fingerprinting | — | — | — | Descartada: ilegal sin consentimiento (art. 5) y antiético |
| 29 | Piano | Con login | Con login | Con login | Referencia; enterprise, a cotizar |
| 30 | Poool | Frágil | No | No | No resuelve: deja la identificación al editor |
| 31 | Zephr | Con login | Con login | Con login | Enterprise |
| 32 | Memberful | Sí | Sí | No | Usa cookies de terceros; pensado para WordPress |
| 33 | Substack | Con login | Con login | Con login | Implica migrar |
| 34 | Ghost | Sí | Con login | Con login | Referencia: cookie de servidor de 184 días |
| 35 | Beehiiv | Sí | Por link | Por link | Referencia: valida las opciones 14 y 19 |
| 36 | Laterpay / Supertab | — | — | — | Es para cobrar, no para juntar contactos |
| 37 | Google Reader Revenue Manager | Sí | Sí | Parcial | No suma frente a la 21 |
| 38 | Pelcro | Con login | Con login | Con login | Pago, para suscripciones |

Lo que hacen los diarios, como contexto:

- **El País**: muro de registro desde 2019. Su defensora del lector reconoce que en incógnito y en
  los navegadores de las redes «no es posible ofrecer una solución técnica».
- **Clarín**: mail, contraseña y activación por mail.
- **La Nación e Infobae**: no se pudo verificar con fuentes primarias.

## Fichas

### Almacenamiento en el navegador

- **1. `localStorage`.** Safari lo borra a los 7 días de uso sin visitar el sitio; en Chrome dura.
  ([WebKit](https://webkit.org/tracking-prevention/))
- **2. `sessionStorage`.** Dura lo que dura la pestaña.
- **3. IndexedDB, Cache API y Service Worker.** Safari también los borra, porque son almacenamiento
  escrito por script. ([WebKit 10218](https://webkit.org/blog/10218/full-third-party-cookie-blocking-and-more/))
- **4. `persist()`.** Safari 17+ lo concede según heurísticas, sobre todo a las apps instaladas.
  ([WebKit 14403](https://webkit.org/blog/14403/updates-to-storage-policy/))
- **5. Cookie escrita por JS.** Safari la topea a 7 días, y a 1 día si se llegó desde un rastreador
  con parámetros en la URL. ([ITP 2.2](https://webkit.org/blog/8828/intelligent-tracking-prevention-2-2/))

### Cookies de servidor

- **6. Endpoint propio + `Set-Cookie`.** Sin tope en Safari, porque sale del mismo host; 400 días en
  Chrome. Costo bajo-medio: es la primera función de servidor del proyecto y entra en el plan gratis.
  ([Vercel + Astro](https://vercel.com/docs/frameworks/frontend/astro))
- **7. Rewrite de Vercel.** Para el navegador es el mismo host, así que no hay cloaking. Vercel
  recomienda Routing Middleware en lugar de `vercel.json` para Astro.
  ([Vercel rewrites](https://vercel.com/docs/routing/rewrites))
- **8. Routing Middleware.** Puede leer el token, escribir la cookie y redirigir. Conviene limitarlo
  con `matcher` por costo. ([Vercel](https://vercel.com/docs/routing-middleware))
- **9. Subdominio del bot en `.cigob.org`.** Funciona sólo si los CNAME coinciden (los dos a
  `cname.vercel-dns.com`); si no, Safari la topea a 7 días.
- **10. Cookie del dominio del bot.** Es de terceros y Safari la bloquea. Además `vercel.app` está en
  la Public Suffix List.
- **11. Storage Access API.** Es para iframes de terceros.
  ([WebKit 14301](https://webkit.org/blog/14301/introducing-storage-access-api/))
- **12. CHIPS.** Es para embeds. ([Chrome](https://developer.chrome.com/docs/privacy-sandbox/chips/))
- **13. Un solo dominio.** Las cookies son por host: con dos dominios, el lector tiene dos cajas de
  cookies distintas.

### Enlace y código

- **14. Token en la difusión.** El link lleva `?t=<token>`; el servidor lo valida, escribe la cookie
  y redirige limpio. Cuatro cuidados:
  - el token sólo dice «registrado», nunca muestra datos;
  - es reutilizable, porque las vistas previas de WhatsApp y los antivirus de mail abren el link;
  - no se registran visitas a nombre de la persona por reenvíos;
  - el 302 y `Referrer-Policy` evitan que se filtre.

  ([Beehiiv](https://www.beehiiv.com/support/article/26615649310999))
- **15. Escape del navegador interno.** Ofrecer «abrir en Safari/Chrome» (`x-safari-https://`,
  `intent://`). ([referencia](https://www.openlinkinapp.com/deep-link-reference))
- **16. Link mágico.** Se abre en el navegador interno de Gmail o Mail y la sesión no pasa al
  navegador real; Beehiiv lo dejó por eso. Resend: 3.000 mails por mes gratis.
  ([stuffreport](https://stuffreport.com/guides/magic-link-sign-in-emails/))
- **17. Código por mail.** Es lo que usan Beehiiv, Substack, Ghost y Piano; en iOS,
  `autocomplete=one-time-code` lo completa solo.
- **18. Código por WhatsApp.** Plantilla de categoría «authentication»; se paga por mensaje
  (~US$0,03 en Argentina). ([Meta](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing))
- **19. Sólo el mail.** Un `SELECT` en el endpoint. Responde «Listo» exista o no el mail, para no
  revelar quién está registrado.
- **20. Autocompletado.** iOS y Android ofrecen los datos guardados de la persona.

### Identidad federada

- **21. Google One Tap / FedCM.** En Safari iOS cae a una ventana emergente; en Chrome Android es
  nativo. Resultados reportados:
  - Times of India: +30 % de inicios de sesión.
  - Lokmat: +142 % de registros.
  - The News Minute: registros ×8.
  - Axel Springer: registros ×15.

  ([Google](https://developers.google.com/identity/gsi/web/guides/itp))
- **22. FedCM genérico.** Necesita un proveedor de identidad.
- **23. Apple.** US$99 por año, exige app, y el lector puede ocultar su mail.
  ([Apple](https://developer.apple.com/sign-in-with-apple/usage-guidelines-for-websites-and-other-platforms/))
- **24. Passkeys.** Infraestructura de autenticación para algo que no protege nada.
  ([web.dev](https://web.dev/articles/passkey-form-autofill))
- **25. Credential Management API.** Safari no la soporta. ([caniuse](https://caniuse.com/credential-management))
- **26. Contraseña.** Jagran estimó un 25-30 % de abandono por «fatiga de contraseñas».

### Otros

- **27. PWA.** En iOS el almacenamiento de la app queda separado del de Safari, y casi nadie instala
  un informe mensual.
- **28. Fingerprinting.** WebKit lo combate; la Ley 25.326 (art. 5) exige consentimiento, y el EDPB
  lo trata igual en Europa (2/2023).

### Plataformas

- **29. Piano:** enterprise.
- **30. Poool:** no identifica a nadie, se lo deja al editor.
- **31. Zephr:** enterprise.
- **32. Memberful:** usa cookies de terceros.
- **33. Substack:** implica migrar.
- **34. Ghost:** cookie de servidor de 184 días. Es la arquitectura que se recomienda acá.
- **35. Beehiiv:** reconoce por el clic desde la newsletter y por volver a llenar el formulario de
  alta.
- **36. Laterpay:** es para cobrar.
- **37. Reader Revenue Manager:** muro de registro sobre One Tap.
- **38. Pelcro:** pago, para suscripciones.

## Conteo

38 opciones relevadas y 38 fichas entregadas.
