#!/usr/bin/env python3

def main():
    import sys
    import json
    from pathlib import Path
    import requests

    # Default globals
    CACHING_DIR = Path("/tmp")
    COUNTRY_ISO = "DE"
    SUBDIVISION_CODE = "DE-NW"

    data = json.load(sys.stdin)
    response = {"xy": 1, "items": []}
    year_cache = {}

    def load_holidays(year: int, country: str, subdivision: str) -> set:
        # Cache file includes year, country, subdivision
        safe_country = country.replace("/", "_")
        safe_subdivision = subdivision.replace("/", "_")
        cache_file = CACHING_DIR / f"holidays_{year}_{safe_country}_{safe_subdivision}.json"

        if cache_file.exists():
            try:
                return set(json.loads(cache_file.read_text(encoding="utf-8")))
            except Exception:
                pass

        url = (
            f"https://openholidaysapi.org/PublicHolidays?"
            f"countryIsoCode={country}&validFrom={year}-01-01&validTo={year}-12-31"
            f"&languageIsoCode=DE&subdivisionCode={subdivision}"
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
        dargs = item.get("dargs", {})
        params = item.get("params", {})

        caching_dir = Path(params.get("cachingDir", CACHING_DIR))
        country = params.get("countryIsoCode", COUNTRY_ISO)
        subdivision = params.get("subdivisionCode", SUBDIVISION_CODE)

        year = int(dargs.get("year", 0))
        month = int(dargs.get("month", 0))
        day = int(dargs.get("day", 0))
        date_str = f"{year:04d}-{month:02d}-{day:02d}"

        if year not in year_cache:
            year_cache[year] = load_holidays(year, country, subdivision)
        holidays = year_cache[year]

        is_holiday = date_str in holidays
        launch = True
        if is_holiday:
            launch = params.get("executeOnHoliday", False)

        response["items"].append({"launch": launch})

    print(json.dumps(response))

if __name__ == "__main__":
    main()

