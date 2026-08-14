"""Tests for the LMU weather HTML parser.

Imports parser.py directly by file path instead of via the
custom_components.lmu_weather package, so these tests don't require the
full `homeassistant` package to be installed (only bs4/pytest).
"""
import importlib.util
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

_PARSER_PATH = Path(__file__).parent.parent / "custom_components" / "lmu_weather" / "parser.py"
_spec = importlib.util.spec_from_file_location("lmu_weather_parser", _PARSER_PATH)
_parser_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parser_module)
parse_lmu_weather_html = _parser_module.parse_lmu_weather_html

LEGACY_FIXTURE = (Path(__file__).parent / "fixtures" / "messung.html").read_text(encoding="utf-8")
STADT_FIXTURE = (Path(__file__).parent / "fixtures" / "messwerte_stadt.html").read_text(encoding="utf-8")
GARCHING_FIXTURE = (Path(__file__).parent / "fixtures" / "messwerte_garching.html").read_text(encoding="utf-8")


@pytest.fixture
def legacy_data() -> dict:
    return parse_lmu_weather_html(LEGACY_FIXTURE)


@pytest.fixture
def stadt_data() -> dict:
    return parse_lmu_weather_html(STADT_FIXTURE)


@pytest.fixture
def garching_data() -> dict:
    return parse_lmu_weather_html(GARCHING_FIXTURE)


def test_legacy_parser(legacy_data):
    assert legacy_data["measured_at"] == datetime(2026, 8, 14, 11, 47, tzinfo=ZoneInfo("Europe/Berlin"))
    assert legacy_data["temp_2_0m"] == 27.9
    assert legacy_data["soil_temp_50cm"] == 23.5
    assert legacy_data["global_radiation"] == 792.6
    assert legacy_data["diffuse_radiation"] == 74.7
    assert legacy_data["sunshine_duration"] == "5 Std. 17 Min."
    assert legacy_data["uv_index"] == 5.8
    assert legacy_data["pressure_station"] == 960.9
    assert legacy_data["precipitation_today"] == 0.005
    assert legacy_data["precipitation_type"] is None


def test_real_live_stadt_parser(stadt_data):
    # Verifying fixes for all reported Stadt bugs against live HTML fixture
    assert stadt_data["global_radiation"] == 859.0
    assert stadt_data["diffuse_radiation"] == 73.9
    assert stadt_data["uv_index"] == 6.5
    assert stadt_data["precipitation_current"] == 0.0
    assert stadt_data["precipitation_today"] == 0.005
    assert stadt_data["precipitation_type"] is None
    assert stadt_data["soil_temp_50cm"] == 23.5
    assert stadt_data["soil_temp_2cm"] == 22.3


def test_stadt_parser_has_no_duplicate_legacy_alias_keys(stadt_data):
    # Height-profile values must only exist under their height-suffixed key
    # (temp_2_0m), not also duplicated under a bare legacy key (temp_2m) --
    # sensor.py creates one entity per dict key, so a duplicate key means a
    # duplicate sensor entity in Home Assistant.
    for key in ("temp_2m", "temp_30m", "humidity_2m", "humidity_30m",
                "wet_temp_2m", "wet_temp_30m", "dewpoint_2m", "dewpoint_30m"):
        assert key not in stadt_data


def test_real_live_garching_parser(garching_data):
    # Verifying fixes for all reported Garching bugs against live HTML fixture
    assert garching_data["pressure_station"] == 965.4
    assert garching_data["sunshine_duration"] == "0 Min."
    assert garching_data["albedo"] == 16.8
    assert garching_data["reflected_radiation"] == 144.7
    assert garching_data["temp_50_0m"] == 28.4
    assert garching_data["wind_speed_50_0m"] == 3.1
    assert garching_data["soil_temp_2cm"] == 26.9


def test_precipitation_type_real_value_is_kept():
    html = LEGACY_FIXTURE.replace("------", "Regen")
    parsed = parse_lmu_weather_html(html)
    assert parsed["precipitation_type"] == "Regen"


def test_empty_html_returns_empty_dict():
    assert parse_lmu_weather_html("<html><body>nothing here</body></html>") == {}
