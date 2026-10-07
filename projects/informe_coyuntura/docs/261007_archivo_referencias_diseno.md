# Archivo de ediciones: referencias de diseño (7-oct-2026)

Juan pidió buscar cómo resuelven su archivo de ediciones productos parecidos, porque la grilla de
tarjetas de `/archivo/` (ADR-0348) no le gustó. Se relevaron 50 referencias: 44 con captura y 6 solo
por búsqueda. 10 no se pudieron ver (bloqueo, error o carga a medias) y figuran igual con el motivo.

## Patrones

- **P1. Mapa de calor año × mes como índice navegable.**
  - Cada celda es un mes, con el color del semáforo y el score adentro.
  - Al pasar el mouse muestra los 4 cinturones; con un clic abre la edición.
  - Los meses futuros quedan como celdas vacías.
  - Referencias: CFGI, Bitcoin Heatmap, QuantJuice, Daily AI Archive y la escala con nombres de Fragile States.
- **P2. Tabla de ediciones con 4 carriles de color.**
  - Una fila por mes con sus columnas: mes y titular, score, cuatro celdas de cinturón, riesgo dominante y cambio contra el mes anterior.
  - Las columnas de color, leídas de arriba abajo, forman franjas: la historia de cada cinturón.
  - Las filas con un hito llevan una marca.
  - Referencias: FOMC y Banxico, combinados con #ShowYourStripes; el titular por edición, del FMI.
- **P3. Línea de tiempo vertical con hitos.**
  - Solo los meses en que algo cambió llevan rótulo y frase.
  - Referencias: Doomsday Clock, Noahpinion y Conference Board.
- **P4. Edición por edición (◀ mes ▶)** con el resumen de la edición en la misma página.
  - Referencias: Drought Monitor, el BCE y el Banco Central de Chile.

## Las 50 referencias

### A. Grilla año × mes con color

1. **CFGI, reportes mensuales**: grilla mes por mes con puntaje y color, y debajo cada mes desarrollado. La más cercana a nuestro caso.
2. **Bitcoin Heatmap**: calendario de calor, sobrio, con tipografía serif.
3. **QuantJuice**: tabla de calor año × mes.
4. **ChartsCheck**: grilla con detalle al pasar el mouse.
5. **ChartRow**: una marca por año dentro de cada mes.
6. **Daily AI Archive**: calendario de calor como índice de un archivo.
7. **Fragile States Index**: escala de estados con nombre.

### B. Franja o línea de tiempo como índice

8. **Doomsday Clock, línea de tiempo**: destaca solo los años en que el reloj se movió.
9. **#ShowYourStripes**: franjas de color sin ejes.
10. **Alternative.me, Fear & Greed**: valores de hoy, de la semana y del mes.
11. **Conference Board, LEI**: tira de variaciones por componente.
12. **Our World in Data**: barra para recorrer años.
13. **US Drought Monitor**: navegación con ◀ ▶.

### C. Lista o tabla cronológica

14. **Fed, FOMC**: bloque por año, una fila por reunión, y los meses futuros vacíos.
15. **Fed, Beige Book**: lista corta más un link al archivo.
16. **Banxico**: fecha, título y formatos, muy denso.
17. **BCRA, IPOM**: tabla que repite el título en cada fila (ejemplo a evitar).
18. **UTDT, ICG**: mes y una frase con el valor y su contexto. Antecedente local.
19. **Stratechery**: año → mes.
20. **RBA**: años desplegables.
21. **Equilibra**: tarjeta genérica con imagen (ejemplo a evitar).
22. **LSEG**: lista mensual con «Show more».
23. **The Chart Store**: título por mes.
24. **Noahpinion**: separador de mes.
25. **FMI, WEO**: un titular por edición.
26. **Banco Central de Chile, IPoM**: «¿Qué nos dice este IPoM?» en 4 frases.
27. **Banco Central de Chile, recuadros**: índice de 25 años.
28. **Poliarquía**: sparklines al costado de las notas.
29. **Directorio Legislativo**: filtros y tarjetas.
30. **CIPPEC**: tarjetas y buscador.
31. **IERAL**: carrusel, sin archivo.
32. **Latinobarómetro**: sin archivo visible.

### D. Portadas por edición

33. **V-Dem**: tapas.
34. **Foreign Affairs**: sumario y tapa.
35. **WEF, Global Risks**: tarjetas con tapa (el patrón que no gustó).
36. **BCE**: la próxima edición anunciada y un carrusel.
37. **Eurasia Group**: riesgos numerados.
38. **Freedom House**: mapa y la edición actual.
39. **EIU**: descarga con formulario, sin archivo.
40. **NOAA**: selectores de año y mes.

### E. Sin captura útil

41. **The Economist**: bloqueo de Cloudflare.
42. **Bank of England**: acceso denegado.
43. **Edelman**: acceso denegado.
44. **OCDE**: bloqueo de Cloudflare.
45. **INDEC**: página de error.
46. **CEPAL**: página no encontrada.
47. **The New Yorker**: error 404.
48. **ifo**: la captura salió en blanco.
49. **BCRA, Política Monetaria**: vista solo en la búsqueda.
50. **Pew y GDPNow**: no revisados.
