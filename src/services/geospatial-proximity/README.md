# Geospatial proximity service

Author: Anrahim Borgi

This directory contains the FastAPI service that exposes the reusable
proximity calculation as a JSON HTTP API. The service delegates the actual
calculation to `src/libraries/algoritm/` and uses `OSRMClient` from
`src/libraries/classes/` for routed distances or durations.

## Directory structure

```text
src/services/geospatial-proximity/
├── __init__.py
├── Dockerfile                 # Container image for the API
├── docker-compose.yml         # API container configuration
├── main.py                    # FastAPI application and endpoints
├── requirements.txt           # Dependencies used by the API image
└── README.md
```

The directory name contains a hyphen, so `main.py` is started as an app file
with Uvicorn rather than imported as a normal Python package.

## Run locally

Start the local OSRM profiles first from `src/services/osrm`. Then, from the
repository root, expose `src` as the Python import path and start the API:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
uvicorn --app-dir src/services/geospatial-proximity main:app --port 8000
```

The API expects the OSRM profiles at these default addresses:

| Profile | URL |
|---|---|
| `foot` | `http://localhost:5000` |
| `car` | `http://localhost:5001` |
| `bicycle` | `http://localhost:5002` |

Use the `osrm_url` request field when a request must use another OSRM base
URL. The API also supports the environment variables `OSRM_FOOT_URL`,
`OSRM_CAR_URL` and `OSRM_BICYCLE_URL` through `OSRMClient`.

## Run with Docker Compose

The API Compose file builds from the repository root and connects to OSRM on
the host through `host.docker.internal`:

```powershell
cd src/services/geospatial-proximity
docker compose up --build
```

The API is then available at `http://localhost:8000`. Start the separate OSRM
Compose setup before starting this service unless you provide another routing
backend.

## Endpoints

- `GET /health` returns `{"status": "ok"}` when the API process is alive.
- `POST /proximity` runs one source-to-target proximity calculation.
- `GET /docs` opens the generated Swagger UI.

Example request:

```json
{
  "sources": [
    {"lon": 12.5683, "lat": 55.6761}
  ],
  "targets": [
    {"lon": 12.5690, "lat": 55.6765, "weight": 1}
  ],
  "radius": 500,
  "profile": "foot",
  "distance_unit": "metres"
}
```

`radius` is interpreted in metres by default. Set `distance_unit` to
`duration` or `seconds` to use OSRM travel time in seconds. Optional fields
include `speed_mps`, `radius_unit` (a backwards-compatible alias),
`include_candidate_distances` and `osrm_url`.

The response contains `distance_matrix`, `relations` and `summary`. When
`include_candidate_distances` is `true`, it also contains the geographic
candidates and their OSRM values.

## Related code

- [`src/libraries/algoritm/`](../../libraries/algoritm/) — calculation pipeline;
- [`src/libraries/classes/`](../../libraries/classes/) — OSRM client;
- [`src/services/osrm/`](../osrm/) — local OSRM containers and routing data.
