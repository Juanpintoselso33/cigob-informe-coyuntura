# ADR-0005 — Reservas: netas "a secas" calculadas de la planilla SDDS + Tesoro + Bopreal

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-06-26 |
| **Ámbito** | Dimensión Capacidad de financiamiento · indicador `reservas_bcra` |
| **Commit** | `3f17e5a` (final; saga: `9204e86` → `1b7d1b9` → `59af7db` → `6e28f83` → `3f17e5a`) |

## Contexto

La Paramétrica original usaba las **reservas brutas** (~48k → banda 70). El
documento `260626 aportes` indica usar las **netas**, con una escala propia. Pero
"reservas netas" **no es un número único**: es un espectro según qué pasivos se
descuentan. El número que mira el mercado día a día es el de "libre disponibilidad"
o **"a secas"** (Machado/OPEN, Ieria): brutas menos los pasivos en moneda
extranjera, **excluyendo** los depósitos del Tesoro y los vencimientos de Bopreal a
12 meses (porque no son pasivos del BCRA para defender el tipo de cambio).

El desafío (ver ADR-0001): calcularlo **de datos oficiales, sin hardcodear**. El
BCRA no expone las netas ni sus componentes en la API de Monetarias.

## Decisión

```
netas a secas = SDDS estricto  +  depósitos del Tesoro  +  Bopreal 12m
```

Los tres términos salen de datos oficiales, **ninguno hardcodeado**:

| Término | Fuente | Cómo se obtiene |
|---|---|---|
| **SDDS estricto** | Planilla SDDS/NEDD del BCRA (`temp{MM}{YY}.pdf`, mensual, USD) | `Activos de reserva (I.A) − drenajes Sección II` (II.1 préstamos/dep + II.2 forwards/swaps + II.3 repos), parseado con `pdfplumber` |
| **Dep. del Tesoro** | Balance Consolidado del BCRA (`balbcrhis.xls`) | col "Dep. gobierno en ME" / TC / 1000 |
| **Bopreal 12m** | Planilla SDDS, **bucket de vencimiento "3m-1año" de la Sección II.1** | 4º número de la línea II.1 |

El SDDS descuenta Tesoro y Bopreal como pasivos; el mercado los **suma de vuelta**
porque no son pasivos del BCRA para defender el TC. Implementación:
`macro._reservas_netas_sdds()` + `macro._tesoro_deposits_usd()` + `macro.fetch_reservas_netas()`.

Escala (BANDAS_ITCM `reservas_bcra`, en M USD de **netas**):
`>20k→100 · 15–20k→85 · 10–15k→70 · 5–10k→50 · 0–5k→30 · neg→10`.

### Verificación empírica (clave)

Se extrajeron 3 meses de la planilla y se compararon contra el número de mercado
publicado. La fórmula reproduce **la misma banda en los tres meses**:

| Fecha | Nuestra fórmula | Mercado (Machado) | Banda |
|---|---|---|---|
| 31/03/26 | −1.719 | −2.500 | 10 (ambos) |
| 30/04/26 | +590 | +1.869 | 30 (ambos) |
| 31/05/26 | +4.122 | +3.807 | 30 (ambos) |

Prueba de que el bucket "3m-1año" **es** el Bopreal: valía ~130 en marzo y **saltó
a ~2.670 en abril**, justo cuando la Serie 1B del Bopreal entró a la ventana de 12
meses (30/04/2026).

## Opciones consideradas (incluye callejones sin salida — NO re-investigar)

- **Reservas brutas** (original). Rechazada: el doc pide netas; las brutas ocultan la deuda en ME.
- **Brutas (API) − pasivos de un config a mano.** Rechazada (ADR-0001): pasivos hardcodeados.
- **Balance Consolidado del BCRA (`balbcrhis.xls`) como única fuente.** Daba +6.376
  (banda 50), ~2,5k por encima del consenso. Descartada como número de scoring: el
  balance está en pesos, agrupa swap+repos+OOII en "y otros" y define los encajes
  distinto al mercado. (Se conserva para el término del Tesoro: col "Dep. gobierno en ME".)
- **Calibración con constante −2.500** para alinear el balance al consenso.
  Rechazada (ADR-0001): constante hardcodeada.
- **Exclusiones (Bopreal+Tesoro) cargadas a mano en un config.** Rechazada (ADR-0001).
- **`din2_ser.txt` (series diarias de reservas y pasivos).** Descartada: son pasivos
  **monetarios** (base, letras, pases) en pesos, no los pasivos en ME para netas.
- **Scrapear el Bopreal del Boletín Oficial.** Resultó innecesario: el Bopreal a 12m
  ya está en la planilla SDDS (bucket de vencimiento 3m-1año de la Sección II.1).
- **SDDS estricto (sin sumar Tesoro/Bopreal).** Da −1.605 (banda 10): correcto y
  100% automático, pero es la definición estricta/FMI-ish, no el número de mercado.
- **SDDS estricto + Tesoro + Bopreal (todo de datos).** Elegida: reproduce la banda
  del mercado y cumple ADR-0001.

## Consecuencias

- Dos fuentes oficiales (planilla SDDS en PDF + balance en XLS), cada una con su
  fallback: el Tesoro se omite si el balance no baja; el SDDS cae a
  `drenajes_seccion_ii` del config (`data/macro/reservas_netas_pasivos.json`).
  Validación anti-silencio: brutas SDDS vs API var 1 ±15%; netas en rango plausible.
- Requiere `pdfplumber` y `xlrd` (ya en `requirements.txt`).
- **Diferencia con otros cálculos** (para tener presente): vs Machado/Ieria
  (~+3,8–3,9k) la diferencia es de ~200–300M y se debe sobre todo a la **fecha**
  (el nuestro es a cierre de mes; ellos lo mueven a diario) y a matices de
  definición (encajes, puts del Bopreal). Las brechas grandes vs PPI "exigente"
  (−587) o el FMI (−6k a −12k) son **metodológicas**: esos restan más (no suman
  Tesoro/Bopreal, o aplican la vara del FMI con valuación fija y desembolsos del
  Fondo). Las tres son correctas; miden cosas distintas. Elegimos "a secas" porque
  es la referencia del mercado y es calculable de datos.
- Hoy (31/05/26): −1.605 + 3.058 + 2.670 = **+4.122 → banda 30**.
