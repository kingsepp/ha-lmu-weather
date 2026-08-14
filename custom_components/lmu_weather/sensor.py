"""Sensor platform for LMU Weather Station."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import re
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    EntityCategory,
    UnitOfIrradiance,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LMUWeatherConfigEntry
from .const import ATTRIBUTION, DOMAIN
from .coordinator import LMUWeatherDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class LMUWeatherSensorEntityDescription(SensorEntityDescription):
    """Describes LMU Weather sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]


def _build_sensor_description(key: str) -> LMUWeatherSensorEntityDescription:
    """Build sensor entity description dynamically for key."""
    # 1. Height profiles (temp_Xm, humidity_Xm, wet_temp_Xm, dewpoint_Xm, wind_speed_Xm)
    if match := re.match(r"^(temp|humidity|wet_temp|dewpoint|wind_speed)_(.+)m$", key):
        param, height = match.groups()
        h_formatted = height.replace("_", ".") + "m"
        
        if param == "temp":
            return LMUWeatherSensorEntityDescription(
                key=key,
                name=f"Temperature ({h_formatted})",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, k=key: data.get(k),
            )
        if param == "wet_temp":
            return LMUWeatherSensorEntityDescription(
                key=key,
                name=f"Wet Bulb Temperature ({h_formatted})",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, k=key: data.get(k),
            )
        if param == "humidity":
            return LMUWeatherSensorEntityDescription(
                key=key,
                name=f"Relative Humidity ({h_formatted})",
                native_unit_of_measurement=PERCENTAGE,
                device_class=SensorDeviceClass.HUMIDITY,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, k=key: data.get(k),
            )
        if param == "dewpoint":
            return LMUWeatherSensorEntityDescription(
                key=key,
                name=f"Dew Point ({h_formatted})",
                native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, k=key: data.get(k),
            )
        if param == "wind_speed":
            return LMUWeatherSensorEntityDescription(
                key=key,
                name=f"Wind Speed ({h_formatted})",
                native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
                device_class=SensorDeviceClass.WIND_SPEED,
                state_class=SensorStateClass.MEASUREMENT,
                value_fn=lambda data, k=key: data.get(k),
            )

    # 2. Soil Temperature (soil_temp_Xcm)
    if match := re.match(r"^soil_temp_(.+)cm$", key):
        depth = match.group(1)
        return LMUWeatherSensorEntityDescription(
            key=key,
            name=f"Soil Temperature (-{depth}cm)",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data, k=key: data.get(k),
        )

    # 3. Wind Bearings (wind_bearing_Xm)
    if match := re.match(r"^wind_bearing_(.+)m$", key):
        h_formatted = match.group(1) + "m"
        return LMUWeatherSensorEntityDescription(
            key=key,
            name=f"Wind Bearing ({h_formatted})",
            native_unit_of_measurement=DEGREE,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:compass",
            value_fn=lambda data, k=key: data.get(k),
        )

    # 4. Standard Static Sensors
    KNOWN_SENSORS: dict[str, LMUWeatherSensorEntityDescription] = {
        "measured_at": LMUWeatherSensorEntityDescription(
            key="measured_at",
            name="Last Measurement",
            device_class=SensorDeviceClass.TIMESTAMP,
            entity_category=EntityCategory.DIAGNOSTIC,
            value_fn=lambda data: data.get("measured_at"),
        ),
        "global_radiation": LMUWeatherSensorEntityDescription(
            key="global_radiation",
            name="Global Irradiance",
            native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
            device_class=SensorDeviceClass.IRRADIANCE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.get("global_radiation"),
        ),
        "diffuse_radiation": LMUWeatherSensorEntityDescription(
            key="diffuse_radiation",
            name="Diffuse Irradiance",
            native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
            device_class=SensorDeviceClass.IRRADIANCE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.get("diffuse_radiation"),
        ),
        "reflected_radiation": LMUWeatherSensorEntityDescription(
            key="reflected_radiation",
            name="Reflected Irradiance",
            native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
            device_class=SensorDeviceClass.IRRADIANCE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.get("reflected_radiation"),
        ),
        "atmospheric_counter_radiation": LMUWeatherSensorEntityDescription(
            key="atmospheric_counter_radiation",
            name="Atmospheric Counter Radiation",
            native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
            device_class=SensorDeviceClass.IRRADIANCE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.get("atmospheric_counter_radiation"),
        ),
        "longwave_outgoing_radiation": LMUWeatherSensorEntityDescription(
            key="longwave_outgoing_radiation",
            name="Longwave Outgoing Radiation",
            native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
            device_class=SensorDeviceClass.IRRADIANCE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.get("longwave_outgoing_radiation"),
        ),
        "albedo": LMUWeatherSensorEntityDescription(
            key="albedo",
            name="Albedo",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:brightness-5",
            value_fn=lambda data: data.get("albedo"),
        ),
        "sunshine_duration": LMUWeatherSensorEntityDescription(
            key="sunshine_duration",
            name="Sunshine Duration",
            icon="mdi:weather-sunny",
            value_fn=lambda data: data.get("sunshine_duration"),
        ),
        "uv_index": LMUWeatherSensorEntityDescription(
            key="uv_index",
            name="UV Index",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:sun-wireless",
            value_fn=lambda data: data.get("uv_index"),
        ),
        "pressure_station": LMUWeatherSensorEntityDescription(
            key="pressure_station",
            name="Air Pressure (Station)",
            native_unit_of_measurement=UnitOfPressure.HPA,
            device_class=SensorDeviceClass.PRESSURE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.get("pressure_station"),
        ),
        "pressure_sealevel": LMUWeatherSensorEntityDescription(
            key="pressure_sealevel",
            name="Air Pressure (Sea Level)",
            native_unit_of_measurement=UnitOfPressure.HPA,
            device_class=SensorDeviceClass.PRESSURE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.get("pressure_sealevel"),
        ),
        "precipitation_current": LMUWeatherSensorEntityDescription(
            key="precipitation_current",
            name="Precipitation Rate",
            native_unit_of_measurement=UnitOfLength.MILLIMETERS,
            device_class=SensorDeviceClass.PRECIPITATION,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda data: data.get("precipitation_current"),
        ),
        "precipitation_today": LMUWeatherSensorEntityDescription(
            key="precipitation_today",
            name="Precipitation Today",
            native_unit_of_measurement=UnitOfLength.MILLIMETERS,
            device_class=SensorDeviceClass.PRECIPITATION,
            state_class=SensorStateClass.TOTAL_INCREASING,
            value_fn=lambda data: data.get("precipitation_today"),
        ),
        "precipitation_type": LMUWeatherSensorEntityDescription(
            key="precipitation_type",
            name="Precipitation Type",
            icon="mdi:weather-rainy",
            value_fn=lambda data: data.get("precipitation_type"),
        ),
    }

    if key in KNOWN_SENSORS:
        return KNOWN_SENSORS[key]

    # Fallback for unknown keys
    return LMUWeatherSensorEntityDescription(
        key=key,
        name=key.replace("_", " ").title(),
        value_fn=lambda data, k=key: data.get(k),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LMUWeatherConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LMU Weather sensors based on a config entry."""
    coordinator = entry.runtime_data

    if coordinator.data:
        entities = [
            LMUWeatherSensor(coordinator, _build_sensor_description(key), entry.entry_id)
            for key in coordinator.data
        ]
        async_add_entities(entities)


class LMUWeatherSensor(CoordinatorEntity[LMUWeatherDataUpdateCoordinator], SensorEntity):
    """Representation of a LMU Weather Sensor."""

    entity_description: LMUWeatherSensorEntityDescription
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LMUWeatherDataUpdateCoordinator,
        description: LMUWeatherSensorEntityDescription,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": coordinator.station_info["name"],
            "manufacturer": "Meteorological Institute Munich (LMU)",
            "model": "Station " + coordinator.station_info["name"],
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)
