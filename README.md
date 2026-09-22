# Geospatial Proximity Engine

The Geospatial Proximity Engine classifies target locations by their shortest
directed travel distance from one or more sources. It is designed for
questions such as which addresses are reachable from a site within a radius,
how many comparable locations are nearby, or which leads have the greatest
local opportunity.

The engine separates geographic distance from network distance. Great-circle
distance is used as a conservative candidate screen, while OSRM supplies the
final directed route distance or travel duration. This preserves the effect of
roads, barriers, one-way restrictions and the selected travel profile.

## Repository structure

```text
.
├── .github/workflows/                 # CI workflow configuration
├── docs/
│   ├── pages/                          # Static HTML documentation and assets
│   ├── poster/                         # LaTeX source and figures for the poster
│   └── README.md
├── src/
│   ├── libraries/
│   │   ├── algoritm/                   # Proximity pipeline
│   │   ├── classes/                    # OSRMClient
│   │   ├── runner/                     # HTTP request runner and example JSON
│   │   └── README.md
│   ├── services/
│   │   ├── geospatial-proximity/       # FastAPI service
│   │   └── osrm/                       # Local OSRM Docker setup
│   ├── test/
│   │   ├── algoritm/
│   │   ├── osrm_api/
│   │   ├── proximity/
│   │   ├── runner/
│   │   ├── services/geospatial_proximity/
│   │   └── README.md
│   ├── visulation/
│   │   ├── data/                       # Prepared JSON input data
│   │   ├── output/                     # Generated maps and exports (gitignored)
│   │   ├── generate_proximity_maps.py
│   │   └── README.md
│   └── README.md
├── .gitignore
├── pytest.ini
├── requriement.txt                    # Repository dependency list
└── README.md
```

The generated OSRM map data under `src/services/osrm/data/` and generated
visualisation output under `src/visulation/output/` are excluded from Git.

## Method

For a directed graph `G = (V, E, w)`, sources `S`, targets `T` and radius `r`,
the pipeline is:

1. select source-target pairs whose great-circle distance is at most `r`;
2. query OSRM for the directed source-to-target table values of those pairs;
3. accept a relation when its routed distance or duration is at most `r`;
4. return the matrix, accepted relations and aggregate summaries.

The geographic screen is safe as an exclusion rule: great-circle distance is
never greater than a feasible route distance. A pair outside the geographic
bound therefore cannot be a routed match.

## Documentation map

- [`src/services/geospatial-proximity/README.md`](src/services/geospatial-proximity/README.md) — HTTP API and Docker startup;
- [`src/services/osrm/README.md`](src/services/osrm/README.md) — local OSRM data and containers;
- [`src/libraries/README.md`](src/libraries/README.md) — reusable algorithm, OSRM client and runner;
- [`src/libraries/runner/README.md`](src/libraries/runner/README.md) — command-line request runner;
- [`src/test/README.md`](src/test/README.md) — test organization and commands;
- [`src/visulation/README.md`](src/visulation/README.md) — Folium map generation;
- [`docs/README.md`](docs/README.md) — static documentation pages and assets.

The browser documentation is available from
[`docs/pages/index.html`](docs/pages/index.html).

## Setup

Create and activate a Python virtual environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requriement.txt
```

The repository keeps the existing dependency filename `requriement.txt`.

## Start local OSRM

Docker Desktop must be running. Follow the preparation steps in
[`src/services/osrm/README.md`](src/services/osrm/README.md), then start the
three local profiles:

```powershell
cd src/services/osrm
docker compose up
```

| Profile | Endpoint |
|---|---|
| `foot` | `http://localhost:5000` |
| `car` | `http://localhost:5001` |
| `bicycle` | `http://localhost:5002` |

## Run the HTTP service

From the repository root, start the API after OSRM is available:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
uvicorn --app-dir src/services/geospatial-proximity main:app --port 8000
```

The service exposes `GET /health`, `POST /proximity` and interactive OpenAPI
documentation at `GET /docs`. It can also be built with the Compose file in
`src/services/geospatial-proximity/`.

## Run the reusable algorithm

With `src` on `PYTHONPATH`, import the public entry point:

```python
from libraries.algoritm.algoritm import run_proximity

distance_matrix, relations, summary = run_proximity(
    sources=[{"lon": 12.5683, "lat": 55.6761}],
    targets=[{"lon": 12.5800, "lat": 55.6800, "weight": 6}],
    radius=500,
    profile="foot",
)
```

The default unit is metres. Set `distance_unit="duration"` to compare OSRM
travel times in seconds; `speed_mps` can override the profile-specific speed
used for the geographic candidate screen.

## Run the request runner

After starting the API and configuring `PYTHONPATH`, submit the example request
from `src/libraries/runner/proximity_request.json`:

```powershell
python -m libraries.runner.runner
```

## Generate the Folium map

The current prepared visualisation inputs are
`src/visulation/data/proximity_sources_500m.json` and
`src/visulation/data/proximity_targets_500m.json`. With OSRM running:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -m src.visulation.generate_proximity_maps `
  --sources src/visulation/data/proximity_sources_500m.json `
  --targets src/visulation/data/proximity_targets_500m.json `
  --radius 500 `
  --profile foot
```

The generated HTML map and JSON distance export are written to
`src/visulation/output/`.

## Run tests

```powershell
pytest
```

The suite covers candidate selection, distance and duration filtering,
aggregation, OSRM URL/profile resolution, chunked table requests, the HTTP
service and the request runner.
