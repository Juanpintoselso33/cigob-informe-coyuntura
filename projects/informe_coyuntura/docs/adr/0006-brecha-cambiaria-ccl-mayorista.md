# ADR-0006 — La brecha cambiaria (cepo_mulc) se mide CCL/mayorista, no CCL/oficial-minorista

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-06-26 |
| **Ámbito** | Cinturón Gestión · indicador `cepo_mulc` |
| **Commit** | `8dd8bc0` |

## Contexto

El indicador `cepo_mulc` (cinturón de gestión) mide la **brecha cambiaria** como
proxy del cepo corporativo. Estaba calculado como `CCL / oficial`, donde "oficial"
era el dólar **minorista** (dolarapi `casa=oficial`, el del BNA). Ese tipo de
cambio minorista ya incluye el spread del banco, así que **subestima** la brecha.

## Decisión

La brecha se mide **CCL / mayorista** (`dolarapi casa=mayorista`), que es la
referencia correcta: el dólar mayorista (Comunicación A 3500 del BCRA) es la tasa
sobre la que se calcula la brecha cambiaria estándar, sin el spread minorista.

```
brecha = (CCL − mayorista) / mayorista × 100
```

Hoy: CCL/mayorista = 4,4% (vs CCL/oficial-minorista = 3,1%, que subestimaba).
Implementación: `gestion.fetch_cepo_mulc()`.

## Opciones consideradas

- **CCL / oficial minorista** (original). Rechazada: el minorista trae el spread del
  banco; subestima la brecha.
- **CCL / mayorista.** Elegida: referencia A3500 del BCRA, la estándar de mercado.

## Consecuencias

- La brecha medida sube levemente (refleja mejor la realidad) → avance del indicador
  baja un poco → algo más de tensión en el cinturón de gestión.
- Descripción de la web actualizada (`web/src/lib/descripciones.ts`).
