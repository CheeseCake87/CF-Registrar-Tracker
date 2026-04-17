import json
from datetime import datetime
from time import sleep

import click
import nodriver as uc

from . import LATEST_JSON_FILE
from . import README
from .fetch_data import processor
from .fetch_data import tlds_processor
from .utils import Sprinkles as Sp
from .utils import convert_int_to_decimal
from .utils import get_known_extensions


@click.group()
def cli():
    pass


@cli.command("known-extensions", help="List all known domain extensions.")
def known_extensions():
    for extension in get_known_extensions():
        print(extension)


@cli.command("find", help="Confirm that a domain extension is included in extensions_known.txt")
@click.argument("extension", type=str, required=True)
def find_extension(extension):
    if extension in get_known_extensions():
        print(f"{Sp.OKGREEN}{extension} is included in extensions_known.txt{Sp.END}")
    else:
        print(f"{Sp.FAIL}{extension} IS NOT included in extensions_known.txt{Sp.END}")


@cli.command("cost", help="Show the cost of a known domain extension.")
@click.argument("extension", type=str, required=True)
def extension_cost(extension):
    if LATEST_JSON_FILE.exists():
        raw = json.loads(LATEST_JSON_FILE.read_text())
        if ext := raw.get(extension):
            print(f"{Sp.OKBLUE}{extension}{Sp.END}")
            print(
                f"{Sp.OKGREEN}Registration: {convert_int_to_decimal(ext['price'])} USD{Sp.END}"
            )
            print(
                f"{Sp.OKGREEN}Renewal: {convert_int_to_decimal(ext['renewal'])} USD{Sp.END}"
            )
        else:
            print(f"{Sp.FAIL}No data for {extension}{Sp.END}")


@cli.command("fetch-pricing", help="Use an automated browser to fetch pricing data.")
def fetch_pricing():
    print(f"{Sp.OKGREEN}!! ------------------------ !!{Sp.END}")
    print(f"{Sp.OKGREEN}!! BROWSER IS ABOUT TO LOAD !!{Sp.END}")
    print(f"{Sp.OKGREEN}!! ------------------------ !!{Sp.END}")
    sleep(3)
    uc.loop().run_until_complete(processor())
    print(f"{Sp.OKGREEN}!! ------------------------ !!{Sp.END}")
    print(f"{Sp.OKGREEN}!!   PRICING DATA UPDATED   !!{Sp.END}")
    print(f"{Sp.OKGREEN}!! ------------------------ !!{Sp.END}")


@cli.command("fetch-tlds", help="Fetch the list of available TLDs and write them to extensions_known.txt.")
def fetch_tlds():
    print(f"{Sp.OKGREEN}!! ------------------------ !!{Sp.END}")
    print(f"{Sp.OKGREEN}!! BROWSER IS ABOUT TO LOAD !!{Sp.END}")
    print(f"{Sp.OKGREEN}!! ------------------------ !!{Sp.END}")
    sleep(3)
    uc.loop().run_until_complete(tlds_processor())
    print(f"{Sp.OKGREEN}!! ------------------------ !!{Sp.END}")
    print(f"{Sp.OKGREEN}!!     TLDS LIST UPDATED    !!{Sp.END}")
    print(f"{Sp.OKGREEN}!! ------------------------ !!{Sp.END}")


@cli.command("update-readme", help="Update the README.md file with the latest pricing data.")
def update_readme():
    readme_raw = README.read_text()
    latest_json_raw = LATEST_JSON_FILE.read_text()
    jsond = json.loads(latest_json_raw)

    # Split README into sections
    split_cheapest = readme_raw.split("## Top 20 Most Expensive Domain Extensions")

    # Sort domains by registration price for cheapest (excluding unavailable)
    available_domains = [(k, v) for k, v in jsond.items() if v['price'] > 0]

    # Sort domains by registration price for most expensive (excluding unavailable)
    sorted_expensive = sorted(available_domains, key=lambda x: x[1]['price'], reverse=True)[:20]

    # Create most expensive table
    expensive_lines = f"Updated: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    expensive_lines += "| Domain Extension | Registration | Renewal |\n| --- | --- | --- |\n"
    for key, value in sorted_expensive:
        d_price = convert_int_to_decimal(value['price'])
        d_renewal = convert_int_to_decimal(value['renewal'])
        registration = f"{d_price} USD"
        renewal = f"{d_renewal} USD" if d_renewal > 0 else 'UNAVAILABLE'
        expensive_lines += f"| {key} | {registration} | {renewal} |\n"

    sorted_cheapest_full = sorted(available_domains, key=lambda x: x[1]['price'])

    # Create full data table
    data_lines = f"Updated: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    data_lines += "| Domain Extension | Registration | Renewal |\n| --- | --- | --- |\n"
    for key, value in sorted_cheapest_full:
        d_price = convert_int_to_decimal(value['price'])
        d_renewal = convert_int_to_decimal(value['renewal'])
        registration = f"{d_price} USD" if d_price > 0 else 'UNAVAILABLE'
        renewal = f"{d_renewal} USD" if d_renewal > 0 else 'UNAVAILABLE'
        data_lines += f"| {key} | {registration} | {renewal} |\n"

    # Reconstruct README with all sections
    new_lines = [
        split_cheapest[0].rstrip("\n"),
        "\n\n## Top 20 Most Expensive Domain Extensions\n\n",
        expensive_lines,
        "\n\n## Data Table (cheapest first)\n\n",
        data_lines
    ]

    README.write_text("".join(new_lines))


if __name__ == "__main__":
    cli()
