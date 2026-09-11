# Vigencia de catálogos oficiales

Consulta directa del 8 de septiembre de 2026. Las respuestas y sus hashes se
registran en [catalogos-oficiales.json](catalogos-oficiales.json). Los resultados
de buscadores no reemplazan el catálogo: COMARB apareció indexado hasta junio,
pero el portal consultado contiene julio y agosto.

## Rezagos explicados

- El portal RIPTE sigue encabezado por junio de 2026, $1.915.878,76. La brecha
  salarial usa ese mes y su CBT correspondiente, sin mezclar con la CBT de julio.
  El enlace de descarga aparece inactivo (`blank:#`), pero el valor está en la
  tabla HTML oficial. Es una comprobación de publicación, no de todos los
  supuestos del indicador.
- El calendario INDEC anuncia EMAE julio para el 24 de septiembre, IPC agosto
  para el 10, supermercados julio para el 23 y EPH segundo trimestre para el 17.
  Los períodos previos no se convierten en errores por compararlos con la fecha
  de consulta. IPI/ISAC julio tienen publicación prevista el propio 8 de
  septiembre: requieren revisar el corte horario antes del cierre final.

## Rezago tributario corregido

El portal ARCA enlaza la planilla `serie2026.xls` con enero-agosto y el informe de
agosto. Se leyó la planilla OLE con `xlrd` directamente: el lector pandas no
acepta la versión instalada, lo que no impide inspeccionar el archivo original.

Julio contiene derechos de exportación de $1.192.117,217 millones y de
importación de $466.938,064 millones. El ICA vigente ya contiene julio. Sin
embargo, `apertura_comercial` y su reconstrucción todavía consultan exclusivamente
las series de la API y terminan en junio. Hay que completar ambos con las
fuentes originales y mantener su mismo mes común con A3500; no basta con
adelantar la fecha de la tarjeta.

COMARB también enlaza julio y agosto. La base imponible compuesta sigue en
junio. Antes de completar su tramo nacional hay que reconciliar exactamente el
subtotal DGI de la API con la planilla ARCA: «total general», «impuestos» y
«recursos tributarios» tienen universos distintos. No se sustituyó uno por otro.
El IPC limita por ahora el último mes real posible a julio.

### Resolución después de reconciliar las fuentes

Una nueva consulta demostró que la API ARCA ya contiene agosto. La serie de
importación incluye tasa de estadística: en julio, 466.938,064 + 108.728,933 =
575.666,997 millones. No se sustituyó por derechos solos. Se completó el ICA
desde el original y se unificó el cálculo de tarjeta e historia (ADR-0282):
apertura pasa a 7,62% en julio.

En COMARB faltaba ejecutar la actualización antes de leer el store. Corregido
en tarjeta e historia (ADR-0283). Julio y agosto se descargaron y conciliaron:
2.296.256 y 2.321.766 millones, respectivamente. El mes común real queda en
julio, con base imponible 102,1. Se conserva la serie DGI original de la API;
no se la reemplaza por otro subtotal de ARCA. Los factores estacionales
recalculados revisan también meses anteriores.

Resultados y comparación previa en
[cotejo-tributario-actualizado.json](cotejo-tributario-actualizado.json).
