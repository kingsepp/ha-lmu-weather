"""DataUpdateCoordinator for LMU Weather Station."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_STATION, DOMAIN, LOGGER, STATION_CITY, STATIONS, UPDATE_INTERVAL
from .parser import parse_lmu_weather_html

_LOGGER = logging.getLogger(__name__)


class LMUWeatherDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching LMU Weather data."""

    def __init__(self, hass: HomeAssistant, station_id: str = STATION_CITY) -> None:
        """Initialize coordinator."""
        self.station_id = station_id
        self.station_info = STATIONS.get(station_id, STATIONS[STATION_CITY])
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from LMU website."""
        session = async_get_clientsession(self.hass)
        url = self.station_info["url"]
        try:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error fetching LMU weather data: HTTP {response.status}")
                html = await response.text()
                data = parse_lmu_weather_html(html)
                if not data:
                    raise UpdateFailed("Failed to parse LMU weather data from HTML")
                return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with LMU weather website: {err}") from err
