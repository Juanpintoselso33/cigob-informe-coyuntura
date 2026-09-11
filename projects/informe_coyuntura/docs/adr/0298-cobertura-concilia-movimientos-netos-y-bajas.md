---
madr: 4
id: '0298'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indicadores: [cobertura_judicial]
archivos: ['scripts/politica.py', 'scripts/cobertura_judicial.py', 'web/src/lib/fichas.ts', 'tests/test_judicial_sello_revision.py']
ambito: 'Reconstrucción estimada de cobertura judicial'
---

# ADR-0298 — Cobertura concilia movimientos netos y bajas

Sumar todas las designaciones como nuevas coberturas duplicaba titulares que
cambiaban de cargo. El CSV tampoco incorporaba todas las normas posteriores a
su publicación y omitía bajas distintas de renuncias. La foto de junio incluso
conservaba como no vacante el cargo de Ana Silvia Guzzardi, fallecida en marzo.

Se preserva el padrón original y se corrige el ancla con bajas comprobadas que
todavía figuran como no vacantes. Los movimientos se concilian por norma y tipo:
el complemento reemplaza el registro, incluso cuando el CSV lo incorpora más
tarde. Una norma ambigua con varios movimientos exige desagregación explícita.
Promociones internas, renovaciones y conjueces no suman altas netas. La serie
resta movimientos antes del ancla y los suma después; tarjeta e historia usan
el mismo cálculo. Los registros y sus fuentes están en `data/politica/`.

La fecha máxima es la menor entre hoy y las fechas revisadas de ambos registros.
Un padrón diferente exige revisar la conciliación antes de publicar datos nuevos.
El numerador original, las correcciones y cada flujo se explicitan por separado.

La decisión acepta una estimación con límites, no certifica el stock físico.
No se dispone de un calendario completo de juras ni un censo de fallecimientos.
Se conserva el universo habilitado del padrón: un destino fuera de él no entra
sin acreditar habilitación. Fraga (918/2026) mantiene provisionalmente efecto
neto cero; verificar su salida del cargo de origen podría reducir el numerador
en uno. El pendiente sigue visible en la ficha y la auditoría.

La conciliación al 8 de septiembre da 705/955 (73,82%); con la salida de Fraga
del universo serían 704/955 (73,72%). Ninguna opción equivale a medir afinidad
judicial, desempeño de los tribunales ni atribución exclusiva al Ejecutivo.

Validación: pruebas de baja omitida y ya incorporada, promociones, deduplicación,
corte temporal, cambio de padrón y coherencia conjunta de tarjeta e historia.
Evidencia documental: `docs/auditorias/2026-09-08/cotejo-judicial-normas-posteriores.json`
y los registros complementarios enlazados por acto.

La revisión de código detectó que una conciliación vencida podía recibir un
sello nuevo al ejecutarse el colector otro día. Se corrige: conserva como
fecha de obtención el corte documentado y no aumenta el contador de resultados
frescos. Releer registros curados no equivale a renovar su revisión; el gate
puede así detectar su antigüedad. La prueba ejecuta el colector con revisión
vigente y vencida y comprueba sello, valor conservado y código de salida.
