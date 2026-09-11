# Cotejo de cartera en CONTRAT.AR

Consulta pública del 8-sep-2026 a [Búsqueda Avanzada](https://contratar.gob.ar/BuscarAvanzado.aspx), accediendo desde la portada para conservar la sesión. Sin login, sin filtros de estado o fecha. Quince búsquedas por nombre; cada resultado positivo devolvió una única fila, sin paginación observada. [Consultas y resultados](cotejo-contratar-cartera.json).

| Consulta | Proceso | Estado publicado | Apertura indicada |
|---|---|---|---|
| AySA | 504/2-0003-LPU26 | Publicado | 15-sep-2026, 10:00 |
| Intercargo | 504/2-0002-LPU26 | Desierto | 25-jun-2026, 10:00 |
| Citelec / ENARSA | 504/2-0002-CPU25 | Con Documento Contractual | 28-abr-2026, 10:00 |
| hidroel | 504/2-0001-CPU25 | Adjudicado | 28-nov-2025, 10:00 |

Confirman hitos ya conservados; no cambian etapas ni acreditan montos cobrados. La fecha de apertura de una licitación no es la fecha de cierre de la transferencia. Citelec y ENARSA devuelven el mismo proceso: no son operaciones sumables.

No hubo coincidencias por Transener, Energía Argentina, Corredores Viales, Belgrano Cargas, Nucleoeléctrica, Río Turbio, Operadora Ferroviaria, ferroví (consulta sin acento: `ferrovi`) ni privatiza. La búsqueda amplia Belgrano devolvió una obra del campamento de DNV en Formosa de 2023, ajena a la privatización. Estas ausencias no invalidan las normas: el buscador consulta nombres de procesos, no un padrón exhaustivo de empresas ni sus actos societarios.

La [ME 1350/2026](https://www.boletinoficial.gob.ar/detalleAviso/primera/346112/20260820), releída para resolver la ausencia de Belgrano, autoriza 504/2-0004-LPU26 y fija presentación de ofertas hasta el 11-nov-2026 a las 09:59. Por lo tanto no se retira el llamado acreditado por esa norma porque una búsqueda textual no lo encuentre.

La revisión integral permanece parcial: faltan los procesos no recuperados y la conciliación de cobros. No se actualizaron fechas generales de revisión, cachés ni valores a partir de resultados negativos. No fue necesario repetir pruebas o build porque esta etapa sólo agrega evidencia.

La consulta adicional por número de Belgrano no se completó: se cargó el campo de búsqueda rápida pero se accionó el botón de búsqueda avanzada; no se observó un POST y venció la espera de 30 segundos. No es un resultado negativo ni prueba de caída del portal. Para continuar hay que usar el control propio de búsqueda rápida, no repetir la misma interacción.

## Consulta exacta de Belgrano completada

El control correcto es `ctl00_CPH1_btnListarPliegoNumero`. Su consulta devuelve una fila: 504/2-0004-LPU26, «Concesión de vías e inmuebles aledaños de LB, LSM y LU.», Publicado, apertura 11-nov-2026 10:00. El nombre abreviado explica el fracaso de las búsquedas por empresa. Queda corroborado el llamado sin modificar etapa. El intento anterior fallido queda superado por este cotejo.
