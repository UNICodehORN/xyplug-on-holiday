#!/usr/bin/env python3

def main():
    import sys
    import json
    from pathlib import Path
    from datetime import datetime
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    import requests

    DEFAULT_TIMEZONE = "UTC"
    DEFAULT_CACHE_DIR = Path("/tmp")
    DEFAULT_COUNTRY = "DE"
    DEFAULT_SUBDIVISION = "DE-NW"

    data = json.load(sys.stdin)
    response = {"xy": 1, "items": []}
    year_cache = {}

    def load_holidays(year: int, country: str, subdivision: str, cache_dir: Path) -> set:
        safe_country = country.replace("/", "_")
        safe_subdivision = subdivision.replace("/", "_")
        cache_file = cache_dir / f"holidays_{year}_{safe_country}_{safe_subdivision}.json"

        if cache_file.exists():
            try:
                return set(json.loads(cache_file.read_text(encoding="utf-8")))
            except Exception:
                pass

        url = (
            f"https://openholidaysapi.org/PublicHolidays?"
            f"countryIsoCode={country}"
            f"&validFrom={year}-01-01"
            f"&validTo={year}-12-31"
            f"&languageIsoCode=DE"
            f"&subdivisionCode={subdivision}"
        )

        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            holidays = {h["startDate"] for h in r.json()}
            cache_file.write_text(json.dumps(list(holidays)), encoding="utf-8")
            return holidays
        except Exception as e:
            print(f"Holiday API error: {e}", file=sys.stderr)
            return set()

    for item in data.get("items", []):
        params = item.get("params", {})

        tz_name = item.get("timezone", DEFAULT_TIMEZONE)
        try:
            tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            tz = ZoneInfo(DEFAULT_TIMEZONE)

        now_ts = int(item.get("now", 0))
        local_dt = datetime.fromtimestamp(now_ts, tz=tz)
        year = local_dt.year
        date_str = local_dt.strftime("%Y-%m-%d")

        cache_dir = Path(params.get("cachingDir", DEFAULT_CACHE_DIR))
        country = params.get("countryIsoCode", DEFAULT_COUNTRY)
        subdivision = params.get("subdivisionCode", DEFAULT_SUBDIVISION)

        cache_key = (year, country, subdivision)
        if cache_key not in year_cache:
            year_cache[cache_key] = load_holidays(year, country, subdivision, cache_dir)

        holidays = year_cache[cache_key]
        is_holiday = date_str in holidays

        if is_holiday:
            launch = bool(params.get("executeOnHoliday", False))
        else:
            launch = True

        response["items"].append({"launch": launch})

    print(json.dumps(response))


if __name__ == "__main__":
    main()
