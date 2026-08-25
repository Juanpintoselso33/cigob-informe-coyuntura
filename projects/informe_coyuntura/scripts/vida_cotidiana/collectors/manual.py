"""
Fuentes que requieren intervención manual o no tienen datos abiertos.
Documenta el estado de cada indicador y el procedimiento para obtenerlo.
"""

FUENTES_MANUALES = {
    "consumo_carne_vacuna": {
        "indicador": "Consumo aparente de carne vacuna per cápita",
        "fuente": "CICCRA (Cámara de la Industria y Comercio de Carnes)",
        "url": "https://www.ciccra.com.ar/estadisticas",
        "frecuencia": "Mensual",
        "formato": "PDF / Excel (publicación mensual)",
        "estado": "NO INVESTIGADO — pendiente verificar URL y formato",
        "procedimiento": (
            "1. Ir a ciccra.com.ar/estadisticas\n"
            "2. Descargar informe mensual (PDF o Excel)\n"
            "3. Extraer 'consumo aparente per cápita' en kg/habitante\n"
            "4. Comparar con mismo mes año anterior"
        ),
    },
    "tarifas_servicios_publicos": {
        "indicador": "Peso de tarifas en el ingreso (luz, gas, agua, transporte)",
        "fuente": "ENRE / ENARGAS / entes reguladores provinciales",
        "url_enre": "https://www.enre.gov.ar/",
        "url_enargas": "https://www.enargas.gob.ar/",
        "frecuencia": "Mensual / cuatrimestral según cuadro tarifario",
        "formato": "PDF de resoluciones, sin API",
        "estado": "ALTA COMPLEJIDAD — no hay API pública ni descarga estructurada",
        "alternativa_recomendada": (
            "Usar el rubro 'Vivienda, agua, electricidad, gas y otros combustibles' "
            "del IPC INDEC (serie: buscar en datos.gob.ar 'ipc vivienda'). "
            "Es menos granular pero automatizable y mensual."
        ),
    },
    "mortalidad_pymes": {
        "indicador": "Tasa de bajas netas de CUITs comerciales y de servicios",
        "fuente_propuesta": "AFIP (Estadísticas Tributarias)",
        "url": "https://www.afip.gob.ar/institucional/estudios/",
        "estado": "NO DISPONIBLE PÚBLICAMENTE — AFIP no publica microdatos de altas/bajas CUIT",
        "alternativa_recomendada": (
            "CAME publica mensualmente el 'Índice de Producción Industrial PyME' (IPIP) "
            "y el 'Índice de Actividad Comercial PyME'. Son proxies de actividad (no mortalidad) "
            "pero capturan el mismo fenómeno de contracción PyME. "
            "URL: came.com.ar/estadisticas"
        ),
    },
    # OJO: esto NO es el indicador que se publica. El tablero publica
    # `subocupacion_demandante` (EPH 47.2), que mide gente que trabaja poco y
    # busca más. Hasta ago-2026 esa card se llamaba `pluriempleo` por error
    # (ADR-0249). El pluriempleo de verdad —tener más de un empleo— sigue sin
    # construirse, y esta entrada documenta cómo se haría.
    "pluriempleo": {
        "indicador": "Proporción de ocupados con más de un empleo (NO se publica)",
        "fuente": "INDEC — EPH microdatos (variable CNOCP o módulo estrategias de hogar)",
        "frecuencia": "Trimestral",
        "estado": "DISPONIBLE EN MICRODATOS — requiere descarga de base EPH y procesamiento",
        "procedimiento": (
            "1. Descargar base individual EPH del trimestre desde indec.gob.ar\n"
            "2. Filtrar por variable PP04G_COD (ocupaciones múltiples)\n"
            "3. Calcular % sobre total de ocupados\n"
            "Nota: la serie sintética pública no incluye este dato"
        ),
        "url_bases": "https://www.indec.gob.ar/indec/web/Institucional-Indec-BasesDeDatos",
    },
    "desercion_escolar": {
        "indicador": "Variación interanual de matrícula secundaria en zonas vulnerables",
        "fuente": "Ministerio de Educación — Relevamiento Anual (RA)",
        "url": "https://www.argentina.gob.ar/educacion/planeamiento/info-estadistica/relevamiento-anual",
        "frecuencia": "ANUAL (con 1 año de retraso)",
        "formato": "Excel descargable",
        "estado": "DISPONIBLE pero no mensualizable — usar como indicador estructural anual",
        "alternativa": (
            "Argentinos por la Educación (argentinosporlaeducacion.org) publica "
            "indicadores procesados más accesibles y con visualizaciones directas."
        ),
    },
    "espera_salud_publica": {
        "indicador": "Tiempo promedio de espera en especialidades críticas",
        "fuente": "SISA — Sistema Integrado de Información Sanitaria Argentina",
        "url": "https://sisa.msal.gov.ar/sisa/",
        "estado": "NO DISPONIBLE EN DATOS ABIERTOS — SISA tiene datos de establecimientos pero no tiempos de espera",
        "alternativa_recomendada": (
            "DEIS (Dirección de Estadísticas e Información en Salud) publica "
            "mortalidad infantil y por causas. No mide espera pero sí resultado. "
            "URL: deis.msal.gov.ar — datos anuales en Excel."
        ),
    },
    "inseguridad_urbana": {
        "indicador": "Tasa de victimización y hechos delictivos",
        "fuente": "SNIC — Sistema Nacional de Información Criminal (Ministerio de Seguridad)",
        "url": "https://www.argentina.gob.ar/seguridad/estadisticascriminales",
        "frecuencia": "Anual (con 6-12 meses de retraso)",
        "estado": "DISPONIBLE pero con rezago significativo",
        "alternativa_mensual": (
            "Encuesta de Victimización del INDEC (publicación irregular) o "
            "índices de consultoras como LICIP-UTDT o Poliarquía. "
            "Estas son las fuentes usadas por el Votómetro para percepción de inseguridad."
        ),
    },
    "sentimiento_digital": {
        "indicador": "Análisis de polaridad sobre 'costo de vida', 'seguridad', 'futuro'",
        "fuente": "APIs de X (Twitter) y Meta",
        "estado": "REQUIERE PIPELINE NLP — no es colector simple",
        "costo": "X API: USD 100+/mes (Basic tier). Meta: restringido a investigadores.",
        "implementacion_sugerida": (
            "1. Suscribir a X API Basic (USD 100/mes) o usar Academic Research\n"
            "2. Query: keywords en español + geolocalización Argentina\n"
            "3. Modelo: sentiment analysis con BERT en español (pysentimiento)\n"
            "4. Output: score diario de polaridad promedio por tema\n"
            "Alternativa gratuita: scrapear Google Trends para 'precios', 'inflación', 'inseguridad'"
        ),
        "alternativa_gratuita": "Google Trends API (pytrends) — sin NLP pero gratuito",
    },
    "apatia_electoral": {
        "indicador": "Sumatoria voto en blanco + nulo + NS/NC en encuestas",
        "fuente": "Votómetro CIGOB (agregado de encuestas)",
        "estado": "DISPONIBLE — ya calculado en web/votometro.html",
        "procedimiento": (
            "Leer del Votómetro el porcentaje de indecisos + voto en blanco "
            "de las encuestas más recientes."
        ),
    },
}


def get_estado_fuentes() -> None:
    """Imprime un resumen del estado de cada fuente manual."""
    print("\n=== ESTADO FUENTES MANUALES ===\n")
    for key, info in FUENTES_MANUALES.items():
        estado = info.get("estado", "Desconocido")
        icon = "✓" if "DISPONIBLE" in estado and "NO" not in estado else "⚠" if "COMPLEJIDAD" in estado or "requiere" in estado.lower() else "✗"
        print(f"{icon} {key}")
        print(f"   Estado: {estado[:80]}...")
        if "alternativa_recomendada" in info or "alternativa_mensual" in info or "alternativa" in info:
            alt = info.get("alternativa_recomendada") or info.get("alternativa_mensual") or info.get("alternativa", "")
            print(f"   Alternativa: {alt[:80]}...")
        print()
