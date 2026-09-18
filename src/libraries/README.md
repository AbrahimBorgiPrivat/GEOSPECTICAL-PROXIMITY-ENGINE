# Reusable libraries

This directory contains the reusable calculation and routing components. The
code is intentionally independent of the Folium presentation layer.

## `algoritm/`

The proximity pipeline is implemented in two modules:

- `algoritm.py` exposes `run_proximity`, validates inputs, orchestrates the
  pipeline and assembles the returned matrix, relations and summary;
- `proximity.py` contains the geographic lower bound, candidate selection,
  routed-distance filtering and aggregation helpers.

Candidate selection uses great-circle distance as a safe lower bound. Only pairs
that can satisfy the radius are sent to OSRM, while the final decision uses the
directed network distance.

## `classes/`

`osrm_api.py` contains `OSRMClient`, which supports:

- local `foot`, `car` and `bicycle` endpoints;
- OSRM table requests for source-to-target distance matrices;
- chunked table requests for larger inputs;
- route requests with GeoJSON geometry for map visualisation.

## Basic usage

```python
from libraries.algoritm.algoritm import run_proximity

distance_matrix, relations, summary = run_proximity(
    sources=sources,
    targets=targets,
    radius=100,
    profile="foot",
)
```

The default radius unit is `metres`. For a time radius, OSRM durations are used
instead:

```python
distance_matrix, relations, summary = run_proximity(
    sources=sources,
    targets=targets,
    radius=900,
    distance_unit="duration",
    profile="foot",
    speed_mps=1.6,  # optional override
)
```

If `speed_mps` is omitted, the algorithm uses the profile defaults `foot=1.4`,
`bicycle=5.6` and `car=13.9` metres per second. The speed converts seconds to
the metre bound used during candidate selection; use a conservative upper-bound
assumption when exact exclusion is required. In seconds mode, matrix values and
the relation field `dist` are durations in seconds.

Set `PYTHONPATH=src` when running the project from its repository root, or use
the test configuration supplied in `pytest.ini`.
