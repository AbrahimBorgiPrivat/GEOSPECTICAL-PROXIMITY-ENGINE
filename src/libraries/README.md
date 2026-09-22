# Reusable libraries

This directory contains the reusable proximity algorithm, OSRM client and
HTTP request runner. It is independent of the FastAPI service and the Folium
visualisation layer.

## Directory structure

```text
src/libraries/
├── __init__.py
├── algoritm/
│   ├── __init__.py
│   ├── algoritm.py       # Public orchestration function
│   └── proximity.py      # Distance, filtering and aggregation helpers
├── classes/
│   ├── __init__.py
│   └── osrm_api.py       # OSRM table and route client
├── runner/
│   ├── __init__.py
│   ├── proximity_request.json
│   ├── runner.py         # Command-line HTTP client
│   └── README.md
└── README.md
```

## Algorithm modules

`algoritm/algoritm.py` exposes `run_proximity`. It validates the inputs,
selects candidate pairs, requests routed values from OSRM, applies the active
radius and returns:

1. a NumPy source-by-target matrix;
2. accepted source-target `relations` with coordinates, weights and `dist`;
3. a `summary` with relation counts and weight totals.

`algoritm/proximity.py` contains the reusable steps:

- great-circle geographic distance;
- conservative candidate selection;
- routed-distance or duration filtering;
- relation and unique-target aggregation;
- radius and movement-speed unit conversion.

`classes/osrm_api.py` contains `OSRMClient`. It resolves the local `foot`,
`car` and `bicycle` endpoints, supports explicit remote base URLs, performs
OSRM table requests, splits large source/target collections into chunks and
requests route geometries for map rendering.

## Basic usage

From the repository root, make `src` available as the top-level package path:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
```

Then call the public function:

```python
from libraries.algoritm.algoritm import run_proximity

distance_matrix, relations, summary = run_proximity(
    sources=[{"lon": 12.5683, "lat": 55.6761}],
    targets=[{"lon": 12.5690, "lat": 55.6765, "weight": 1}],
    radius=500,
    profile="foot",
)
```

The default unit is `metres`. For a time-based radius, use seconds through
`distance_unit="duration"` (or the backwards-compatible `radius_unit`):

```python
distance_matrix, relations, summary = run_proximity(
    sources=sources,
    targets=targets,
    radius=15 * 60,
    distance_unit="duration",
    profile="foot",
    speed_mps=1.6,
)
```

When `speed_mps` is omitted, the profile defaults are `foot=1.4`,
`bicycle=5.6` and `car=13.9` metres per second. This speed is used only to
convert a duration radius into the geographic candidate-screen radius; OSRM
still makes the final routed decision.

## Runner

`runner/runner.py` sends the example JSON in
`runner/proximity_request.json` to `http://localhost:8000/proximity` and
prints the response. With the API running and `PYTHONPATH` configured, run it
from the repository root:

```powershell
python -m libraries.runner.runner
```

See [`runner/README.md`](runner/README.md) for the runner-specific details.
