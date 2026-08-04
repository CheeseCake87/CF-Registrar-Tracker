import json
from datetime import datetime
from time import sleep
from typing import Any, Coroutine

import nodriver as uc
from bs4 import BeautifulSoup
from nodriver.core.tab import Tab

from . import CWD, KNOWN_EXTENSIONS_FILE, LATEST_JSON_FILE, TEMP_FILE
from .utils import convert_int_to_decimal, convert_to_int, generate_domain

CONTENT_TRIES = 0


def _get_content(content):
    soup = BeautifulSoup(content, "html.parser")
    return soup.find("div", {"data-testid": "domain-exact-match-availability"})


def _get_tlds_results(content):
    soup = BeautifulSoup(content, "html.parser")
    return soup.find("div", {"data-testid": "tlds-results"})


async def _loop_to_find_tlds(
    page: Coroutine[Any, Any, Tab] | Tab,
    tries: int = 0,
) -> BeautifulSoup | None:
    tries += 1

    if tries > 15:
        return None

    content = await page.get_content()

    if try_ := _get_tlds_results(content):
        return try_

    sleep(1)

    return await _loop_to_find_tlds(page, tries)


async def tlds_processor():
    browser = await uc.start()
    page = await browser.get("https://domains.cloudflare.com/tlds")

    tlds_div = await _loop_to_find_tlds(page)

    if tlds_div is None:
        raise RuntimeError("Could not locate tlds-results element")

    tlds = set()
    for text in tlds_div.stripped_strings:
        tlds.add(f".{text}")

    sorted_tlds = sorted(tlds)

    KNOWN_EXTENSIONS_FILE.write_text("\n".join(sorted_tlds) + "\n")


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

        temp_data[extension] = {}

        page = await browser.get(
            f"https://domains.cloudflare.com/?domain={generate_domain()}{extension}"
        )

        pricing = await _loop_to_find_price(page)

        if isinstance(pricing, dict):
            temp_data[extension] = pricing
            continue

        price = pricing.find(
            "span", {"data-testid": "promo-price", "class": "text-lg md:text-xl"}
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

        if hasattr(price, "text"):
            temp_data[extension]["price"] = convert_to_int(price.text)
        else:
            temp_data[extension]["price"] = 0

        if hasattr(renewal, "text"):
            temp_data[extension]["renewal"] = convert_to_int(renewal.text)
        else:
            temp_data[extension]["renewal"] = 0

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
