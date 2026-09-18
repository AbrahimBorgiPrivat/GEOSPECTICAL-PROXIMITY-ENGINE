# Source package

The `src` directory contains the executable Python code for the Geospatial
Proximity Engine. The implementation is split into reusable libraries, tests
and the map-generation workflow.

## Structure

- `libraries/` — proximity algorithm, validation, aggregation and OSRM client;
- `services/osrm/` — Docker Compose configuration for local OSRM profiles;
- `test/` — unit and integration-style tests;
- `visulation/` — prepared JSON inputs and combined Folium map generation.

The core pipeline is:

```text
source/target data -> geographic candidate screen -> OSRM table distances
                    -> routed radius filter -> relations and summaries
```

The public orchestration entry point is
`libraries.algoritm.algoritm.run_proximity`.

## Running source modules

From the repository root, expose `src` so the existing `libraries` imports can
be resolved:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
```

See the READMEs in `libraries`, `test` and `visulation` for module-specific
commands and conventions.
