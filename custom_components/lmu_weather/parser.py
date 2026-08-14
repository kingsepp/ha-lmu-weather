"""Parser for LMU Weather HTML pages (both legacy messung.php and new Quicklooks HTML5)."""
from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup, Tag


def parse_lmu_weather_html(html_content: str) -> dict[str, Any]:
    """Parse LMU weather HTML page content into structured dictionary."""
    soup = BeautifulSoup(html_content, "html.parser")
    data: dict[str, Any] = {}

    # 1. Timestamp
    full_text = soup.get_text(" ", strip=True)
    ts_match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4}\s+\d{1,2}:\d{2})", full_text)
    if ts_match:
        try:
            dt_local = datetime.strptime(ts_match.group(1), "%d.%m.%Y %H:%M").replace(
                tzinfo=ZoneInfo("Europe/Berlin")
            )
            data["measured_at"] = dt_local.astimezone(timezone.utc)
        except ValueError:
            pass

    # 2. Profilwerte (#messwerte-profilwerte)
    profil_table = soup.find("table", id="messwerte-profilwerte")
    if not profil_table:
        for t in soup.find_all("table"):
            if "Profilwerte" in t.get_text():
                profil_table = t
                break

    if profil_table:
        rows = profil_table.find_all("tr")
        if len(rows) >= 2:
            height_cols = [td.get_text(strip=True).replace(" m", "") for td in rows[1].find_all(["td", "th"])]
            if len(height_cols) >= 2 and ("Höhe" in height_cols[0] or "Höh" in height_cols[0] or _extract_float(height_cols[1]) is not None):
                heights = height_cols[1:]
                start_row = 2
            else:
                heights = ["2.0", "30.0"]
                start_row = 1

            for row in rows[start_row:]:
                cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                if not cols:
                    continue
                label = cols[0]
                values = cols[1:]
                for h, val in zip(heights, values):
                    h_clean = h.replace(".", "_")
                    if not h_clean.endswith("m"):
                        h_clean += "m"
                    key_suffix = f"_{h_clean}"
                    val_float = _extract_float(val)
                    if "Lufttemperatur" in label:
                        data[f"temp{key_suffix}"] = val_float
                    elif "Feuchttemperatur" in label:
                        data[f"wet_temp{key_suffix}"] = val_float
                    elif "Relative Feuchte" in label:
                        data[f"humidity{key_suffix}"] = val_float
                    elif "Taupunkt" in label:
                        data[f"dewpoint{key_suffix}"] = val_float
                    elif "Windgeschwindigkeit" in label:
                        data[f"wind_speed{key_suffix}"] = val_float

    # 3. Wind & Druck (#messwerte-winddruck)
    winddruck_table = soup.find("table", id="messwerte-winddruck")
    if winddruck_table:
        for row in winddruck_table.find_all("tr"):
            cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if len(cols) == 2:
                label, val = cols[0], cols[1]
                if "Windgeschwindigkeit 30 m" in label:
                    data["wind_speed_30m"] = _extract_float(val)
                elif "Windrichtung 30 m" in label:
                    data["wind_bearing_30m"] = _extract_float(val)
                elif "Luftdruck 517 m" in label or "Luftdruck 5" in label or "Luftdruck 4" in label:
                    data["pressure_station"] = _extract_float(val)
                elif "Luftdruck NN" in label:
                    data["pressure_sealevel"] = _extract_float(val)

    # 4. Niederschlag (#messwerte-niederschlag)
    niederschlag_table = soup.find("table", id="messwerte-niederschlag")
    if niederschlag_table:
        rows = niederschlag_table.find_all("tr")
        if len(rows) >= 3:
            headers = [td.get_text(" ", strip=True) for td in rows[1].find_all(["td", "th"])]
            vals = [td.get_text(strip=True) for td in rows[2].find_all(["td", "th"])]
            for h, v in zip(headers, vals):
                if "Aktuell" in h:
                    data["precipitation_current"] = _extract_float(v)
                elif "Summe" in h or "0 Uhr" in h:
                    data["precipitation_today"] = _extract_float(v)
                elif "Art" in h:
                    data["precipitation_type"] = _clean_precipitation_type(v)

    # 5. Strahlungswerte (#messwerte-strahlung)
    strahlung_table = soup.find("table", id="messwerte-strahlung")
    if not strahlung_table:
        for t in soup.find_all("table"):
            if "Strahlung" in t.get_text():
                strahlung_table = t
                break

    if strahlung_table:
        rows = strahlung_table.find_all("tr")
        for i in range(len(rows) - 1):
            headers = [td.get_text(" ", strip=True) for td in rows[i].find_all(["td", "th"])]
            vals = [td.get_text(" ", strip=True) for td in rows[i + 1].find_all(["td", "th"])]
            if len(headers) == len(vals) and any(term in "".join(headers) for term in ["Global", "Diffus", "Reflex", "Atm", "Sonnenschein", "UV"]):
                for h, v in zip(headers, vals):
                    if "Global" in h:
                        data["global_radiation"] = _extract_float(v)
                    elif "Diffus" in h:
                        data["diffuse_radiation"] = _extract_float(v)
                    elif "Reflex" in h:
                        data["reflected_radiation"] = _extract_float(v)
                    elif "Atm" in h or "Gegenstr" in h:
                        data["atmospheric_counter_radiation"] = _extract_float(v)
                    elif "Langw" in h or "Ausstr" in h:
                        data["longwave_outgoing_radiation"] = _extract_float(v)
                    elif "Sonnenschein" in h:
                        data["sunshine_duration"] = " ".join(v.split())
                    elif "UV" in h:
                        data["uv_index"] = _extract_float(v)
                    elif "Albedo" in h:
                        data["albedo"] = _extract_float(v)

    # 6. Sonstige Messwerte (#messwerte-sonstige - e.g. Garching)
    sonstige_table = soup.find("table", id="messwerte-sonstige")
    if sonstige_table:
        rows = sonstige_table.find_all("tr")
        if len(rows) >= 3:
            headers = [td.get_text(" ", strip=True) for td in rows[1].find_all(["td", "th"])]
            vals = [td.get_text(" ", strip=True) for td in rows[2].find_all(["td", "th"])]
            for h, v in zip(headers, vals):
                if "Luftdruck 4" in h or "Luftdruck 5" in h or "Luftdruck 478" in h:
                    data["pressure_station"] = _extract_float(v)
                elif "Luftdruck NN" in h:
                    data["pressure_sealevel"] = _extract_float(v)
                elif "Windrichtung" in h and "10" in h:
                    data["wind_bearing_10m"] = _extract_float(v)
                elif "Windrichtung" in h and "62" in h:
                    data["wind_bearing_62m"] = _extract_float(v)
                elif "Niederschlag" in h and "Aktuell" in h:
                    data["precipitation_current"] = _extract_float(v)
                elif "Niederschlag" in h and ("Summe" in h or "0 Uhr" in h):
                    data["precipitation_today"] = _extract_float(v)

    # 7. Bodenwerte (#messwerte-boden)
    boden_table = soup.find("table", id="messwerte-boden")
    if not boden_table:
        for t in soup.find_all("table"):
            if "Bodenwerte" in t.get_text():
                boden_table = t
                break

    if boden_table:
        rows = boden_table.find_all("tr")
        depths = []
        vals = []
        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
            if any("50 cm" in c for c in cols) or any("50cm" in c for c in cols):
                depths = [c.replace(" cm", "").replace("cm", "") for c in cols if "cm" in c or c.isdigit()]
            elif "Temperatur" in "".join(cols) or any("°C" in c for c in cols):
                vals = [c for c in cols if _extract_float(c) is not None]

        if not depths or not vals:
            all_tds = [td.get_text(strip=True) for td in boden_table.find_all(["td", "th"])]
            for td in all_tds:
                if "cm" in td:
                    depths.append(td.replace(" cm", "").replace("cm", ""))
                elif _extract_float(td) is not None and "Bodenwerte" not in td:
                    vals.append(td)

        if depths and vals:
            for d, v in zip(depths, vals):
                data[f"soil_temp_{d}cm"] = _extract_float(v)

    # Fallbacks for legacy messung.php layout
    if "pressure_station" not in data or "precipitation_current" not in data or "global_radiation" not in data:
        for table in soup.find_all("table"):
            text = table.get_text(" ", strip=True)
            if "Sonstige Messwerte" in text:
                rows = table.find_all("tr")
                if len(rows) >= 3:
                    headers = [td.get_text(" ", strip=True) for td in rows[1].find_all(["td", "th"])]
                    vals = [td.get_text(" ", strip=True) for td in rows[2].find_all(["td", "th"])]
                    for h, v in zip(headers, vals):
                        if "Luftdruck" in h and ("515" in h or "517" in h or "478" in h):
                            data.setdefault("pressure_station", _extract_float(v))
                        elif "Luftdruck" in h and "NN" in h:
                            data.setdefault("pressure_sealevel", _extract_float(v))
                        elif "Windrichtung" in h and "30" in h:
                            data.setdefault("wind_bearing_30m", _extract_float(v))
                        elif "Niederschlag" in h and "aktuell" in h.lower():
                            data.setdefault("precipitation_current", _extract_float(v))
                        elif "Niederschlag" in h and ("0 Uhr" in h or "0Uhr" in h or "summe" in h.lower()):
                            data.setdefault("precipitation_today", _extract_float(v))
                        elif "Niederschlag" in h and "art" in h.lower():
                            data.setdefault("precipitation_type", _clean_precipitation_type(v))

    return data


def _extract_float(val_str: str) -> float | None:
    """Helper to parse float from string like '28.2 °C' or '960.9 hPa'."""
    match = re.search(r"[-+]?\d*\.\d+|\d+", val_str)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def _clean_precipitation_type(val_str: str) -> str | None:
    """Clean precipitation type string."""
    cleaned = val_str.strip()
    if not cleaned or re.fullmatch(r"-+", cleaned):
        return None
    return cleaned
