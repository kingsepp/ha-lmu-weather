"""Test the LMU Weather Station config flow."""

from unittest.mock import AsyncMock

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

# Literal values instead of importing custom_components.lmu_weather.const:
# HA's loader only makes `custom_components.*` importable once it has
# actually loaded the integration at runtime (via the `hass` fixture's
# config dir), not at test-collection time.
DOMAIN = "lmu_weather"
CONF_STATION = "station"
STATION_CITY = "stadt"
STATION_GARCHING = "garching"
STATION_NAMES = {
    STATION_CITY: "Munich City (Theresienstraße 37)",
    STATION_GARCHING: "Garching (Oskar von Miller Tower)",
}


async def _start_flow(hass: HomeAssistant):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_form_creates_entry_for_selected_station(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Selecting a station creates a config entry titled after that station."""
    result = await _start_flow(hass)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATION: STATION_GARCHING}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == STATION_NAMES[STATION_GARCHING]
    assert result["data"] == {CONF_STATION: STATION_GARCHING}
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_defaults_to_munich_city(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Submitting without picking a station defaults to Munich City."""
    result = await _start_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_STATION: STATION_CITY}


async def test_duplicate_station_aborts(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Configuring the same station twice aborts the second attempt."""
    result = await _start_flow(hass)
    await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATION: STATION_CITY}
    )

    result = await _start_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATION: STATION_CITY}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_both_stations_can_be_added(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Munich City and Garching can both be configured at the same time."""
    result = await _start_flow(hass)
    result_city = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATION: STATION_CITY}
    )
    assert result_city["type"] is FlowResultType.CREATE_ENTRY

    result = await _start_flow(hass)
    result_garching = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_STATION: STATION_GARCHING}
    )
    assert result_garching["type"] is FlowResultType.CREATE_ENTRY

    assert len(mock_setup_entry.mock_calls) == 2
