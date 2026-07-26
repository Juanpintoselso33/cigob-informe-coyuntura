# ADR-0141 — Detector de novedades judiciales de la CSJN

- **Estado**: Aceptado
- **Fecha**: 2026-07-26
- **Ámbito**: cinturón político (ITCP), bloque judicial — herramienta interna
- **Relacionados**: ADR-0140 (mapa de acceso), ADR-0129 (mismo patrón,
  privatizaciones), ADR-0131 (protocolo de codificación)

## Contexto

ADR-0140 dejó establecido que el modelo de datos de la CSJN contiene lo que los
indicadores judiciales necesitan, que el buscador completo está detrás de CAPTCHA
y que hay **un endpoint JSON abierto** —el módulo de novedades— con carátula,
fuero, fecha, materia y los booleanos `inconstitucional` y `sentenciaArbitraria`.

Ese endpoint **topea en 10 registros por consulta y no pagina**. No sirve para
contar. Sirve para no perderse un fallo.

## Decisión

Se construye un **detector**, no un indicador. Mismo patrón que ADR-0129 para
privatizaciones: automatiza la vigilancia, no el juicio.

`detectar_novedades_judiciales()` en `scripts/politica.py` barre cuatro términos
—`inconstitucionalidad`, `medida cautelar`, `estado nacional`, `amparo`— y por
cada fallo nuevo decide si lo marca:

- **declara inconstitucionalidad** (`inconstitucional == true`, campo controlado
  de la propia Secretaría de Jurisprudencia), o
- **el Estado es parte**, por carátula.

Todo `idAnalisis` visto queda anotado en `revisadas` con su veredicto —pase o no
el filtro—, así que **un fallo se avisa una sola vez**. Los marcados van a
`pendientes` en `data/politica/csjn_novedades.json` para que el analista los lea
y los saque.

El filtro de «Estado es parte» es **deliberadamente amplio** (`EN-`, `ESTADO
NACIONAL`, `PODER EJECUTIVO`, ANSES, AFIP/ARCA, `MINISTERIO DE`, `SECRETARIA
DE/NACIONAL`…). Un detector que sobre-avisa cuesta un vistazo; uno que sub-avisa
pierde el fallo y nadie se entera. Las formas salen de carátulas reales del
endpoint.

Corre al final de `politica.py`, **envuelto en `try`**: si la CSJN no responde,
lo que se pierde es un aviso, no un dato del índice.

## Lo que este ADR explícitamente NO hace

- **No crea un indicador ni una serie, y no puede.** Con 10 registros por
  consulta cualquier conteo estaría mal. Hay un test dedicado
  (`test_no_alimenta_ningun_indice`) que además verifica que `csjn_novedades` no
  aparezca en `itcp.py`, para que nadie lo conecte al índice por descuido más
  adelante.
- **No clasifica.** Marcar «el Estado es parte» no dice si el fallo frenó una
  política, ni a favor de quién. Eso es lectura, y ADR-0131 fijó cómo hacerla
  (reglas escritas, doble codificación, kappa ≥ 0,70).
- **No resuelve CAPTCHAs** ni busca rodeos al buscador completo.

## Primera corrida

40 registros vistos sobre los cuatro términos, 33 fallos únicos, **17 marcados**:
7 en CAF (Contencioso Administrativo Federal), 2 en CSJ, el resto repartido entre
fueros federales del interior. **Dos declaran inconstitucionalidad**, uno de
ellos «TORRES ABAD, CARMEN c/ EN-JGM s/HABEAS DATA» — exactamente el fenómeno que
el aporte externo llamó *veto de constitucionalidad*.

El filtro discrimina: no marcó «G. B., R. c/ OSDE s/AMPARO DE SALUD», que es un
amparo entre privados.

## Consecuencias

- `data/politica/csjn_novedades.json` entra al `git add` de
  `data-pipeline.yml` **en este mismo cambio**, con un test que lo verifica
  (`test_el_store_esta_en_el_git_add_del_cron`). Es la lección de
  `feedback_cache_persistence_cron`: tres cachés se perdieron por olvidar este
  paso.
- El detector **acumula el universo** que hoy no se puede contar. Si en algún
  momento la CSJN abre el buscador completo —o responde un pedido de acceso a la
  información— el registro ya tendrá historia revisada y la codificación no
  arranca de cero.
- Seis tests nuevos en `tests/test_politica_csjn_detector.py`, todos con sesión
  falsa: no tocan la red.
