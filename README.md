# LMU Weather Station

1. [Why this integration?](#1-why-this-integration)
2. [Installation](#2-installation)
    1. [HACS installation (recommended)](#option-1-hacs-installation-recommended)
    2. [Manual installation](#option-2-manual-installation)
3. [Set up a station](#3-set-up-a-station)
4. [Sensors](#4-sensors)
5. [Removal](#5-removal)
6. [Change log](#6-change-log)
7. [Development](#7-development)
8. [Credits](#8-credits)
9. [Disclaimer](#9-disclaimer)

# Quick installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=ha-lmu-weather&owner=kingsepp)
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=lmu_weather)

* go to `Settings` --> `Devices and services` --> add integration `LMU Weather Station`, pick a station, done. No credentials, no YAML.

# 1. Why this integration?

The Meteorologisches Institut München (LMU) runs two of its own weather
stations and publishes their current readings as public HTML pages, updated
every 2 minutes. There is a beta API from the LMU, but its data arrives
irregularly and with significant delay, which makes it unsuitable for
near-real-time sensors — the HTML pages are the more current source, and
there's no existing Home Assistant integration for either the API or the
HTML pages. This integration reads the HTML pages directly instead and
turns every published value into a sensor entity.

> [!IMPORTANT]
> **This is an inofficial integration and does not belong to the LMU.**
>
> **All data originates directly from the LMU's own weather stations — this
> integration does not collect, estimate, or store any data itself, it only
> parses the numbers the LMU already publishes on its website every couple
> of minutes.**
>
> **The LMU gives no guarantee about the availability of these pages; if
> the LMU changes their page layout or takes the pages down, this
> integration stops working until updated accordingly.**

Data source — the two published pages this integration polls every 2 minutes:

* Munich City (Theresienstraße 37): https://www.meteo.physik.uni-muenchen.de/~quicklooks/aktuelle_messwerte/messwerte_stadt.html
* Garching (Oskar-von-Miller-Turm): https://www.meteo.physik.uni-muenchen.de/~quicklooks/aktuelle_messwerte/messwerte_garching.html

# 2. Installation

## Option 1: HACS installation (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=ha-lmu-weather&owner=kingsepp)

Or use these steps:
* In Home Assistant go to the HACS integration (left admin menu)
* top right, click the 3 dots
* click "Custom Repositories"
* Repository: `https://github.com/kingsepp/ha-lmu-weather`
* Category: `Integration`
* click Add (bottom right), close the popup
* search for "LMU Weather Station" and click on it
* click Download (bottom right)
* Restart HA

## Option 2: Manual installation

* Copy the `custom_components/lmu_weather` folder (the folder itself, not just its contents) into your `config/custom_components/` folder.
* Restart HA

# 3. Set up a station

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=lmu_weather)

Or use these steps:
* go to `Settings` --> `Devices and services`
* click `+ ADD INTEGRATION`
* search for `LMU Weather Station` and follow the configuration flow
* pick the station you want (Munich City or Garching)

You can add the integration a second time to configure the other station —
both run side by side as separate devices, so you can compare them.

⚠️ It may take a minute for all entities to appear after adding a station.

# 4. Sensors

The sensor set is built dynamically from whatever the station's page
publishes, so it differs slightly per station. Munich City exposes 26
sensors, Garching (more measurement heights) around 63:

* Air/wet-bulb temperature, relative humidity, dew point — at every height the station measures (Munich City: 2 m & 30 m; Garching: 0.2 m up to 50 m)
* Wind speed and wind bearing
* Soil temperature at multiple depths (-2 cm to -50 cm)
* Global, diffuse, reflected and atmospheric counter radiation, longwave outgoing radiation, sunshine duration, UV index, albedo (Garching only)
* Air pressure (station level & sea level)
* Precipitation (current rate, daily total, precipitation type)
* Timestamp of the last published measurement (diagnostic sensor), so a stalled source page becomes visible instead of silently going stale

# 5. Removal

* Settings --> Devices and services --> LMU Weather Station (per station) --> the three-dot menu on the integration card --> **Delete**. This removes the config entry and all its sensor entities.
* HACS --> Integrations --> LMU Weather Station --> the three-dot menu --> **Remove**. This deletes the `custom_components/lmu_weather` files. Restart Home Assistant afterwards.

# 6. Change log

## 2026-08-14 - Version 1.0.0
* Initial release: config-flow setup, station selection (Munich City / Garching), dynamic sensor creation from whatever the station's page publishes.

# 7. Development

```bash
pip install -r requirements-test.txt  # beautifulsoup4, pytest
pytest tests/
```

The parser (`custom_components/lmu_weather/parser.py`) has no Home Assistant
imports and is tested standalone against real, saved copies of both LMU
pages in `tests/fixtures/`. The config-flow tests under `tests/config_flow/`
need the full Home Assistant test harness (`hass`/`enable_custom_integrations`
fixtures), so they only run inside a `home-assistant/core` checkout, not
with plain `pytest`.

# 8. Credits

* The LMU (Meteorologisches Institut München) for publishing this data openly.

# 9. Disclaimer

The use of this Home Assistant integration is at your own risk. It is
provided "as-is" and without any warranty regarding the accuracy,
completeness, or availability of the underlying data. This integration is
not affiliated with, endorsed by, or supported by the LMU.
