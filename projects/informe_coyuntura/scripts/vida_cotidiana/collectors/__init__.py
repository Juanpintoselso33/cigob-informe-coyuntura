from .indec_series import fetch_indec
from .bcra import fetch_bcra
from .utdt_icc import fetch_icc
from .cafam import fetch_cafam
from .ciccra import fetch_ciccra
from .snic import fetch_snic
from .salud import fetch_salud
from .trends import fetch_trends
from .utdt_nowcast_pobreza import fetch_nowcast_pobreza

__all__ = [
    "fetch_indec", "fetch_bcra", "fetch_icc", "fetch_cafam",
    "fetch_ciccra", "fetch_snic", "fetch_salud", "fetch_trends",
    "fetch_nowcast_pobreza",
]
