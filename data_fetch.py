"""
data_fetch.py  —  Papilio AI Market Entry Intelligence Engine
---------------------------------------------------------
Fetches real economic data from the World Bank Open Data API.

Every returned DataPoint:
  {
    "key":       str,
    "indicator": str,
    "label":     str,
    "value":     float | None,
    "year":      str   | None,
    "source":    str,
    "url":       str,
    "status":    "ok" | "unavailable" | "error",
    "error_msg": str | None
  }

Rules:
  - value is None  →  status is "unavailable" or "error"
  - value is float →  status is "ok"
  - No fallback values. No estimates. No invented data.
"""

import requests
from datetime import datetime
from typing import Optional

WB_BASE   = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
WB_PARAMS = {"format": "json", "mrv": 5, "per_page": 5}
RETRIEVED_AT = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

INDICATORS = {
    "gdp_usd":              ("NY.GDP.MKTP.CD",       "GDP, current USD"),
    "gdp_growth_pct":       ("NY.GDP.MKTP.KD.ZG",    "GDP growth, annual %"),
    "gdp_per_capita_usd":   ("NY.GDP.PCAP.CD",        "GDP per capita, current USD"),
    "fdi_pct_gdp":          ("BX.KLT.DINV.WD.GD.ZS", "FDI net inflows, % of GDP"),
    "inflation_pct":        ("FP.CPI.TOTL.ZG",        "Inflation, consumer prices, annual %"),
    "military_exp_pct_gdp": ("MS.MIL.XPND.GD.ZS",    "Military expenditure, % of GDP (SIPRI via World Bank)"),
    "military_exp_usd":     ("MS.MIL.XPND.CD",        "Military expenditure, current USD (SIPRI via World Bank)"),
    "population":           ("SP.POP.TOTL",            "Population, total"),
    "rule_of_law_rank":     ("RL.PER.RNK",             "Rule of Law, percentile rank 0-100 (WB Governance Indicators)"),
    "corruption_control":   ("CC.PER.RNK",             "Control of Corruption, percentile rank 0-100 (WB Governance Indicators)"),
    "political_stability":  ("PV.PER.RNK",             "Political Stability, percentile rank 0-100 (WB Governance Indicators)"),
    "exports_pct_gdp":      ("NE.EXP.GNFS.ZS",        "Exports of goods and services, % of GDP"),
}


def _make_datapoint(key, indicator, label, value, year, country_code, status, error_msg=None):
    return {
        "key":       key,
        "indicator": indicator,
        "label":     label,
        "value":     round(float(value), 4) if value is not None else None,
        "year":      year,
        "source":    f"World Bank Open Data — {label} ({indicator})",
        "url":       f"https://data.worldbank.org/indicator/{indicator}?locations={country_code.upper()}",
        "status":    status,
        "error_msg": error_msg,
    }


def _fetch_indicator(country_code: str, key: str) -> dict:
    """Fetches one indicator. Never raises — errors captured in returned dict."""
    indicator, label = INDICATORS[key]
    url = WB_BASE.format(country=country_code.lower(), indicator=indicator)
    resp = None

    try:
        resp = requests.get(url, params=WB_PARAMS, timeout=12)
        resp.raise_for_status()
        payload = resp.json()

        if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
            return _make_datapoint(key, indicator, label, None, None, country_code,
                                   "unavailable", "API returned empty data array")

        for entry in payload[1]:
            raw = entry.get("value")
            if raw is not None:
                try:
                    return _make_datapoint(key, indicator, label,
                                           float(raw), str(entry.get("date", "unknown")),
                                           country_code, "ok")
                except (TypeError, ValueError):
                    continue

        return _make_datapoint(key, indicator, label, None, None, country_code,
                               "unavailable", "All returned values are null")

    except requests.exceptions.Timeout:
        return _make_datapoint(key, indicator, label, None, None, country_code,
                               "error", "Request timed out after 12s")
    except requests.exceptions.ConnectionError as e:
        return _make_datapoint(key, indicator, label, None, None, country_code,
                               "error", f"Connection error: {str(e)[:120]}")
    except requests.exceptions.HTTPError as e:
        code = resp.status_code if resp is not None else "?"
        return _make_datapoint(key, indicator, label, None, None, country_code,
                               "error", f"HTTP {code}: {str(e)[:80]}")
    except (ValueError, KeyError, IndexError) as e:
        return _make_datapoint(key, indicator, label, None, None, country_code,
                               "error", f"Parse error: {str(e)[:120]}")
    except Exception as e:
        return _make_datapoint(key, indicator, label, None, None, country_code,
                               "error", f"Unexpected: {str(e)[:120]}")


def get_country_profile(country_code: str, verbose: bool = True) -> dict:
    """
    Fetches all configured indicators for one country.
    Returns a structured profile dict — never crashes.
    """
    cc = country_code.upper().strip()
    if verbose:
        print(f"  Fetching World Bank data for: {cc}")

    indicators = {}
    available = 0
    unavailable = 0

    for key in INDICATORS:
        dp = _fetch_indicator(cc, key)
        indicators[key] = dp
        if dp["status"] == "ok":
            available += 1
            if verbose:
                print(f"    OK  {key}: {dp['value']:,} ({dp['year']})")
        else:
            unavailable += 1
            if verbose:
                print(f"    --  {key}: {dp['status'].upper()} — {dp['error_msg']}")

    if verbose:
        print(f"  -> {available} available, {unavailable} unavailable\n")

    return {
        "country_code":      cc,
        "retrieved_at":      RETRIEVED_AT,
        "data_source":       "World Bank Open Data API (https://data.worldbank.org)",
        "indicators":        indicators,
        "available_count":   available,
        "unavailable_count": unavailable,
    }


def format_for_prompt(profile: dict) -> str:
    """
    Converts a country profile into a strict text block for the AI prompt.
    Every available value: indicator, value, year, source, URL.
    Every missing value: explicitly marked DATA NOT AVAILABLE.
    """
    cc    = profile["country_code"]
    ts    = profile["retrieved_at"]
    avl   = profile["available_count"]
    unavl = profile["unavailable_count"]

    lines = [
        "=" * 64,
        f"VERIFIED ECONOMIC DATA — {cc}",
        f"Retrieved: {ts} (live API call, not cached)",
        f"Source: {profile['data_source']}",
        f"Coverage: {avl} available / {unavl} unavailable",
        "-" * 64,
        "AVAILABLE VALUES (cite these exactly as written):",
    ]

    unavailable_lines = []

    for key, dp in profile["indicators"].items():
        if dp["status"] == "ok":
            lines.append(
                f"  [{dp['indicator']}] {dp['label']}: "
                f"{dp['value']:,} | Year: {dp['year']} | "
                f"Source: {dp['source']} | URL: {dp['url']}"
            )
        else:
            unavailable_lines.append(
                f"  [{dp['indicator']}] {dp['label']}: "
                f"DATA NOT AVAILABLE ({dp['status'].upper()})"
            )

    if not any(dp["status"] == "ok" for dp in profile["indicators"].values()):
        lines.append("  (no data available — all indicators failed)")

    lines.append("")
    lines.append("UNAVAILABLE (do not estimate, substitute, or omit the gap):")
    lines.extend(unavailable_lines if unavailable_lines else ["  (none — full coverage)"])
    lines.append("-" * 64)
    lines.append(
        "RULE: Use ONLY values from AVAILABLE VALUES above. "
        "For anything under UNAVAILABLE, write 'data not available' in your output. "
        "Do not invent, estimate, or use external knowledge to fill gaps."
    )
    lines.append("=" * 64)

    return "\n".join(lines)

def fetch_all_data(country_code):
    profile = get_country_profile(country_code, verbose=False)
    formatted = format_for_prompt(profile)
    return formatted