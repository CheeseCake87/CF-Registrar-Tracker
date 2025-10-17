import json
from datetime import datetime
from time import sleep
from typing import Callable, Any, Coroutine

import nodriver as uc
from bs4 import BeautifulSoup
from nodriver.core.tab import Tab

from . import KNOWN_EXTENSIONS_FILE, TEMP_FILE, LATEST_JSON_FILE, CWD
from .utils import convert_int_to_decimal
from .utils import convert_to_int
from .utils import generate_domain


CONTENT_TRIES = 0

def _get_content(content):
    soup = BeautifulSoup(content, "html.parser")
    return soup.find("div", {"data-testid": "domain-exact-match-availability"})


async def _loop_to_find_price(
        page: Coroutine[Any, Any, Tab] | Tab,
        tries: int = 0,
) -> BeautifulSoup | Coroutine[Any, Any, BeautifulSoup | None] | dict:

    tries += 1

    if tries > 15:
        return {
            "price": 0,
            "renewal": 0,
        }

    content = await page.get_content()

    if try_ := _get_content(content):
        return try_

    sleep(1)

    return await _loop_to_find_price(page, tries)


async def processor():
    browser = await uc.start()

    if not TEMP_FILE.exists():
        TEMP_FILE.write_text("{}")

    temp_data = json.loads(TEMP_FILE.read_text())
    known_extensions = KNOWN_EXTENSIONS_FILE.read_text().splitlines()

    for extension in known_extensions:
        if extension in temp_data:
            # skip if already fetched
            continue

        page = await browser.get(
            f"https://domains.cloudflare.com/?domain={generate_domain()}{extension}"
        )

        pricing = await _loop_to_find_price(page)

        if isinstance(pricing, dict):
            temp_data[extension] = pricing
            continue

        price = pricing.find(
            "span", {"class": "block text-lg font-semibold md:text-xl"}
        )
        renewal = pricing.find(
            "span", {"class": "block whitespace-nowrap text-xs text-gray-500"}
        )

        if not price and not renewal:
            temp_data[extension] = {
                "price": 0,
                "renewal": 0,
            }
            continue

        temp_data[extension] = {
            "price": convert_to_int(price.text),
            "renewal": convert_to_int(renewal.text),
        }

        TEMP_FILE.write_text(json.dumps(temp_data, indent=4))

    yyyymmdd = datetime.now().strftime("%Y-%m-%d")
    archived_json = CWD / "json" / f"{yyyymmdd}_domain_extensions.json"
    archived_csv = CWD / "csv" / f"{yyyymmdd}_domain_extensions.csv"

    json_temp_dump = json.dumps(temp_data, indent=4)

    LATEST_JSON_FILE.write_text(json_temp_dump)
    archived_json.write_text(json_temp_dump)

    for domain_extension, data in temp_data.items():
        with open(archived_csv, "a") as f:
            f.write(
                f"{domain_extension},{convert_int_to_decimal(data['price'])},{convert_int_to_decimal(data['renewal'])}\n"
            )
