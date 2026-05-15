def fetch(settings, format_lines, get_rows, get_cols):
    import math
    import re
    import time
    from datetime import datetime, timezone

    import requests

    # Keep provider polling state inside this plugin so settings changes
    # can force an immediate refresh without server-side cache hooks.
    state = getattr(fetch, "_state", None)
    if state is None:
        state = {
            "last_sig": None,
            "last_polled_at": 0.0,
            "flights": [],
            "last_error_provider": None,
            "last_error": None,
            "opensky_token": None,
            "opensky_token_exp": 0.0,
        }
        setattr(fetch, "_state", state)

    def _to_float(value, default):
        try:
            return float(value)
        except Exception:
            return default

    def _to_int(value, default):
        try:
            return int(value)
        except Exception:
            return default

    def _parse_lat_lon(raw):
        if not raw:
            return None
        text = str(raw).strip()
        match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", text)
        if not match:
            return None
        lat = float(match.group(1))
        lon = float(match.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
        return None

    def _resolve_location(location):
        return _parse_lat_lon(location)

    def _haversine_km(lat1, lon1, lat2, lon2):
        radius = 6371.0
        p1 = math.radians(lat1)
        p2 = math.radians(lat2)
        dp = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius * c

    def _bearing_deg(lat1, lon1, lat2, lon2):
        p1 = math.radians(lat1)
        p2 = math.radians(lat2)
        dl = math.radians(lon2 - lon1)
        y = math.sin(dl) * math.cos(p2)
        x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
        return (math.degrees(math.atan2(y, x)) + 360) % 360

    def _cardinal(deg):
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = int((deg + 22.5) // 45) % 8
        return directions[index]

    def _sanitize_callsign(value):
        if not value:
            return "UNKNOWN"
        clean = str(value).strip().upper()
        return clean if clean else "UNKNOWN"

    def _parse_timestamp(value):
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return int(value)
        text = str(value).strip()
        if not text:
            return None
        try:
            return int(float(text))
        except Exception:
            pass
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            return int(datetime.fromisoformat(text).astimezone(timezone.utc).timestamp())
        except Exception:
            return None

    def _format_altitude(altitude_m, unit):
        if altitude_m is None:
            return "A?"
        if unit == "m":
            altitude = int(round(altitude_m))
            if altitude >= 10000:
                return f"A{int(round(altitude / 1000.0))}KM"
            return f"A{altitude}M"
        altitude_ft = int(round(altitude_m * 3.28084))
        if unit == "fl":
            return f"FL{int(round(altitude_ft / 100.0))}"
        if altitude_ft >= 10000:
            return f"A{int(round(altitude_ft / 1000.0))}K"
        return f"A{altitude_ft}"

    def _format_speed(speed_ms, unit):
        if speed_ms is None:
            return "?"
        if unit == "mph":
            return f"{int(round(speed_ms * 2.23694))}MPH"
        if unit == "kmh":
            return f"{int(round(speed_ms * 3.6))}KPH"
        return f"{int(round(speed_ms * 1.94384))}KT"

    def _format_distance(distance_km, direction, unit):
        if unit == "mi":
            return f"{distance_km * 0.621371:.1f}MI {direction}".strip()
        if unit == "nm":
            return f"{distance_km * 0.539957:.1f}NM {direction}".strip()
        return f"{distance_km:.1f}KM {direction}".strip()

    def _normalize_flight(callsign, latitude, longitude, *, altitude_m=None, speed_ms=None, heading=None, on_ground=False, last_seen=None):
        if latitude is None or longitude is None:
            return None
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except Exception:
            return None
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return None
        normalized = {
            "callsign": _sanitize_callsign(callsign),
            "lat": latitude,
            "lon": longitude,
            "altitude_m": None,
            "speed_ms": None,
            "heading": None,
            "on_ground": bool(on_ground),
            "last_seen": _parse_timestamp(last_seen),
        }
        try:
            if altitude_m is not None:
                normalized["altitude_m"] = float(altitude_m)
        except Exception:
            pass
        try:
            if speed_ms is not None:
                normalized["speed_ms"] = float(speed_ms)
        except Exception:
            pass
        try:
            if heading is not None:
                normalized["heading"] = float(heading)
        except Exception:
            pass
        return normalized

    def _get_opensky_token(client_id, client_secret):
        now = time.time()
        if state.get("opensky_token") and now < float(state.get("opensky_token_exp", 0.0)):
            return state.get("opensky_token")

        response = requests.post(
            "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise ValueError("OpenSky token response missing access_token")
        expires_in = int(payload.get("expires_in", 1800))
        state["opensky_token"] = token
        state["opensky_token_exp"] = now + max(60, expires_in - 30)
        return token

    def _fetch_opensky(lamin, lomin, lamax, lomax, client_id, client_secret):
        headers = None
        if client_id and client_secret:
            token = _get_opensky_token(client_id, client_secret)
            headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://opensky-network.org/api/states/all",
            params={
                "lamin": round(lamin, 5),
                "lomin": round(lomin, 5),
                "lamax": round(lamax, 5),
                "lomax": round(lomax, 5),
            },
            headers=headers,
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        flights = []
        for state in payload.get("states", []) or []:
            if len(state) < 17:
                continue
            altitude_m = state[13] if len(state) > 13 and state[13] is not None else None
            if altitude_m is None:
                altitude_m = state[7] if len(state) > 7 and state[7] is not None else None
            flight = _normalize_flight(
                state[1],
                state[6],
                state[5],
                altitude_m=altitude_m,
                speed_ms=state[9] if len(state) > 9 else None,
                heading=state[10] if len(state) > 10 else None,
                on_ground=state[8] if len(state) > 8 else False,
                last_seen=state[4] if len(state) > 4 else None,
            )
            if flight:
                flights.append(flight)
        return flights

    def _fetch_flightaware(lamin, lomin, lamax, lomax, api_key):
        query = f'-latlong "{lamin:.5f} {lomin:.5f} {lamax:.5f} {lomax:.5f}"'
        response = requests.get(
            "https://aeroapi.flightaware.com/aeroapi/flights/search",
            params={"query": query, "max_pages": 1},
            headers={"x-apikey": api_key},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        flights = []
        for item in payload.get("flights", []) or []:
            pos = item.get("last_position") or {}
            altitude_ft = pos.get("altitude")
            speed_kt = pos.get("groundspeed")
            flight = _normalize_flight(
                item.get("ident_icao") or item.get("ident_iata") or item.get("ident") or item.get("registration"),
                pos.get("latitude"),
                pos.get("longitude"),
                altitude_m=(altitude_ft * 0.3048) if altitude_ft is not None else None,
                speed_ms=(speed_kt / 1.94384) if speed_kt is not None else None,
                heading=pos.get("heading"),
                on_ground=False,
                last_seen=pos.get("timestamp") or item.get("last_position_time"),
            )
            if flight:
                flights.append(flight)
        return flights

    def _fetch_airlabs(lamin, lomin, lamax, lomax, api_key):
        response = requests.get(
            "https://airlabs.co/api/v9/flights",
            params={
                "api_key": api_key,
                "bbox": f"{lamin:.5f},{lomin:.5f},{lamax:.5f},{lomax:.5f}",
                "_fields": "lat,lng,alt,dir,speed,updated,flight_iata,flight_icao,flight_number,reg_number,status",
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        items = payload.get("response") or payload.get("data") or []
        flights = []
        for item in items:
            speed_kmh = item.get("speed")
            flight = _normalize_flight(
                item.get("flight_iata") or item.get("flight_icao") or item.get("flight_number") or item.get("reg_number"),
                item.get("lat"),
                item.get("lng"),
                altitude_m=item.get("alt"),
                speed_ms=(speed_kmh / 3.6) if speed_kmh is not None else None,
                heading=item.get("dir"),
                on_ground=str(item.get("status", "")).lower() in ("landed", "scheduled", "ground"),
                last_seen=item.get("updated"),
            )
            if flight:
                flights.append(flight)
        return flights

    def _fetch_aviationstack(api_key):
        response = requests.get(
            "https://api.aviationstack.com/v1/flights",
            params={
                "access_key": api_key,
                "flight_status": "active",
                "limit": 100,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        flights = []
        for item in payload.get("data", []) or []:
            live = item.get("live") or {}
            flight_info = item.get("flight") or {}
            aircraft = item.get("aircraft") or {}
            speed_kmh = live.get("speed_horizontal")
            flight = _normalize_flight(
                flight_info.get("iata") or flight_info.get("icao") or flight_info.get("number") or aircraft.get("registration"),
                live.get("latitude"),
                live.get("longitude"),
                altitude_m=live.get("altitude"),
                speed_ms=(speed_kmh / 3.6) if speed_kmh is not None else None,
                heading=live.get("direction"),
                on_ground=live.get("is_ground", False),
                last_seen=live.get("updated"),
            )
            if flight:
                flights.append(flight)
        return flights

    def _extract_fr24_items(payload):
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        for key in ("data", "aircraft", "flights", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                return [v for v in value.values() if isinstance(v, dict)]
        return [
            value
            for value in payload.values()
            if isinstance(value, dict) and any(k in value for k in ("lat", "lng", "lon", "latitude", "longitude"))
        ]

    def _fetch_flightradar24(lamin, lomin, lamax, lomax, api_key, api_host):
        host = (api_host or "flightradar24-com.p.rapidapi.com").strip()
        response = requests.get(
            f"https://{host}/flights/list-in-boundary",
            params={
                "bl_lat": f"{lamin:.5f}",
                "bl_lng": f"{lomin:.5f}",
                "tr_lat": f"{lamax:.5f}",
                "tr_lng": f"{lomax:.5f}",
            },
            headers={
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": host,
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        flights = []
        for item in _extract_fr24_items(payload):
            speed_kt = item.get("speed") or item.get("ground_speed") or item.get("groundSpeed")
            altitude_ft = item.get("alt") or item.get("altitude")
            flight = _normalize_flight(
                item.get("callsign") or item.get("flight") or item.get("flight_number") or item.get("icao") or item.get("iata") or item.get("registration"),
                item.get("lat") or item.get("latitude"),
                item.get("lng") or item.get("lon") or item.get("longitude"),
                altitude_m=(altitude_ft * 0.3048) if altitude_ft is not None else None,
                speed_ms=(speed_kt / 1.94384) if speed_kt is not None else None,
                heading=item.get("track") or item.get("heading"),
                on_ground=str(item.get("status", "")).lower() in ("landed", "scheduled", "ground"),
                last_seen=item.get("timestamp") or item.get("last_seen") or item.get("time"),
            )
            if flight:
                flights.append(flight)
        return flights

    def _provider_requirements(provider):
        return {
            "opensky": [],
            "flightaware": [("flightaware_api_key", "FLIGHTAWARE")],
            "flightradar24": [("flightradar24_api_key", "FR24 KEY")],
            "airlabs": [("airlabs_api_key", "AIRLABS KEY")],
            "aviationstack": [("aviationstack_api_key", "AVSTACK KEY")],
        }.get(provider, [])

    def _provider_tag(provider):
        return {
            "opensky": "OPENSKY",
            "flightaware": "FLTAWARE",
            "flightradar24": "FR24",
            "airlabs": "AIRLABS",
            "aviationstack": "AVSTACK",
        }.get(provider, "API")

    def _extract_error_text(response):
        if not response:
            return ""
        try:
            payload = response.json()
            if isinstance(payload, dict):
                for key in ("error", "message", "reason", "detail"):
                    if key in payload and payload[key]:
                        return str(payload[key])
            return str(payload)
        except Exception:
            return (response.text or "").strip()

    def _error_pages(provider, err, dwell_repeat):
        tag = _provider_tag(provider)
        if isinstance(err, requests.Timeout):
            return [format_lines("PLANES", "API TIMEOUT", tag)] * dwell_repeat
        if isinstance(err, requests.ConnectionError):
            return [format_lines("PLANES", "CONNECTION ERR", tag)] * dwell_repeat

        status = None
        body_text = ""
        if isinstance(err, requests.HTTPError):
            response = getattr(err, "response", None)
            if response is not None:
                status = response.status_code
                body_text = _extract_error_text(response).lower()

        if status in (401, 403):
            return [format_lines("PLANES", "AUTH ERROR", f"{tag} KEY")] * dwell_repeat

        if status == 429 or any(token in body_text for token in ("rate", "limit", "quota", "usage", "too many")):
            return [format_lines("PLANES", "RATE LIMITED", tag)] * dwell_repeat

        if status == 402:
            return [format_lines("PLANES", "PLAN LIMIT", tag)] * dwell_repeat

        if status in (500, 502, 503, 504):
            return [format_lines("PLANES", "API OFFLINE", tag)] * dwell_repeat

        if status is not None:
            return [format_lines("PLANES", f"API ERR {status}", tag)] * dwell_repeat

        return [format_lines("PLANES", "DATA ERROR", "TRY AGAIN")] * dwell_repeat

    def _fetch_provider_flights(provider, lamin, lomin, lamax, lomax):
        if provider == "opensky":
            return _fetch_opensky(
                lamin,
                lomin,
                lamax,
                lomax,
                str(settings.get("opensky_client_id", "")).strip(),
                str(settings.get("opensky_client_secret", "")).strip(),
            )
        if provider == "flightaware":
            return _fetch_flightaware(lamin, lomin, lamax, lomax, str(settings.get("flightaware_api_key", "")).strip())
        if provider == "flightradar24":
            return _fetch_flightradar24(
                lamin,
                lomin,
                lamax,
                lomax,
                str(settings.get("flightradar24_api_key", "")).strip(),
                str(settings.get("flightradar24_api_host", "")).strip(),
            )
        if provider == "airlabs":
            return _fetch_airlabs(lamin, lomin, lamax, lomax, str(settings.get("airlabs_api_key", "")).strip())
        if provider == "aviationstack":
            return _fetch_aviationstack(str(settings.get("aviationstack_api_key", "")).strip())
        raise ValueError(f"Unsupported source: {provider}")

    base_loop_seconds = 4.0

    location_raw = settings.get("location", "42.3601,-71.0589")
    radius_value = max(
        1.0,
        _to_float(settings.get("radius", settings.get("radius_km", 100)), 100.0),
    )
    radius_unit = str(settings.get("radius_unit", "mi")).lower()
    max_results = max(1, min(10, _to_int(settings.get("max_results", "9"), 9)))
    units_preset = str(settings.get("units_preset", "aviation")).lower()
    distance_unit = str(settings.get("distance_unit", "nm")).lower()
    altitude_unit = str(settings.get("altitude_unit", "fl")).lower()
    speed_unit = str(settings.get("speed_unit", "kt")).lower()
    dwell_seconds = max(1.0, min(30.0, _to_float(settings.get("dwell_seconds", "15"), 15.0)))
    polling_seconds = max(15.0, min(3600.0, _to_float(settings.get("polling_rate", "240"), 240.0)))
    data_source = str(settings.get("data_source", "opensky")).strip().lower()
    dwell_repeat = max(1, int(round(dwell_seconds / base_loop_seconds)))

    if units_preset == "aviation":
        distance_unit = "nm"
        altitude_unit = "fl"
        speed_unit = "kt"
    elif units_preset == "metric":
        distance_unit = "km"
        altitude_unit = "m"
        speed_unit = "kmh"
    elif units_preset == "imperial":
        distance_unit = "mi"
        altitude_unit = "ft"
        speed_unit = "mph"

    if distance_unit not in ("km", "mi", "nm"):
        distance_unit = "km"
    if radius_unit not in ("mi", "km"):
        radius_unit = "mi"
    if altitude_unit not in ("ft", "fl", "m"):
        altitude_unit = "ft"
    if speed_unit not in ("kt", "mph", "kmh"):
        speed_unit = "kt"
    if data_source not in ("opensky", "flightaware", "flightradar24", "airlabs", "aviationstack"):
        data_source = "opensky"

    radius_km = radius_value * 1.609344 if radius_unit == "mi" else radius_value
    radius_km = max(10.0, min(250.0, radius_km))

    center = _resolve_location(location_raw)
    if not center:
        return [format_lines("PLANES", "BAD LOCATION", "USE LAT,LON")] * dwell_repeat

    for key, label in _provider_requirements(data_source):
        if not str(settings.get(key, "")).strip():
            return [format_lines("PLANES", "ADD API KEY", label)] * dwell_repeat

    lat, lon = center
    delta_lat = radius_km / 111.0
    cos_lat = math.cos(math.radians(lat))
    delta_lon = radius_km / max(111.0 * max(cos_lat, 0.01), 1.0)

    lamin = max(-90.0, lat - delta_lat)
    lamax = min(90.0, lat + delta_lat)
    lomin = max(-180.0, lon - delta_lon)
    lomax = min(180.0, lon + delta_lon)

    settings_sig = (
        location_raw,
        radius_value,
        radius_unit,
        max_results,
        units_preset,
        distance_unit,
        altitude_unit,
        speed_unit,
        dwell_seconds,
        polling_seconds,
        data_source,
        str(settings.get("opensky_client_id", "")).strip(),
        str(settings.get("opensky_client_secret", "")).strip(),
        str(settings.get("flightaware_api_key", "")).strip(),
        str(settings.get("flightradar24_api_key", "")).strip(),
        str(settings.get("flightradar24_api_host", "")).strip(),
        str(settings.get("airlabs_api_key", "")).strip(),
        str(settings.get("aviationstack_api_key", "")).strip(),
    )

    now_ts = time.time()
    sig_changed = settings_sig != state["last_sig"]
    due_for_poll = (now_ts - state["last_polled_at"]) >= polling_seconds
    need_poll = sig_changed or due_for_poll or (not state["flights"] and state["last_error"] is None)

    if need_poll:
        try:
            state["flights"] = _fetch_provider_flights(data_source, lamin, lomin, lamax, lomax)
            state["last_error_provider"] = None
            state["last_error"] = None
            state["last_polled_at"] = now_ts
            state["last_sig"] = settings_sig
        except Exception as err:
            state["last_error_provider"] = data_source
            state["last_error"] = err
            state["last_polled_at"] = now_ts
            state["last_sig"] = settings_sig

    if state["last_error"] and not state["flights"]:
        return _error_pages(state["last_error_provider"] or data_source, state["last_error"], dwell_repeat)

    flights = state["flights"]

    now = int(time.time())
    nearby = []
    for flight in flights:
        if flight["on_ground"]:
            continue
        if flight["last_seen"] and (now - int(flight["last_seen"]) > 300):
            continue

        dist_km = _haversine_km(lat, lon, flight["lat"], flight["lon"])
        if dist_km > radius_km:
            continue

        bearing = _bearing_deg(lat, lon, flight["lat"], flight["lon"])
        nearby.append({
            "flight": flight,
            "distance": dist_km,
            "direction": _cardinal(bearing),
        })

    if not nearby:
        radius_text = f"{radius_value:.0f}{radius_unit.upper()}"
        return [format_lines("PLANES", "NONE NEARBY", f"RAD {radius_text}")] * dwell_repeat

    nearby.sort(key=lambda item: item["distance"])
    pages = []
    for item in nearby[:max_results]:
        flight = item["flight"]
        distance = _format_distance(item["distance"], item["direction"], distance_unit)
        alt = _format_altitude(flight["altitude_m"], altitude_unit)
        speed = _format_speed(flight["speed_ms"], speed_unit)
        page = format_lines(flight["callsign"], distance, f"{alt} {speed}")
        pages.extend([page] * dwell_repeat)

    return pages


def trigger(settings, conditions):
    """Fire when aircraft matching the configured filter appear overhead."""
    import math, requests

    filter_type = conditions.get('filter', 'any')
    keyword = conditions.get('keyword', '').upper().strip()

    state = getattr(trigger, '_state', None)
    if state is None:
        state = {'seen_callsigns': set()}
        setattr(trigger, '_state', state)

    # Reuse fetch state's cached flights if available (avoids extra API calls)
    fetch_state = getattr(fetch, '_state', None)
    flights = fetch_state['flights'] if fetch_state and fetch_state.get('flights') else []

    if not flights:
        # No cached data — do a quick OpenSky poll
        try:
            loc = settings.get('location', '41.97,-87.90')
            lat, lon = [float(x.strip()) for x in loc.split(',')]
            radius_km = 50
            d = radius_km / 111.0
            r = requests.get(
                'https://opensky-network.org/api/states/all',
                params={'lamin': lat-d, 'lomin': lon-d, 'lamax': lat+d, 'lomax': lon+d},
                timeout=8
            ).json()
            flights = [{'callsign': (s[1] or '').strip().upper()} for s in (r.get('states') or [])]
        except Exception:
            return False

    new_found = False
    for f in flights:
        cs = f.get('callsign', '')
        if not cs:
            continue
        if filter_type == 'keyword' and keyword and keyword not in cs:
            continue
        if cs not in state['seen_callsigns']:
            state['seen_callsigns'].add(cs)
            new_found = True

    # Prune seen set to avoid unbounded growth
    if len(state['seen_callsigns']) > 500:
        state['seen_callsigns'] = set(list(state['seen_callsigns'])[-200:])

    return new_found