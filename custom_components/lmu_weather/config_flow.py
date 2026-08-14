"""Config flow for LMU Weather Station integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_STATION, DOMAIN, STATION_CITY, STATIONS


class LMUWeatherConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LMU Weather Station."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input[CONF_STATION]
            station_info = STATIONS[station_id]

            await self.async_set_unique_id(station_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=station_info["name"],
                data={CONF_STATION: station_id},
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_STATION, default=STATION_CITY): vol.In(
                    {key: info["name"] for key, info in STATIONS.items()}
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
