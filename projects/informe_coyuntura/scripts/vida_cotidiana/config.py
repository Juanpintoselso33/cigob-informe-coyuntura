# config.py — Constantes del monitor Cinturón Vida Cotidiana
# Todos los IDs verificados con requests reales al 2026-05-10

# ── INDEC / datos.gob.ar ────────────────────────────────────────────────────
DATOS_GOB_BASE   = "https://apis.datos.gob.ar/series/api/series/"
DATOS_GOB_SEARCH = "https://apis.datos.gob.ar/series/api/search/"

INDEC_SERIES = {
    # Precios
    "ipc_total":               "148.3_INIVELNAL_DICI_M_26",    # IPC total nacional, mensual
    "ipc_alimentos":           "146.3_IALIMENNAL_DICI_M_45",   # IPC Alimentos y Bebidas no alc.
    "ipc_vivienda":            "146.3_IVIVIENNAL_DICI_M_52",   # IPC Vivienda+agua+elec+gas (tarifas)
    "ipc_regulados":           "148.3_IREGULANAL_DICI_M_22",   # IPC Regulados (tarifas directas)

    # Canasta basica (para brecha salario vs CBT)
    "cbt":                     "150.1_CSTA_BATAL_0_D_20",      # Canasta Basica Total (adulto equiv.)
    "cba":                     "150.1_CSTA_BARIA_0_D_26",      # Canasta Basica Alimentaria

    # Salarios
    "isalarios_total":         "149.1_TL_INDIIOS_OCTU_0_21",
    "isalarios_privado":       "149.1_TL_REGIADO_OCTU_0_16",

    # Empleo (EPH - trimestral)
    "desocupacion":            "42.3_EPH_PUNTUATAL_0_M_30",    # Tasa desocupacion %
    "empleo":                  "42.3_EPH_PUNTUATAL_0_M_24",    # Tasa empleo %
    "informalidad_trimestral": "52.2_ASDJ_0_0_37",             # Asalariados sin desc. jubil. (TRIMESTRAL, 2011→) — métrica del ITVC
    "informalidad_anual":      "52.1_ASDJ_0_0_37",             # variante anual: respaldo
    "subocupacion_demandante": "47.2_ECTSDT_0_T_47",           # Proxy pluriempleo (trimestral)

    # Actividad / Construccion
    "isac":                    "33.2_ISAC_SIN_EDAD_0_M_23_56",
    "emae":                    "143.3_ICE_SERVIA_2004_A_25",
    # IPI manufacturero DESESTACIONALIZADO (proxy PyMEs): la serie original
    # mostraba ±20% m/m de puro calendario (Semana Santa, días hábiles)
    "ipi":                     "453.1_SERIE_DESEADA_0_0_24_58",
    "ipi_original":            "453.1_SERIE_ORIGNAL_0_0_14_46", # respaldo/referencia

    # Ganaderia
    "faena_vacuna":            "41.3_FCV_0_A_18",              # Faena vacuna (miles cabezas, mensual)

    # Siderurgia
    "acero_crudo":             "41.3_AC_0_A_11",               # Acero crudo (miles ton, mensual)
}

RIPTE_CSV = (
    "https://infra.datos.gob.ar/catalog/sspm/dataset/158/distribution/158.1/download/"
    "remuneracion-imponible-promedio-trabajadores-estables-ripte-total-pais-pesos-serie-mensual.csv"
)

# ── BCRA API v4.0 ────────────────────────────────────────────────────────────
BCRA_BASE = "https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias"
BCRA_VARIABLES = {
    "prestamos_privado_total": 26,
    "prestamos_hipotecarios":  112,
    "prestamos_personales":    114,
    "prestamos_tarjeta":       115,
    "badlar":                  7,
}

# ── UTDT ─────────────────────────────────────────────────────────────────────
UTDT_ICC_LISTADO       = "https://www.utdt.edu/listado_contenidos.php?id_item_menu=16458"
UTDT_ICC_DOWNLOAD_BASE = "https://www.utdt.edu/download.php?fname="

# ── CAFAM ─────────────────────────────────────────────────────────────────────
CAFAM_API = "https://back.cafam.org.ar/api/patentamientos"

# ── CICCRA — Carne vacuna per capita ─────────────────────────────────────────
# Informes mensuales con numeracion correlativa: 300=ene-2026, 301=feb-2026, etc.
CICCRA_HOME           = "https://ciccra.com.ar/"
CICCRA_INF_BASE       = "https://ciccra.com.ar/wp-content/uploads/"
CICCRA_INF_START_NUM  = 300
CICCRA_INF_START_YEAR = 2026
CICCRA_INF_START_MONTH = 1

# ── Camara Argentina del Acero ────────────────────────────────────────────────
ACERO_SITE_BASE = "https://www.acero.org.ar/"

# ── SNIC — Estadisticas criminales ───────────────────────────────────────────
# Descarga directa verificada. Last-Modified 2025-05-21. Frecuencia: anual.
SNIC_CSV = "https://cloud-snic.minseg.gob.ar/Bases/SNIC/snic-pais.csv"
CABA_DELITOS_URL = "https://cdn.buenosaires.gob.ar/datosabiertos/datasets/ministerio-de-justicia-y-seguridad/delitos/delitos_{year}.csv"

# ── Salud ─────────────────────────────────────────────────────────────────────
# API CKAN. IMPORTANTE: SSL cert roto, usar verify=False.
SALUD_CKAN_BASE = "https://datos.salud.gob.ar/api/3/action/"

# ── Google Trends ─────────────────────────────────────────────────────────────
TRENDS_KEYWORDS = ["inflacion", "precios", "inseguridad", "trabajo"]
TRENDS_GEO      = "AR"

# ── Google Trends — intencion migratoria (ADR-0035) ──────────────────────────
# Tanda 1: puntuable (4o proxy de espiritu_epoca). Tandas 2-4: contexto, sin
# backfill. Tanda 5: diagnostico de causa (economico vs. estructural).
MIGRACION_TANDA_INTENCION = [
    "emigrar de argentina", "como irme de argentina", "quiero irme del pais",
    "vivir en el exterior", "trabajo en el exterior",
]
MIGRACION_TANDA_CIUDADANIAS = [
    "ciudadania italiana", "ciudadania espanola", "pasaporte italiano",
    "pasaporte europeo", "descendencia italiana",
]
MIGRACION_TANDA_TRABAJO_VISAS = [
    "visa de trabajo", "trabajar en espana", "trabajar en estados unidos",
    "sponsorship visa", "curriculum en ingles",
]
MIGRACION_TANDA_DESTINOS = [
    "mudarse a espana", "mudarse a estados unidos", "mudarse a australia",
    "vivir en miami", "emigrar a canada",
]
MIGRACION_TANDA_DIAGNOSTICO = [
    "inflacion argentina", "inseguridad argentina", "no hay futuro en argentina",
]
MIGRACION_CATEGORIA_EMPLEO = 60  # categoria "Jobs" de Google Trends

# ── General ───────────────────────────────────────────────────────────────────
HTTP_TIMEOUT = 30
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}
MESES_ES = ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"]
