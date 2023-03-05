"""Geolocation utils."""
import os
import urllib.parse
from typing import Any

import requests
from joblib import Memory
from loguru import logger as log

memory = Memory(".cache", verbose=0)


@memory.cache
def geocode(input_query: str) -> dict[Any, Any]:
    log.info(f"geocode(input_query='{input_query}')")
    query = urllib.parse.quote_plus(input_query)
    api_key = os.environ.get("GOOGLE_API_KEY")
    r = requests.get(
        f"https://maps.googleapis.com/maps/api/geocode/json?address={query}&key={api_key}",
        timeout=30,
    )
    if r.status_code == 200:
        try:
            geocode_data = r.json()["results"][0]["geometry"]["location"]
            geocode_data["formatted_address"] = r.json()["results"][0]["formatted_address"]
        except Exception as e:
            log.info(f"{r.status_code=}")
            log.info(f"Is {input_query} a postcode with a geographic extent (not PO Box)?")
            log.info(r.json())
            raise e
        return geocode_data
    message = f"Request failed with status: {str(r.status_code)} ({str(r.content)})"
    log.error(message)
    raise RuntimeError(message)
