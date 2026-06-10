---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Integrar el Informe de Coyuntura (dashboard estático en GitHub Pages, deploy diario) dentro de cigob.org (Wix Studio) de modo que se sienta nativo'
session_goals: 'Explorar opciones más allá del iframe simple y llegar a una recomendación fundada'
selected_approach: 'ai-recommended'
techniques_used: ['Assumption Reversal', 'Morphological Analysis', 'Solution Matrix']
ideas_generated: ['camino-blend-cigob', 'iframe-contexto-propio', 'auto-resize-postmessage', 'menu-unico-subnav-interna', 'subcarpeta-cigob-informe', 'plan-prueba-sin-wix']
session_active: false
workflow_completed: true
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Juan
**Date:** 2026-06-06

## Session Overview

**Topic:** Cómo integrar el Informe de Coyuntura (dashboard estático multipágina publicado en GitHub Pages con deploy automático diario) dentro de un sitio Wix de modo que se sienta parte del sitio Wix (header/menú presentes), sin romper el flujo de auto-deploy.

**Goals:** Explorar opciones de integración más allá del iframe obvio y llegar a una recomendación fundada.

### Session Setup

**Prioridades del usuario:**

- 🔒 Innegociables: **Visual** (estilo del informe debe matchear el sitio Wix, no parecer un cajón pegado) + **Navegación** (menú de Wix siempre visible, el usuario nunca siente que "salió").
- ⭐ Importan: **Mobile** (verse bien en celular) + **Dominio** (URL bajo dominio propio, no github.io).
- ➖ Secundario: continuidad de scroll.

**Restricciones técnicas conocidas:**
- Informe = sitio estático en `https://juanpintoselso33.github.io/biblitotecario-ai/informe/`, deploy diario automático vía GitHub Actions.
- GitHub Pages NO envía `X-Frame-Options` ni `frame-ancestors` → embebible en iframe sin bloqueo.
- Wix: el elemento de embed/iframe requiere plan Premium.

**Sitio destino (verificado en vivo):**
- Destino = **https://www.cigob.org/**, construido en **Wix Studio (EditorX)**. Soporta embeds HTML/iframe en plan Premium.
- Identidad cigob.org: fondo blanco, paleta celeste/turquesa, tipografía sans redondeada, logo aros CiGob. Menú: Inicio · Método CiGob · Soluciones · Novedades · Testimonios.

**Realidad visual del informe (verificada en vivo — corrige supuesto previo):**
- El informe NO es oscuro. Es CLARO y editorial: fondo crema/off-white, headings serif, acentos teal/verde/naranja, cards con borde superior de color, footer navy con logo "Realidad Política Argentina · Fundación CiGob".
- Ya está marcado como propiedad CiGob (header "Observatorio · Fundación CiGob", footer con links a cigob.org).
- Conclusión: informe y cigob.org son la MISMA familia de marca (primos cercanos). El match visual está ~80% hecho. Gap real = armonizar crema↔blanco y teal↔celeste, NO rediseñar.

**Decisión tomada (vía Assumption Reversal):**
- Camino elegido = **el informe se ve CiGob, fundido en el sitio** (no "zona app" diferenciada).
- El reversal descartó el falso problema "choque oscuro/claro". El trabajo real es INTEGRAR bien, no rediseñar.

---

## Técnicas aplicadas

### 1. Assumption Reversal (deep)
Sacó a la luz 5 supuestos ocultos. El flip del supuesto C ("match visual = informe imita Wix") nos hizo verificar la realidad en vivo y **descartó un falso problema**: yo había asumido que el informe era oscuro y chocaba con cigob.org. Verificación en vivo: el informe es CLARO/editorial (crema + teal + serif), ya marcado como propiedad CiGob. Conclusión: misma familia de marca, no hay choque. El trabajo es **integrar, no rediseñar**.

### 2. Morphological Analysis (deep)
Descompuso "integrar en cigob.org" en 5 parámetros independientes (mecanismo, hosting, navegación, altura, dominio) y mapeó opciones reales para Wix Studio. Decisiones del usuario:
- **Navegación:** un único ítem "Informe" en el menú de CiGob; sub-navegación (Macro/Política/Vida/Gestión) **adentro** del informe → no satura el front.
- **Dominio:** `cigob.org/informe` (subcarpeta vía página Wix) alcanza.

### 3. Solution Matrix (structured)
Puntuó el combo ganador contra las prioridades. Hallazgo técnico decisivo (verificado en vivo): el informe es **multipágina** (cada cinturón es su URL), y como el **iframe es su propio contexto de navegación**, los clics internos navegan dentro del iframe SIN recargar la página de Wix. El único reto real es la **altura variable** entre páginas → lo resuelve el auto-resize por `postMessage`, viable porque el usuario controla el código del informe.

---

## Recomendación final (combo ganador)

> **Página Wix dedicada `cigob.org/informe`** (entra al menú de CiGob) → elemento **Embed / iframe** apuntando al informe en GitHub Pages → **navegación interna del informe intacta** → **auto-resize por `postMessage`** para que no haya doble scroll.

| Prioridad | Cumple | Nota |
|---|---|---|
| 🔒 Visual (CiGob) | ✅ | Misma familia de marca; sólo armonizar crema↔blanco / teal↔celeste |
| 🔒 Navegación (menú Wix) | ✅ | Header/menú CiGob siempre arriba; sub-nav adentro |
| ⭐ Mobile | ✅ | Iframe responsive + informe ya responsive |
| ⭐ Dominio | ✅ | `cigob.org/informe` (página Wix) |
| Deploy diario intacto | ✅ | Informe sigue en Pages; el script va en el build |
| Sin doble scroll | ✅ | Lo resuelve el auto-resize |

**Dato que destraba:** cigob.org usa dominio propio → ya es plan **Premium** de Wix → el elemento Embed está habilitado, no hay que comprar nada.

---

## División de trabajo: ¿qué es boludez y qué es desarrollo?

| Tarea | Lado | Tipo |
|---|---|---|
| Crear página "Informe" + sumarla al menú | Wix | **Boludez** no-code (~2 min) |
| Poner elemento Embed y pegar la URL del informe | Wix | **Boludez** no-code |
| Script "height-poster" en el informe | Tu repo | Edición chica en el build (1 archivo) |
| Snippet Velo que escucha la altura | Wix | Copy-paste (te lo damos hecho) |
| Página de prueba para validar sin Wix | Tu repo | Ya creada |

**Camino mínimo = 100% no-code en Wix.** Lo único con código es opcional (auto-resize) y se entrega pre-escrito para pegar.

---

## PLAN DE ACCIÓN

### Fase 0 — Validar sin Wix (ya podés hacerlo hoy)
1. Abrí `projects/informe_coyuntura/test-embed-wix.html` con doble clic en el navegador.
2. Verificá: ¿el informe se ve bien bajo un header tipo CiGob? ¿La sub-navegación (Macro/Política/…) funciona dentro del marco? ¿En mobile (achicá la ventana) se banca?
3. Si algo no encaja, se ajusta acá antes de tocar Wix.

### Fase 1 — Versión que YA FUNCIONA (no-code, pedido-boludez a Wix)
Pedido textual para quien tenga acceso a Wix Studio:
> "En cigob.org: creá una página nueva llamada **Informe** (URL `cigob.org/informe`) y agregala al menú principal. Adentro, poné un elemento **Embed → Insertar HTML / iframe** que ocupe el ancho completo y bastante alto, apuntando a esta dirección:
> `https://juanpintoselso33.github.io/biblitotecario-ai/informe/`"

Resultado: informe embebido, menú CiGob arriba, sub-navegación adentro. Único compromiso temporal: scroll interno del iframe (doble scroll) — secundario según prioridades.

### Fase 2 — Pulido "funciona perfecto" (auto-resize, sin doble scroll)

**a) En tu repo** — agregar el height-poster en `projects/informe_coyuntura/web/src/layouts/Layout.astro`, justo antes de `</body>` (un solo archivo cubre las 5 páginas):
```html
<script>
  // Auto-resize: avisa la altura al contenedor (Wix) cuando está dentro de un iframe
  (function () {
    if (window.self === window.top) return;      // sólo si está embebido
    function postHeight() {
      window.parent.postMessage(
        { type: 'cigob-informe-height', height: document.documentElement.scrollHeight },
        '*'
      );
    }
    window.addEventListener('load', postHeight);
    window.addEventListener('resize', postHeight);
    if (window.ResizeObserver) new ResizeObserver(postHeight).observe(document.body);
    setTimeout(postHeight, 300);
    setTimeout(postHeight, 1200);                 // reintento tras fuentes/charts
  })();
</script>
```
Esto entra en el build y se deploya con el flujo diario normal (no lo rompe).

**b) En Wix** — pegar este snippet de Velo en la página "Informe" (asumiendo que el embed tiene id `#html1`; ajustar el id al real):
```js
$w.onReady(function () {
  $w('#html1').onMessage((event) => {
    const d = event.data;
    if (d && d.type === 'cigob-informe-height' && d.height) {
      $w('#html1').height = Math.ceil(d.height);
    }
  });
});
```

### Fase 3 — Armonización visual fina (opcional, bajo esfuerzo)
- Igualar fondo crema↔blanco y acentos teal↔celeste si se nota el salto.
- Asegurar que la transición header-CiGob → informe se lea como una sola pieza.

---

## Riesgos / cosas a chequear al implementar
- **Plan Wix:** confirmar que el embed/iframe está disponible en el plan actual (debería, por dominio propio). Si fuese un plan sin custom code, el iframe básico igual anda; sólo Velo requeriría plan con Velo habilitado.
- **Id del elemento en Velo:** ajustar `#html1` al id real que Wix le asigne al embed.
- **Rutas internas del informe:** son absolutas (`/biblitotecario-ai/informe/...`); funcionan en el iframe. Si algún día se mueve a `informe.cigob.org`, revisar el base path del build de Astro.
- **Altura en cambios de sección:** el poster se re-dispara en `load`/`resize`/`ResizeObserver`; validar que al navegar entre cinturones la altura se ajuste bien.

---

## Próximos pasos sugeridos
1. **Ahora:** abrir `test-embed-wix.html` y validar encaje + navegación + mobile.
2. **Esta semana:** redactar/enviar el pedido-boludez de Fase 1 a quien tenga Wix.
3. **Cuando haya acceso:** sumar el height-poster (Fase 2a) y el Velo (Fase 2b).
4. **Si hace falta:** armonización visual fina (Fase 3).
