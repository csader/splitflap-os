"""Resolve the configured global location to coordinates, country and currency
(keyless: Nominatim).

This is the single place the app geocodes the configured location. Both the weather
helper and the ``get_location`` helper need the *same* location, so both go through
``coordinates()`` here — cached, one Nominatim lookup instead of one per caller. It
lets currency/holiday apps key off *where you are* rather than your language (the
language can't tell France (EUR) from Canada (CAD) or Switzerland (CHF)).
"""

import re

# Catalog globals this helper draws on (named in the app dialog's "also uses" hint).
GLOBAL_KEYS = ["location_precise", "zip_code"]

_UA = {"User-Agent": "splitflap-os/1.0"}
_geo_cache: dict = {}    # rounded (lat, lon) -> {"country", "subdivision"}
_coord_cache: dict = {}  # geocode query string -> (lat, lon, CITY)


def _currency_for(country):
    """ISO 4217 currency for an ISO 3166 country, from babel's CLDR data (a project
    dependency). Returns None if unknown — callers then fall back to the language's
    default currency (i18n.base_currency)."""
    if not country:
        return None
    try:
        from babel.numbers import get_territory_currencies
        cur = get_territory_currencies(country.upper())   # current tender per CLDR
        return cur[0] if cur else None
    except Exception:
        return None


def coordinates(settings):
    """``(lat, lon, CITY)`` for the configured location: the precise coordinates if
    set, else a geocode of the ZIP/postcode/city. Returns ``None`` when nothing is
    configured. The forward geocode is cached, so weather and get_location share it."""
    lat = str(settings.get("location_lat", "") or "").strip()
    lon = str(settings.get("location_lon", "") or "").strip()
    name = str(settings.get("location_name", "") or "").strip()
    if lat and lon:
        try:
            city = name.split(",")[0].strip().upper() if name else "LOCATION"
            return float(lat), float(lon), city
        except ValueError:
            pass
    query = str(settings.get("zip_code", "") or "").strip()
    if not query:
        return None
    if query in _coord_cache:
        return _coord_cache[query]
    try:
        import requests
        params = {"q": query, "format": "json", "limit": 1, "addressdetails": 1}
        if re.fullmatch(r"\d{5}", query):      # a US ZIP — 02118 also exists abroad
            params["countrycodes"] = "us"
        geo = requests.get("https://nominatim.openstreetmap.org/search",
                           params=params, headers=_UA, timeout=6).json()
        if geo:
            addr = geo[0].get("address", {})
            city = (addr.get("city") or addr.get("town") or addr.get("village")
                    or addr.get("municipality") or addr.get("county")
                    or geo[0].get("display_name", query).split(",")[0]).strip().upper()
            result = (float(geo[0]["lat"]), float(geo[0]["lon"]), city)
            _coord_cache[query] = result
            return result
    except Exception:
        pass
    return None


def _geo(settings):
    """Reverse-geocode the configured location to ``{country, subdivision}``, cached.
    subdivision is the ISO 3166-2 code (e.g. 'CA-QC' for Quebec) or None."""
    coords = coordinates(settings)
    if not coords:
        return {"country": None, "subdivision": None}
    lat, lon, _city = coords
    key = (round(lat, 2), round(lon, 2))
    if key in _geo_cache:
        return _geo_cache[key]
    out = {"country": None, "subdivision": None}
    try:
        import requests
        r = requests.get("https://nominatim.openstreetmap.org/reverse",
                         params={"lat": lat, "lon": lon, "format": "json", "zoom": 5},
                         headers=_UA, timeout=6).json()
        addr = r.get("address") or {}
        out["country"] = str(addr.get("country_code") or "").upper()[:2] or None
        sub = str(addr.get("ISO3166-2-lvl4") or addr.get("ISO3166-2-lvl6") or "").upper()
        out["subdivision"] = sub or None
        if out["country"]:
            _geo_cache[key] = out
    except Exception:
        pass
    return out


def country(settings):
    """ISO country code for the configured location (reverse-geocoded, cached)."""
    return _geo(settings).get("country")


def resolve(settings) -> dict:
    """{ok, country, subdivision, currency} for the configured location. ok is False
    (values None) when there's no location set or the lookup failed."""
    g = _geo(settings)
    cc = g.get("country")
    return {"ok": bool(cc), "country": cc, "subdivision": g.get("subdivision"),
            "currency": _currency_for(cc)}
