# Plan de adopción — tres documentos de agosto 2026

Estado: **verificado contra las fuentes reales**, no contra lo que dicen los
documentos. Cada apartado dice qué se comprobó y con qué.

| | Qué es | Fuente | Estado |
|---|---|---|---|
| Proteína animal | Ficha completa | SAGYP, PDF mensual | **Lista para implementar** |
| ICC | Ejemplo de cálculo | UTDT, ya en el informe | **No publicar el número** |
| Cierre de PyMEs | Informe de fuentes | SRT, serie por tamaño | Necesita una ficha primero |

---

## 1. ICC — el número del documento está mal y sale invertido

**Acción: que nadie copie ese número al informe. No hay nada que construir.**

El documento concluye que el Índice de Confianza del Consumidor "registra una
recuperación del +7,7% respecto al promedio del último cuatrimestre de 2023".
Contrastado contra la serie que el propio informe ya publica:

| | Documento | Serie real (UTDT) |
|---|---|---|
| Promedio sep-dic 2023 | 39,0 | **43,55** (42,9 · 44,1 · 46,8 · 40,4) |
| Valor actual | "41,5 a 42,5" | **39,8** (jul-2026) |
| Variación | **+7,7%** (recuperación) | **−8,6%** (caída) |

No es un error de redondeo: los dos insumos están mal y el signo se invierte. El
propio texto avisa que los números son de relleno —"si dispones de los valores
puntuales exactos… obtendrás el porcentaje definitivo"— pero está redactado como
hallazgo, y así es como termina en un informe.

**El ICC ya está en el cinturón vida cotidiana** (`icc_utdt`, 39,8, pesa 82% de
su dimensión) y ya se rebasea contra el 4T-2023 dentro del ITVC. La comparación
que el documento quiere hacer el informe ya la hace, y bien.

---

## 2. Proteína animal — lista, y la fuente confirma la hipótesis

**Acción: implementar. Es el mismo patrón que el desequilibrio monetario (ADR-0192).**

### Lo que se verificó

La fuente que nombra la ficha existe, está viva y es parseable:
`magyp.gob.ar/sitio/areas/bovinos/informacion_sectorial` →
`Tablero_CONSUMO_PER_CAPITA_CARNES_PROMEDIO_MOVIL.pdf`, actualizado **al mes de
junio de 2026**, con el promedio móvil de 12 meses ya calculado por la fuente.

Los datos que trae, y que **confirman la tesis de la ficha**:

```
                 2026      2025     var. i.a.
Carne vacuna    47,28     51,21      −7,67%     ← cae fuerte
Carne aviar     47,24     46,97      +0,57%
Carne porcina   19,93     18,24      +9,29%     ← compensa
TOTAL          114,45    116,42      −1,69%     ← cae mucho menos
```

Hay sustitución real: la vacuna cae 7,7% y el total sólo 1,7% porque cerdo y
pollo la reemplazan. Sin el Componente B, el informe leería esa caída del 7,7%
como deterioro del poder adquisitivo. Con B, se ve que la mayor parte es cambio
de hábito.

**Pero el total también cae**, así que no es sustitución pura: hay ~1,7 puntos
de caída real que el indicador actual tampoco distinguía.

### Lo que hay que decidir antes

- **Choque de fuentes.** El indicador vigente `consumo_carne` usa **CICCRA**
  (47,5 kg, may-2026, PDF mensual scrapeado). La ficha dice IPCVA/SAGYP, y el
  tablero de SAGYP da **47,28** para junio. Son fuentes distintas para el mismo
  Componente A. Recomendación: **pasar A también al tablero de SAGYP**, porque
  ahí los tres componentes salen del mismo PDF, con la misma metodología de
  promedio móvil y el mismo corte temporal. Hoy mezclarlos compararía peras con
  manzanas dentro del propio ratio C.
- **Los cortes de B.** La ficha propone verde ≥112,8 anclado en el promedio
  histórico de la Bolsa de Comercio de Rosario. Eso es un **ancla externa**, que
  es mejor que un percentil de la propia serie: baja la circularidad del índice
  en vez de subirla. Se conserva.
- **El peso.** La ficha propone no sumar peso: redistribuir el de
  `consumo_carne` (3,02% del ITVC) entre A, B y C como un compuesto. Correcto —
  evita que "carne" pese el doble que alquileres dentro del cinturón.

### Riesgo conocido

El PDF trae **datos anuales** (una barra por año 2021-2026), no una serie
mensual. El "al mes de junio" es el corte del promedio móvil, no un punto
mensual. Habrá que acumular la serie mes a mes como ya se hace con CICCRA y con
los patentamientos comerciales.

---

## 3. Cierre de PyMEs — el informe es bueno, pero apunta a un problema mayor

**Acción: primero una ficha; el informe de fuentes no alcanza para implementar.**

### Por qué importa más de lo que parece

Ya existe `mortalidad_pymes` en el cinturón vida cotidiana, pesa **26%** de su
dimensión, y **es un proxy**: su fuente es *"INDEC — IPI manufacturero
desestacionalizado"* y su propia descripción pública dice "aproximada por la
actividad industrial manufacturera".

O sea: el informe dice "mortalidad de PyMEs" y mide producción industrial.

El documento trae exactamente lo que falta para que mida lo que su nombre
promete: la **serie histórica de empleadores según tamaño de nómina de la SRT**,
mensual desde julio de 1996, con trece tramos por cantidad de trabajadores.

### Lo que se verificó, y una advertencia

La serie existe y se publica. **Pero el rezago real es mayor que el que dice el
documento**: la edición de mayo de 2026 llegaba a datos de **febrero de 2026**,
o sea unos tres meses, no los "45 a 60 días" que afirma el texto. Eso importa
porque el gate de calidad tiene topes de frescura por indicador y hay que
declararlo antes, no descubrirlo cuando falle.

### Lo que falta para poder implementarlo

1. Una ficha con la estructura de las otras: definición, bandas, peso, fuente
   exacta y limitaciones.
2. Decidir la métrica: variación neta mensual de empleadores, o acumulada desde
   el inicio del mandato. La segunda es más estable y más comparable con el
   resto del informe, que ya usa base 4T-2023.
3. Decidir el recorte PyME: el documento sugiere 1-50 trabajadores contra más de
   500. Hay que fijarlo, no dejarlo abierto.
4. La segunda mitad del documento —monotributistas y autónomos como sustitución
   del empleo tradicional— es **otro indicador**, no una mejora de éste. Vale la
   pena, pero como ficha aparte.

---

## Orden recomendado

1. **ICC**: avisar hoy. Cuesta un mensaje y evita publicar un número invertido.
2. **Proteína animal**: implementar. Fuente verificada, hipótesis confirmada,
   patrón conocido.
3. **PyMEs**: pedir la ficha, y mientras tanto dejar de llamar "mortalidad de
   PyMEs" a un índice de producción industrial.
