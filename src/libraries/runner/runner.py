"""Call the geospatial proximity HTTP service with a JSON request."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import requests


DEFAULT_INPUT = Path(__file__).with_name("proximity_request.json")
DEFAULT_URL = "http://localhost:8000/proximity"


def load_request(path: Path) -> dict[str, Any]:
    """Load one proximity API request from JSON."""
    with path.open("r", encoding="utf-8") as file:
        request = json.load(file)
    if not isinstance(request, dict):
        raise ValueError(f"Expected a JSON object in {path}.")
    return request


def run(input_path: Path = DEFAULT_INPUT, url: str = DEFAULT_URL) -> dict[str, Any]:
    """Send the JSON request to the running proximity service."""
    request = load_request(input_path)
    response = requests.post(url, json=request, timeout=300)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict):
        raise ValueError("The proximity service returned a non-object JSON response.")
    return result


def main() -> int:
    try:
        result = run()
    except (OSError, ValueError, requests.RequestException) as error:
        print(f"Runner failed: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
