"""Constants for the LMU Weather Station integration."""
from datetime import timedelta
import logging
from typing import Final

DOMAIN: Final = "lmu_weather"
ATTRIBUTION: Final = "Data provided by Meteorological Institute Munich (LMU)"

UPDATE_INTERVAL: Final = timedelta(minutes=2)
LOGGER: Final = logging.getLogger(__package__)

CONF_STATION: Final = "station"

STATION_CITY: Final = "stadt"
STATION_GARCHING: Final = "garching"

STATIONS: Final[dict[str, dict[str, str]]] = {
    STATION_CITY: {
        "name": "Munich City (Theresienstraße 37)",
        "url": "https://www.meteo.physik.uni-muenchen.de/~quicklooks/aktuelle_messwerte/messwerte_stadt.html",
    },
    STATION_GARCHING: {
        "name": "Garching (Oskar von Miller Tower)",
        "url": "https://www.meteo.physik.uni-muenchen.de/~quicklooks/aktuelle_messwerte/messwerte_garching.html",
    },
}
