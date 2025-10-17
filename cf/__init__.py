from pathlib import Path

CWD = Path.cwd()
KNOWN_EXTENSIONS_FILE = CWD / "known_extensions.txt"
CSV_DIR = CWD / "csv"
JSON_DIR = CWD / "json"

TEMP_FILE = CWD / "temp.json"

README = CWD / "README.md"

LATEST_CSV_FILE = CSV_DIR / "latest_domain_extensions.csv"
LATEST_JSON_FILE = JSON_DIR / "latest_domain_extensions.json"

__all__ = [
    "KNOWN_EXTENSIONS_FILE",
    "CSV_DIR",
    "JSON_DIR",
    "TEMP_FILE",
    "LATEST_CSV_FILE",
    "LATEST_JSON_FILE",
]
