# Geospatial Proximity Engine

The Geospatial Proximity Engine classifies target locations by their shortest
directed travel distance from one or more sources. It is designed for questions
such as: which addresses are reachable from a site within a given radius, how
many comparable stores are nearby, or which leads have the greatest local
opportunity?

The central distinction is between geographic distance and network distance.
Straight-line distance is used as a safe lower-bound screen, while OSRM provides
the final route distance over the directed transport network. This preserves the
effect of roads, barriers, one-way restrictions and the selected travel profile.

## Method

Let `G = (V, E, w)` be a directed graph with non-negative edge lengths, `S` the
sources and `T` the targets. For a radius `r`, the engine applies four steps:

1. Select candidate source-target pairs whose great-circle distance is at most `r`.
2. Query OSRM for the directed source-to-target distance matrix of those pairs.
3. Accept a relation when its routed distance is at most `r`.
4. Return relation counts, weighted sums, unique targets and unique weighted sums.

The candidate screen is exact as an exclusion rule. By the triangle inequality,
great-circle distance is no greater than the length of any feasible route. Thus,
when the geographic distance exceeds `r`, the routed distance must also exceed
`r`; no true match is removed before routing.

## Outputs

`run_proximity` returns:

- a NumPy source-by-target distance matrix;
- accepted source-target relations with coordinates, weights and distances;
- summary measures for relation-based and unique target coverage.

Distances and radii use metres by default. A radius can also be expressed in
seconds, in which case OSRM travel durations are used. The default OSRM profile
is `foot`, with `car` and `bicycle` also supported.

## Documentation

Open the [documentation overview](docs/pages/index.html) for the introduction,
formal theory, four-step solution, Python/OSRM implementation, applications and
the conference [poster](docs/pages/poster.html).

Folder-specific documentation is available in:

- [`docs/README.md`](docs/README.md) — documentation pages and assets;
- [`src/README.md`](src/README.md) — source package structure;
- [`src/libraries/README.md`](src/libraries/README.md) — reusable algorithm and OSRM code;
- [`src/test/README.md`](src/test/README.md) — test organization and commands;
- [`src/visulation/README.md`](src/visulation/README.md) — Folium map generation.

## Setup

Create and activate a Python virtual environment from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requriement.txt
```

On Git Bash, activate the environment with:

```bash
source .venv/Scripts/activate
```

The repository currently uses the existing filename `requriement.txt` for its
dependency list.

## Start OSRM

Docker Desktop must be running. Start the Denmark OSRM services from the project
root:

```powershell
cd src/services/osrm
docker compose up
```

The local profiles are:

| Profile | Endpoint |
|---|---|
| `foot` | `http://localhost:5000` |
| `car` | `http://localhost:5001` |
| `bicycle` | `http://localhost:5002` |

The large OSRM map and routing data are excluded from Git through `.gitignore`.

## Run the algorithm

The package imports use `libraries` as the top-level source package. From
PowerShell, expose `src` on `PYTHONPATH` before running examples:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
```

Then the reusable calculation can be called as follows:

```python
from libraries.algoritm.algoritm import run_proximity

distance_matrix, relations, summary = run_proximity(
    sources=[{"lon": 12.5683, "lat": 55.6761}],
    targets=[{"lon": 12.5800, "lat": 55.6800, "weight": 6}],
    radius=500,
    profile="foot",
)
```

The matrix contains accepted routed distances and `numpy.nan` for non-matches.
The relation list contains the accepted source-target pairs, and `summary`
contains the aggregate measures described above.

When `distance_unit="duration"`, the matrix and each relation's `dist` value
are travel times in seconds rather than distances in metres.

For a time-based radius, set `distance_unit="duration"`. The default movement
speed is profile-specific: 1.4 m/s for walking, 5.6 m/s for cycling and
13.9 m/s for driving. Override it with `speed_mps` when a different movement
assumption is appropriate:

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

The speed is used to convert the time radius to a geographic metre bound for
candidate selection. For the exclusion argument to remain conservative, use a
speed that is an upper-bound movement assumption for the chosen profile.

## Generate the Folium map

With OSRM running and `PYTHONPATH` configured, generate the combined map for the
prepared visualisation data:

```powershell
python -m src.visulation.generate_proximity_maps --radius 100 --profile foot
```

To generate a walking-time map instead, use for example:

```powershell
python -m src.visulation.generate_proximity_maps --radius 900 --distance-unit duration --profile foot
```

The HTML map and its distance export are written to `src/visulation/output/`.
The map uses light OpenStreetMap tiles, blue sources, green accepted targets and
routes, and red rejected routes and targets.

## Run tests

```powershell
pytest
```

The test suite covers candidate selection, distance filtering, aggregation,
OSRM URL/profile handling and chunked table requests.
