---
madr: 4
id: '0068'
estado: 'aceptado'
fecha: 2026-07-15
cinturon: 'gestion'
indicadores: [fal_modernizacion_laboral]
relacionado: ['0013', '0062']
modificado_por: ['0098']
ambito: 'Cinturón gestión · ITCG · `fal_modernizacion_laboral`'
---

# ADR-0068 — fal_modernizacion_laboral: la consulta al BO contaba el régimen de la construcción — se re-apunta al FAL de la Ley 27.802

## Contexto y planteo del problema

Auditoría de la serie pedida por el usuario ("investiguemos los valores de la
serie / velocidad de crecimiento"). La serie publicada crecía monótona de 0,1
(dic-2023) a 2,9 (jun-2026) y era el mayor lastre individual del ITCG
(77,7 sin el indicador vs 73,8 con él). Tres hallazgos:

### 1. La consulta medía ruido, no reforma

La cobertura contaba menciones de **"fondo de cese laboral"** en la Primera
Sección del BO desde dic-2023 (`todasLasPalabras`: matchea las tres palabras
en cualquier parte del documento — el DNU 70/2023 entra por "Fondo
Monetario… cese… laboral"). Pero ese nombre designa al régimen de la
**industria de la construcción (Estatuto de la Ley 22.250)**: el Capítulo V se
llama "Fondo de Cese Laboral" desde la Ley 25.371 (2001), que renombró el
"Fondo de Desempleo" original de 1980 — 20+ años de ruido en el BO. Conteo
pre-reforma de la misma frase: 2021 = 10 · 2022 = 6 · 2023 pre-Ley Bases = 4
(~7-8/año).
Post-Ley Bases: 21 menciones en 31 meses ≈ **8,1/año — indistinguible de la
línea de base**. El "crecimiento" de la serie era la acumulación del ruido
administrativo de siempre; su velocidad, la tasa de ese ruido.

### 2. El instrumento de la reforma cambió de nombre

La **Ley 27.802 (Modernización Laboral; sancionada 27-feb-2026, promulgada
05-mar, publicada BO 06-mar-2026)** creó el instrumento como **"Fondo de
Asistencia Laboral" (FAL)** en su Título II (art. 58), reglamentado por el
**Decreto 408/2026 (BO 01-jun-2026)**. La consulta vieja no podía verlo.
Menciones de la frase nueva: 17 desde dic-2023, pero solo **3 desde la
publicación de la ley** (mar = ley, may, jun = reglamentación) — las 14
previas son el mismo ruido de palabras sueltas (verificado mes a mes: 1
mención espuria en ene-2026). El corte de fecha en la sanción limpia la
señal sin heurísticas.

**El régimen entra en vigencia el 1-nov-2026** (art. 27 del Decreto 408/2026
prorrogó el arranque originalmente previsto para el 1-jun-2026). La
recaudación se canaliza por ARCA dentro de la CUSS; los fondos se instrumentan
como FCI o fideicomisos supervisados por la CNV (art. 5 del decreto). Es
decir: la adopción financiera (aportes, altas de fondos en CNV) es
**legalmente imposible antes de noviembre de 2026** — el 0 de la CNV no es
solo "temprano", está impedido por la propia norma hasta esa fecha.

### 3. CNV: cero bajo cualquier denominación (dato duro)

Sobre 1.656 fondos del registro CNV: 0 con "CESE", 0 con "ASISTENCIA
LABORAL". La materialización financiera del régimen es exactamente cero
(coherente con el diferimiento a nov-2026: los fondos aún no pueden operar).

### Verificación externa (chequeo pedido por el usuario)

Los hechos posteriores al corte de conocimiento se confirmaron contra fuente
independiente, no solo contra el BO consultado por el colector:

| Hecho | Fuente | Resultado |
|---|---|---|
| Ley 27.802 = "Modernización Laboral", BO 06-mar-2026 | InfoLeg (norma id 423680), Biblioteca AFIP, BO 35865 | ✓ |
| Título II crea el FAL (art. 58); aporte 1% grandes / 2,5% MiPyMEs (art. 60) | Texto BO de la ley; La Nación, Perfil, TN | ✓ |
| Decreto 408/2026 (BO 01-jun-2026) reglamenta el FAL vía FCI/fideicomisos CNV | BO aviso 342622; Microjuris; 4 estudios jurídicos | ✓ |
| Entrada en vigencia prorrogada al 01-nov-2026 (art. 27) | Decreto 408/2026 art. 27; La Nación; Perfil | ✓ |
| "Fondo de Cese Laboral" = régimen de la construcción (Ley 22.250, nombre desde Ley 25.371/2001) | InfoLeg Ley 22.250 texto actualizado | ✓ |

Correcciones que introdujo el chequeo respecto del borrador inicial: (a) la
vigencia es nov-2026, no jun-2026 (el "reglamentado hace seis semanas" era
impreciso — la adopción financiera está diferida por norma); (b) el nombre
"Fondo de Cese Laboral" de la construcción rige desde 2001, no 1980 (el
régimen es de 1980; el argumento de contaminación se sostiene igual).

## Opciones consideradas

- **Re-apuntar la cobertura al régimen vigente**: menciones del BO de «fondo de asistencia laboral» desde el 01-mar-2026 — elegida.
- **La consulta anterior, «fondo de cese laboral»** — descartada: contaba el régimen homónimo de la construcción, que es ruido de fondo.
- **Mantener el pleno autorreferencial** (21 menciones ≡ una estimación manual) — descartado: se recalibra contra un ancla externa, por el criterio de ADR-0059.

## Decisión

1. **Cobertura re-apuntada al régimen vigente**: menciones BO de
   `"fondo de asistencia laboral"` **desde el 01-mar-2026**
   (`FAL_BO_TEXTO`/`FAL_BO_DESDE` en `gestion.py`).
2. **Pleno recalibrado con ancla externa** (criterio de ADR-0059): se
   mantiene 420 menciones pero deja de ser autorreferencial (antes: 21
   menciones ≡ estimación manual ~5%). Ahora: el MTEySS homologa **~2.000
   convenios y acuerdos/año** (serie 2008-2022, informes de negociación
   colectiva; pico 3.057 en 2022) y una cláusula nueva demostró poder
   difundirse hasta el **42% de las homologaciones anuales** (cláusulas de
   crisis 2020-21). 420 menciones acumuladas ≈ un año donde ~1 de cada 5
   homologaciones incorpora el FAL. Provisional hasta que exista serie
   MTEySS de homologaciones con FAL.
3. **Detector CNV ampliado**: `_cnv_fondos_cese()` busca "CESE" (RG
   1071/2025, régimen Ley Bases) **o** "ASISTENCIA LABORAL" (Ley 27.802).
4. **Serie reconstruida**: 0,0 desde dic-2023 hasta feb-2026 (el régimen
   medible no existía y la adopción financiera fue siempre 0) y menciones
   acumuladas desde mar-2026 en adelante (`fetch_fal_serie`). El histórico
   fallback (`data/historico/indicadores.json`) y el respaldo manual
   (`manuales.json`) se corrigen en consecuencia.
5. **Bandas ITCG sin cambios**: el valor cae de 2,9 a ~0,4 pero ambos están
   en la banda inferior (≤5 → 10); el puntaje del indicador apenas se mueve
   y el diseño de anclas (40-60 = adopción masiva) sigue vigente.

### Consecuencias

- El valor publicado pasa de 2,9 a **0,4** y la serie deja de mostrar un
  crecimiento que no existió. La lectura honesta queda expuesta: régimen
  cuya adopción financiera recién puede arrancar el 1-nov-2026 — el valor
  cercano a cero es el dato, no una falla (mismo principio que ADR-0061:
  no recalibrar contra el rango propio para "subir" un indicador que mide
  bien un fenómeno que todavía no ocurrió). Hasta noviembre el indicador
  mide el andamiaje normativo (ley + decreto + normas complementarias de
  ARCA/CNV/Secretaría de Trabajo); a partir de ahí captará adopción real.
- Impacto ITCG mínimo (~±0,1: ambos valores puntúan en el piso de la banda),
  pero la card, sus componentes y la serie ahora cuentan la historia real.
- Cuando el FAL empiece a aparecer en homologaciones, la serie lo captará
  con la frase correcta y sin línea de base contaminada; los fondos que se
  registren en CNV entrarán bajo cualquiera de las dos denominaciones.
- Queda pendiente (mejor fuente): serie del MTEySS de convenios homologados
  con cláusula FAL — reemplazaría al proxy de menciones y permitiría anclar
  el pleno en cobertura real de trabajadores.

## Más información

### Precedentes directos

ADR-0013/0023 (diseño del compuesto y separación de litigiosidad); método de auditoría de datos crudos de ADR-0062/0065/0066
