---
madr: 4
id: '0006'
estado: 'aceptado'
fecha: 2026-06-26
cinturon: 'gestion'
indicadores: [cepo_mulc]
relacionado: ['0055']
ambito: 'Cinturón Gestión · indicador `cepo_mulc`'
commit: '`8dd8bc0`'
---

# ADR-0006 — La brecha cambiaria (cepo_mulc) se mide CCL/mayorista, no CCL/oficial-minorista

## Contexto y planteo del problema

El indicador `cepo_mulc` (cinturón de gestión) mide la **brecha cambiaria** como
proxy del cepo corporativo. Estaba calculado como `CCL / oficial`, donde "oficial"
era el dólar **minorista** (dolarapi `casa=oficial`, el del BNA). Ese tipo de
cambio minorista ya incluye el spread del banco, así que **subestima** la brecha.

## Opciones consideradas

- **CCL / oficial minorista** (original). Rechazada: el minorista trae el spread del
  banco; subestima la brecha.
- **CCL / mayorista.** Elegida: referencia A3500 del BCRA, la estándar de mercado.

## Decisión

La brecha se mide **CCL / mayorista** (`dolarapi casa=mayorista`), que es la
referencia correcta: el dólar mayorista (Comunicación A 3500 del BCRA) es la tasa
sobre la que se calcula la brecha cambiaria estándar, sin el spread minorista.

```
brecha = (CCL − mayorista) / mayorista × 100
```

Hoy: CCL/mayorista = 4,4% (vs CCL/oficial-minorista = 3,1%, que subestimaba).
Implementación: `gestion.fetch_cepo_mulc()`.

### Consecuencias

- La brecha medida sube levemente (refleja mejor la realidad) → avance del indicador
  baja un poco → algo más de tensión en el cinturón de gestión.
- Descripción de la web actualizada (`web/src/lib/descripciones.ts`).
