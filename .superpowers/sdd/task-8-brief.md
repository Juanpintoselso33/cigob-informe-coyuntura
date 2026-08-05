### Task 8: ADR-0036

**Files:**
- Create: `docs/adr/0036-itcp-parametrica-politica.md`

- [ ] **Step 1: Escribir el ADR**

Seguir el formato de ADR-0013 (tabla Estado/Fecha/Ámbito, Contexto, Decisión,
Operacionalizaciones, Opciones descartadas, Consecuencias). Contenido mínimo
a incluir (ya redactado en el spec, `docs/superpowers/specs/2026-07-07-itcp-cinturon-politica-design.md` — usar como fuente):

- Contexto: cinturón política se puntuaba con promedio simple; 5 dimensiones
  ya descriptas en `docs/cinturon_politica.md` pero nunca pesadas.
- Decisión: pesos 30/25/20/15/10, sin doc CIGOB de respaldo (a diferencia de
  ITCM/ITCG/ITVC) — decisión editorial explícita justificada en el propio
  marco del proyecto ("capacidad de gobernar, NO popularidad").
- `cohesion_bloque` redefinido de "% alineado con posición oficial" a "índice
  de Rice" (cohesión interna) — la posición oficial no es un dato disponible.
- 3 indicadores nuevos y su alcance honesto: `cohesion_bloque_senado`
  (complementario, no reemplaza a Diputados), `adhesion_reformas_provincial`
  (adhesión fiscal puntual, no proxy de `gobernadores_alineamiento`),
  `protestas_caba` (reutilizado de gestión, lectura distinta: condición de
  gobernabilidad, no juicio sobre legitimidad de protestar).
- Bandas provisionales a recalibrar: las 4 nuevas/recalibradas.
- Opciones descartadas: compactar `poder_legislativo` en un compuesto (sin
  doc que lo exija, se mantiene plano); usar Senado o Presupuesto Abierto
  como proxy directo de `gobernadores_alineamiento` (construct-invalid,
  documentado en `manuales.json._meta`).

- [ ] **Step 2: Commit**

```bash
git add docs/adr/0036-itcp-parametrica-politica.md
git commit -m "docs(adr): ADR-0036 — paramétrica ITCP del cinturón política"
```

---

