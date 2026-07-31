---
madr: 4
id: '0148'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'politica'
indicadores: [sector_privado]
corrige: ['0145']
ambito: 'cinturón político (ITCP) · dimensión `sector_privado`'
---

# ADR-0148 — Apoyo empresario: con UIA, la métrica funciona

- **Reabre y corrige**: ADR-0145 (la versión sólo-AEA, descartada)
- **Relacionados**: ADR-0131 (protocolo), ADR-0139 (AEA como fuente), ADR-0088

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

1. **El indicador queda habilitado para construirse**, y ADR-0145 queda corregido
   en su conclusión —no en su método, que fue el correcto: se descartó por los
   números y el camino de salida quedó escrito.
2. **NO se incorpora todavía al ITCP.** Falta la **segunda pasada de codificación
   con otro codificador** y kappa ≥ 0,70, y ahora es **más** necesaria que antes:
   mientras la métrica no servía, el kappa era un trámite sobre algo descartado;
   ahora la codificación incide sobre un número que se publicaría.
3. La codificación de UIA de esta pasada se apoyó mucho en títulos. Varios casos
   son discutibles —«Retorno de la política industrial» como crítica, o el
   comunicado del G6 sobre el marco laboral como dirigido al Congreso— y son
   justamente los que el segundo codificador tiene que mirar.

### Consecuencias

103 comunicados codificados con las **mismas reglas**, sin tocarlas
(`apoyo_empresario_reglas.json`, escritas antes de ver los datos de AEA y
aplicadas tal cual a UIA):

| | sólo AEA (ADR-0145) | AEA + UIA |
|---|---|---|
| computables desde dic-2023 | 2 | **16** |
| meses con la ventana vacía | 5 de 32 | **0** |
| meses con `n = 1` | **20 de 32** | **0** |
| `n` por ventana | casi siempre 1 | **2 a 8, promedio 5** |

Y la serie **tiene forma**: −1,00 en dic-2023 · −0,75 en feb-2025 · **+0,33 en
feb-2026** · −0,71 hoy. Ya no es el eco del último comunicado.

## Más información

### Qué cambió

ADR-0145 descartó el indicador con un diagnóstico preciso: la fuente era buena,
las reglas aguantaron, la codificación funcionó, **falló la frecuencia del
fenómeno** — AEA se pronunció sobre el Ejecutivo nacional 13 veces en seis años.
Y dejó escrito el único camino: **sumar cámaras**.

Se sumó una. Alcanzó.

### La fuente que faltaba

**UIA publica en `uia.org.ar/prensa/{id}/`, con IDs secuenciales y páginas
servidas sin JavaScript** — fecha y título en el HTML. El listado sí es una app
con JS, pero las notas individuales no, así que el corpus se recorre por ID.

Ojo con la sección equivocada: **UIA/Noticias está dominado por informes del
CEU** (indicadores laborales, boletines estadísticos), el mismo patrón que hundió
a ADEBA. Los comunicados de postura están en **UIA/Prensa**, que es otra sección.

Barrido del rango de IDs: **57 comunicados desde dic-2023**, contra 46 de AEA en
seis años.

### El hallazgo que le da sentido

**La industria critica y el gran empresariado apoya.**

UIA se pronuncia contra los aumentos de tarifas, la presión tributaria, la
competencia importada y el cierre de Fate. AEA celebra el acuerdo con el FMI y el
Pacto de Mayo. Son dos electorados distintos dentro del mismo sector, y el
indicador los captura en vez de promediarlos a ciegas.

Eso también explica por qué el saldo agregado es negativo casi todo el período
pese a que el relato dominante es de apoyo empresario al Gobierno: **AEA es más
citable, UIA es más frecuente.**

### Las ocho cámaras quedan evaluadas: AEA + UIA es el techo

Cerrado el 27-jul. De las ocho del relevamiento original, **dos sirven, cuatro no
publican postura y dos no son relevables**:

| | veredicto |
|---|---|
| **AEA** · **UIA** | **sirven** — son el corpus |
| ADEBA | el feed son 21 «Síntesis normativa»: boletín regulatorio diario |
| CAC | agenda institucional (visitas, webinars, paritarias) |
| CAME | servicios al socio (escalas de convenio, rondas de negocios) |
| CAMARCO | sin sección de prensa ni comunicados; `/noticias/` son 13 piezas institucionales y de servicios |
| COPAL | **feed muerto desde 2022**, con tres entradas tituladas «Prueba» |
| **SRA** | **`robots.txt`: «Bloqueo completo para bots — Disallow: /»** |
| **AmCham** | «AmCham Connect»: plataforma de socios detrás de login |

Las dos últimas merecen distinguirse del resto, porque **no es que no se pueda:
es que no corresponde.**

- **SRA** declara en su `robots.txt` que ningún bot debe recorrer el sitio. Es la
  política del operador, no una barrera técnica, y se respeta. Si alguna vez
  hiciera falta, la vía es pedírselo a la entidad.
- **AmCham** movió su dominio: `amchamar.com.ar` está muerto y `amcham.com.ar` es
  hoy una SPA de networking para socios cuyo JS sólo expone
  `apiv2.amcham.com.ar/api/cognito/`. No hay prensa pública, y el contenido de
  socios está detrás de autenticación — ahí no se entra. No resuelve ningún
  dominio institucional alternativo.

**Conclusión: el corpus AEA + UIA es el máximo alcanzable sin pedirle datos a una
entidad.** Y alcanza: la métrica funciona con `n` de 2 a 8 por ventana.

### Nota sobre el costo, que ADR-0136 sobreestimó

ADR-0136 rechazó el indicador en parte por «trabajo permanente de dos personas».
Con 103 comunicados en seis años y ~20 por año entre las dos cámaras, la
codificación mensual es de unas dos piezas por mes. Sigue siendo trabajo humano
recurrente, pero no del orden que se declaró.
