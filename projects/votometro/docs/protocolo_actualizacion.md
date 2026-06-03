# Protocolo de actualización — Votómetro Argentina 2027
**Fundación CIGOB · Uso interno**
Versión: marzo 2026

---

## Introducción

El Votómetro es un archivo HTML único (`votometro.html`) que vive en la carpeta `web/` del proyecto. Todos los datos de encuestas están escritos directamente dentro del archivo — no hay base de datos ni servidor. Para actualizarlo hay que editar ese archivo con un editor de texto, agregar las encuestas nuevas, y subir el archivo modificado.

Este documento explica paso a paso cómo hacerlo sin conocimientos técnicos avanzados.

---

## 1. Checklist para agregar una encuesta nueva

### Antes de empezar

- [ ] Tenés el archivo abierto en un editor de texto (Notepad++, VS Code, o incluso el Bloc de notas)
- [ ] La encuesta tiene fecha, consultora, porcentajes por partido y tamaño de muestra
- [ ] Verificaste que la fuente es confiable (ver criterios de calidad en sección 2)

### Dónde está el archivo

```
projects/votometro/web/votometro.html      (relativo a la raíz del repo)
```

### Cómo encontrar el lugar exacto donde agregar la encuesta

1. Abrí el archivo en tu editor de texto
2. Usá la función de búsqueda (Ctrl+F) y buscá: `encuestasRaw`
3. Vas a encontrar el array que empieza en la línea ~1104 con `const encuestasRaw = [`
4. Scrolleá hasta el **final** del array — buscá el último objeto antes del `];` de cierre
5. El último dato actualmente es de **marzo 2026** — insertá el nuevo objeto **antes** del `];`

### Formato exacto de un objeto de encuesta

Cada encuesta es un objeto JavaScript con este formato:

```javascript
{ fecha:'AAAA-MM-DD', consultora:'Nombre Consultora', LLA:00.0, PJ:00.0, PRO:00.0, PU:00.0, FIT:00.0, OTROS:00.0, muestra:0000, tipo:'espacio', calidad:'A' },
```

**Ejemplo real** (encuesta de Trends, enero 2026):
```javascript
{ fecha:'2026-01-16', consultora:'Trends', LLA:43.0, PJ:32.0, PRO:4.0, PU:4.0, FIT:3.0, OTROS:14.0, muestra:2000, tipo:'espacio', calidad:'A' },
```

### Campos requeridos — descripción de cada uno

| Campo | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `fecha` | texto `'AAAA-MM-DD'` | Fecha de publicación o de campo (la más reciente si hay rango) | `'2026-04-15'` |
| `consultora` | texto | Nombre exacto de la consultora (ver tabla sección 3) | `'Giacobbe'` |
| `LLA` | número | % intención de voto LLA / Milei | `42.5` |
| `PJ` | número | % PJ / Kirchnerismo / Frente Patria | `30.0` |
| `PRO` | número | % PRO / Juntos | `6.5` |
| `PU` | número | % Provincias Unidas / UCR otros | `4.5` |
| `FIT` | número | % FIT-U / izquierda | `4.0` |
| `OTROS` | número | % resto (incluye ns/nc si la encuesta lo reporta así) | `12.5` |
| `muestra` | número entero | Cantidad de casos encuestados | `1800` |
| `tipo` | texto | `'espacio'` = intención por partido / `'candidato'` = por nombre Milei / `'real'` = resultado oficial | `'espacio'` |
| `calidad` | texto | `'A'`, `'B'` o `'C'` (ver criterios sección 2) | `'A'` |

### Sobre la suma de los porcentajes

Los valores **no necesitan sumar exactamente 100%**. Es normal y esperado que no sumen 100 cuando:
- La encuesta reporta ns/nc (no sabe / no contesta) como categoría separada
- Hay partidos regionales o candidatos menores que no entran en los campos estándar
- La encuesta es de tipo `candidato` (hay más indecisos declarados)

Lo que sí importa: que los valores reflejen fielmente lo que publicó la consultora, sin redistribuir manualmente los porcentajes.

### Actualizar la fecha de última actualización

Después de agregar la encuesta, buscá en el archivo la línea:

```javascript
const ULTIMA_ACTUALIZACION = new Date('2026-03-01');
```

Cambiá la fecha por la fecha del día en que estás haciendo la actualización:

```javascript
const ULTIMA_ACTUALIZACION = new Date('2026-04-15'); // ← nueva fecha
```

Esto actualiza automáticamente el pie del Votómetro que dice "Actualizado: [fecha]".

---

## 2. Criterios de calidad A / B / C

La calidad de una encuesta determina cuánto peso tiene en el modelo. No es un juicio subjetivo — hay criterios fijos.

### Calidad A — Fuente primaria verificada

**Requisitos:**
- Publicada en un medio de referencia (Infobae, La Nación, Clarín, Perfil, Cronista, Bloomberg Línea)
- Muestra mayor a 1.000 casos **Y** metodología probabilística (CATI o presencial)
- Se puede verificar la fuente original

**Ejemplos de encuestas A:**
- Trends en Clarín (n=2000, CATI)
- CB Consultora en La Nación (n=1668, CATI)
- Giacobbe en Página12 (n=2500, presencial+CATI)
- Resultado electoral oficial (siempre A)

### Calidad B — Fuente secundaria con referencia

**Requisitos:**
- Publicada con referencia identificable pero en medios de segundo nivel, o
- Metodología verificable pero muestra entre 500 y 1.000 casos, o
- Encuesta de calidad A pero sin publicación formal (estimación informada)

**Ejemplos de encuestas B:**
- Giacobbe estimado por tendencias de imagen sin publicación directa
- Management & Fit en medios especializados
- QSocial en portales con buena cobertura pero metodología mixta

### Calidad C — Reconstruida o sin fuente primaria verificable

**Requisitos / situaciones:**
- Reconstruida desde indicadores de imagen o aprobación (no es encuesta de intención directa)
- Publicación sin metodología clara
- Datos de 2023-2024 cuando el Votómetro presidencial 2027 no era el tema principal de las encuestas

**Nota importante:** Calidad C no significa que el dato sea incorrecto — significa que tiene mayor incertidumbre. El modelo lo usa con menor peso automáticamente.

### Tabla resumen

| Criterio | Calidad A | Calidad B | Calidad C |
|---|---|---|---|
| Fuente | Medio de referencia nacional | Medio identificable | Sin publicación directa |
| Muestra | > 1.000 casos | 500–1.000 casos | < 500 o no informada |
| Metodología | Probabilística (CATI/presencial) | CATI o mixta documentada | Online, panel, redes o no especificada |
| Verificación | Se puede consultar el original | Hay referencia citada | Estimación o reconstrucción |

---

## 3. Tabla de consultoras con clasificación de sesgo y calidad

Esta tabla proviene directamente del HTML del Votómetro. Los valores numéricos son los factores de ponderación que usa el modelo.

### Cómo leer los valores

- **Factor CALIDAD**: mide el track record histórico y rigor metodológico. 1.15 = muy precisa; 0.55 = históricamente muy inexacta.
- **Factor SESGO**: mide si la consultora tiende a sobreestimar o subestimar a LLA. 1.00 = sin sesgo documentado; < 1.00 = subestima LLA; > 1.00 = sobreestima LLA.
- **Factor MEDIO**: mide la independencia del medio que publica/financia. 1.00 = independiente.
- **Factor METODOLOGÍA**: mide el rigor del método de recolección. 1.15 = presencial estratificado; 0.85 = social media / panel sin marco muestral claro.

### Tabla de consultoras activas

| Consultora | Calidad | Sesgo | Medio | Metodología | Nota principal |
|---|---|---|---|---|---|
| Poliarquía | 1.15 | 1.00 | 1.00 | 1.10 | Referencia neutra; CATI aleatorio estratificado |
| CB Consultora | 1.10 | 1.02 | 1.00 | 1.05 | CATI+presencial; calibrada en 2025 |
| CB Global Data | 1.10 | 1.02 | 1.00 | 1.05 | Misma firma que CB; encuestas de candidato |
| Zuban Córdoba | 1.05 | 1.00 | 1.00 | 1.15 | Mayor rigor metodológico documentado |
| Opina Argentina | 1.00 | 1.00 | 1.00 | 0.95 | CATI + online |
| Giacobbe | 0.92 | 0.88 | 1.00 | 1.05 | Subestima LLA históricamente (-11pp PASO 2023, -5pp leg. 2025) |
| DC Consultores | 0.92 | 0.93 | 0.88 | 0.85 | Más precisa en leg. 2025; revaluación al alza |
| Circuitos | 0.90 | 1.03 | 0.98 | 1.00 | IVR + CATI; buena muestra |
| Management & Fit | 0.90 | 0.92 | 0.98 | 1.00 | Error -13pp PASO 2023; casi exacta en leg. 2025 |
| Atlas Intel | 0.90 | 0.95 | 0.98 | 0.90 | Panel online grande; sesgos propios |
| Trends | 0.95 | 0.95 | 0.95 | 0.90 | Online + CATI; subestimó LLA en 2025 |
| Opinaia | 0.95 | 1.00 | 1.00 | 0.90 | Panel online; calibrada principalmente en CABA |
| Proyección | 0.88 | 0.90 | 0.92 | 0.90 | Orientación bonaerense; medios K |
| Synopsis | 0.85 | 0.95 | 0.95 | 0.90 | Menor track record |
| Escenarios | 0.85 | 0.97 | 0.97 | 0.90 | Metodología no totalmente pública |
| Pulso Research | 0.85 | 0.98 | 0.97 | 0.90 | Relativamente nueva |
| QSocial | 0.85 | 0.82 | 0.88 | 0.88 | Fuerte sesgo pro-LLA; gran error histórico |
| Isasi Burdman | 0.55 | 0.68 | 0.88 | 0.85 | Error 24pp en margen PBA leg. 2025; sesgo pro-oficialismo extremo |

### Qué hacer con una consultora nueva (no está en la tabla)

Si aparece una consultora que no figura en la tabla, el modelo le asigna valores por defecto:
- Calidad: 0.80
- Sesgo: 1.00
- Medio: 1.00
- Metodología: 0.90

Antes de publicar, consultá con Redlines si conviene agregarla explícitamente a los diccionarios del HTML con valores más precisos. Esto requiere editar las secciones `CALIDAD`, `SESGO`, `MEDIO` y `METODOLOGIA` en el archivo (líneas ~1006–1085).

---

## 4. Frecuencia recomendada de actualización

### Rutina normal

- **Frecuencia base**: semanal, si hay encuestas nuevas publicadas en la semana
- **Criterio mínimo**: solo agregar encuestas que tengan publicación verificable o referencia identificable
- No es obligatorio agregar todas las encuestas que circulan — la calidad del dato importa más que la cantidad

### Antes de eventos clave (obligatorio)

Actualizar siempre antes de:
- PASO (si se realizan) — idealmente 48 horas antes
- Elecciones generales — idealmente 48 horas antes
- Reuniones institucionales de CIGOB donde se presenta el Votómetro
- Entrevistas o apariciones públicas donde se cite el Votómetro

### Si una consultora publica dos encuestas en la misma semana

Regla general: **incluir ambas** si tienen diferente metodología, universo o tipo (espacio vs candidato). Si son prácticamente idénticas (misma metodología, misma semana, mismo universo), incluir solo la más reciente o la de mayor muestra, y agregar una nota en el comentario del código.

Ejemplo de nota en el código:
```javascript
// Nota: se excluye encuesta del 12-abr por ser metodológicamente idéntica a la del 15-abr (misma ola)
{ fecha:'2026-04-15', consultora:'CB Consultora', LLA:40.0, ... },
```

---

## 5. Roles: quién hace qué

### CIGOB

- Decide qué encuestas incluir en cada actualización
- Asigna el campo `calidad` (`'A'`, `'B'` o `'C'`) a cada encuesta nueva
- Edita el array `encuestasRaw` en el HTML agregando los nuevos objetos
- Actualiza la constante `ULTIMA_ACTUALIZACION` con la fecha del día
- Es responsable de la precisión de los datos ingresados

### Redlines Estrategia y Comunicación

- Soporte técnico: cambios en la metodología, ajustes al modelo de ponderación
- Desarrollo de nuevas funcionalidades (mapas, nuevas secciones, etc.)
- Ajustes a los factores de CALIDAD, SESGO, MEDIO y METODOLOGIA de consultoras
- Deploy a producción si CIGOB no tiene acceso directo a GitHub

### Regla ante duda metodológica

Si hay dudas sobre si incluir una encuesta, cómo clasificarla, o si un dato parece inconsistente con la serie histórica: **no publicar hasta consultar con Redlines**. Es mejor publicar un día tarde que publicar un dato que distorsione el modelo.

---

## 6. Cómo publicar los cambios

El Votómetro se publica en GitHub Pages. Hay dos formas de hacerlo:

### Opción A: CIGOB hace el deploy directo (requiere Git instalado)

1. Guardar el archivo `votometro.html` modificado
2. Abrir una terminal (Command Prompt o PowerShell) en la carpeta del repositorio
3. Ejecutar los siguientes comandos uno por uno:

```bash
git add web/votometro.html
git commit -m "Actualización encuestas [fecha] — [consultoras agregadas]"
git push
```

**Ejemplo de mensaje de commit descriptivo:**
```bash
git commit -m "Agregar encuestas Trends y Giacobbe abril 2026"
```

4. En unos minutos (1–3 min) el sitio se actualiza solo en GitHub Pages

### Opción B: Enviar el archivo modificado a Redlines para que hagan el deploy

1. Guardar el archivo `votometro.html` modificado
2. Enviarlo por el canal acordado (mail, Drive, WhatsApp) con el mensaje:
   > "Actualización Votómetro — [fecha] — se agregaron [N] encuestas de [consultoras]. Por favor hacer deploy."
3. Redlines sube el archivo y hace el push

### Verificación post-publicación

Después de publicar, abrir el sitio en el navegador y verificar:
- [ ] El footer dice "Actualizado: [fecha correcta]"
- [ ] El número de encuestas en el hero aumentó
- [ ] Las nuevas encuestas aparecen en la tabla de encuestas recientes
- [ ] El gráfico de tendencia refleja los nuevos datos

---

## Apéndice — Referencia rápida de campos

```
fecha        → 'AAAA-MM-DD'    (obligatorio)
consultora   → 'Nombre'        (exacto, sensible a mayúsculas)
LLA          → número (%)      (puede tener decimales)
PJ           → número (%)
PRO          → número (%)
PU           → número (%)
FIT          → número (%)
OTROS        → número (%)      (incluye ns/nc si corresponde)
muestra      → número entero   (0 solo para resultado real)
tipo         → 'espacio'       (intención por partido)
             | 'candidato'     (intención por nombre Milei vs. oponente)
             | 'real'          (resultado electoral oficial)
calidad      → 'A' | 'B' | 'C'
```

---

*Documento preparado para uso interno de la Fundación CIGOB. Ante dudas técnicas, contactar a Redlines Estrategia y Comunicación.*
