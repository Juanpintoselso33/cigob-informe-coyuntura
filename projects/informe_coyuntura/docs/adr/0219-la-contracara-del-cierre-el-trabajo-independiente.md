---
madr: 4
id: '0219'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'vida'
indicadores: [trabajo_independiente]
archivos: ['scripts/vida_cotidiana/collectors/trabajo_independiente.py', 'scripts/vida_cotidiana/main.py', 'scripts/descargar_series.py', 'scripts/itvc.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/procedencia_anclas.py', 'scripts/gate_calidad.py', 'tests/test_trabajo_independiente.py']
complementa: ['0218']
relacionado: ['0033', '0130', '0220', '0225', '0250']
ambito: 'ITCIS · dimensión de prospectivas de empleo · sustitución de asalariados por independientes'
origen: 'Segunda mitad del documento "260811 cierre de pymes", que ADR-0218 dejó anotada como otro indicador'
---

# ADR-0219 — La contracara del cierre: el trabajo independiente

## Contexto y planteo del problema

[[0218-el-cierre-de-pymes-se-mide-con-la-srt]] puso en el índice el cierre neto
de PyMEs y dejó anotado lo que no medía: **una economía donde cierran empresas
y aparecen personas facturando por su cuenta no es lo mismo que una donde
cierran y no aparece nada.** El documento de fuentes lo planteaba como su
segunda mitad — monotributistas y autónomos como el otro lado de la
reconfiguración de la matriz productiva.

Sin ese dato el informe ve media película. Publica que hay 30.707 empleadores
PyME menos y no puede decir si esas unidades productivas desaparecieron o se
transformaron.

## Factores de decisión

- **El indicador tiene que responder la pregunta que abre el otro**, o es un
  dato suelto más en una dimensión que ya tiene cinco.
- **El signo hay que declararlo y sostenerlo.** Un desplazamiento hacia el
  trabajo por cuenta propia admite dos lecturas —emprendedorismo o
  precarización— y publicar un puntaje obliga a elegir una.
- **La serie no puede mezclar economía con regulación.** Un cambio de régimen
  que mueve cientos de miles de personas de un mes al otro no es mercado de
  trabajo.

## Opciones consideradas

1. Participación del trabajo independiente en el empleo registrado, invertida.
2. Cantidad de independientes en nivel, rebaseada.
3. No crear un indicador y usar el dato sólo como explicación del color de
   `mortalidad_pymes`, como hace la matriz A×B de proteína animal.
4. No incorporarlo.

## Decisión

**Opción 1.** Entra `trabajo_independiente`: **qué proporción del empleo
registrado son autónomos y monotributistas**, frente a los asalariados de los
tres sectores (privado, público y casas particulares). Fuente: SIPA, vía las
series mensuales sin estacionalidad de datos.gob.ar.

Puntúa **invertido**: más peso independiente es peor. El fundamento es el mismo
con el que el cinturón ya invierte `informalidad` y `pluriempleo` — un empleo
que se corre del salario al trabajo por cuenta propia pierde aportes
patronales, indemnización y estabilidad, aunque siga siendo registrado. **La
lectura contraria existe y el propio documento la nombra** ("no siempre
significa una pérdida equivalente de valor económico agregado"): si la
Fundación decide que el emprendedorismo registrado es una mejora, se cambia el
`invertido=True` de una línea en `itvc.py` y se recalcula.

Entra con **10% de la dimensión** y los cinco componentes previos ceden
proporcionalmente (×0,90), conservando su orden relativo — la regla de
[[0130-la-dimension-empleo-pasa-a-medir-empleo]] y ADR-0153. El peso nominal de
la dimensión no se toca.

### El monotributo social queda AFUERA, y es la decisión que más importa acá

Su serie **cae 394 mil personas en un solo mes**, diciembre de 2024. No es un
fenómeno del mercado de trabajo: es una decisión regulatoria sobre el propio
régimen.

El costo de no verlo se mide:

| Serie | 4T-2023 | may-2026 | Lectura |
|---|---|---|---|
| Con monotributo social | 22,91% | 22,05% | la participación **baja** |
| **Sin monotributo social** | **19,12%** | **20,60%** | la participación **sube** |

Las dos lecturas son opuestas y sólo una describe la economía. Con el régimen
social adentro, y con el signo invertido, el indicador habría leído una reforma
administrativa **como una mejora del empleo**.

### Consecuencias

- **El componente entra en 92,8** (participación 19,12% → 20,60%, invertida) con
  2,42% del índice. El ITCIS queda en 90,6 y la tensión en 6,9: el alta se
  compensa con la dilución de los otros cinco.
- **La hipótesis del documento se confirma con datos**: entre el 4T-2023 y mayo
  de 2026 los independientes registrados crecen **+6,2%** (2.436 mil → 2.587
  mil) mientras los asalariados caen **−3,3%** (10.306 mil → 9.967 mil). El
  cierre de PyMEs no es destrucción pura: hay reconfiguración.
- La dimensión de prospectivas de empleo queda con **seis componentes** y cuatro
  de ellos miden empleo directamente. El diagnóstico de ADR-0033 —"ninguno de
  sus componentes mide empleo"— quedó del todo atrás.
- El tope de frescura es 165 días, igual que el de la SRT: SIPA publica con el
  mismo rezago de unos tres meses.

### Confirmación

`tests/test_trabajo_independiente.py` cuida lo que puede volver a romperse: que
el monotributo social siga excluido —con el mes del quiebre nombrado—, que el
signo siga invertido, que card y serie sean el mismo número, y que la serie
llegue al 4T-2023.

## Pros y contras de las opciones

**1. Participación, invertida.** A favor: responde exactamente la pregunta que
abre el cierre de PyMEs, normaliza por el tamaño del mercado de trabajo y tiene
un signo defendible y declarado. En contra: el signo es discutible, y la
participación puede subir porque caen los asalariados y no porque crezcan los
independientes — por eso el ADR publica las dos variaciones por separado.

**2. Nivel de independientes.** A favor: más simple. En contra: crece con la
población y con cualquier campaña de formalización; sin normalizar no dice si
la estructura del empleo cambió.

**3. Sólo como explicación del color.** A favor: evita elegir un signo, que es
el punto débil de la opción 1. En contra: deja fuera del índice un movimiento
de 150 mil personas que el cinturón sí debería pesar, y el informe ya tiene el
mecanismo de explicación ocupado por la matriz A×B de la carne.

**4. No incorporarlo.** A favor: ninguno. En contra: deja publicado el cierre de
empresas sin su contracara, que es justo lo que ADR-0218 anotó como pendiente.

## Más información

- Series usadas, todas sin estacionalidad y mensuales: autónomos
  `151.1_IPENDIETAC_2012_M_34`, monotributo `151.1_IPENDIETAC_2012_M_36`,
  asalariados privado `151.1_AARIADOTAC_2012_M_26`, público
  `..._M_25` y casas particulares `..._M_40`.
- La serie excluida queda nombrada en el colector, con el mes del quiebre, para
  que la exclusión sea una decisión visible y no un olvido.
