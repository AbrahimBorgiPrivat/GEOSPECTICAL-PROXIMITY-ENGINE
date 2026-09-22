# Tests

The tests in this directory cover the reusable proximity pipeline, the OSRM
client boundary, the HTTP service and the command-line runner. Most tests use
controlled or mocked OSRM responses and therefore do not require Docker.

## Directory structure

```text
src/test/
├── conftest.py                         # Shared fixtures and test setup
├── algoritm/
│   └── test_run_proximity.py           # Public orchestration
├── proximity/
│   ├── test_aggregate_results.py
│   ├── test_calculate_osrm_distances.py
│   ├── test_filter_by_route_distance.py
│   ├── test_find_proximity.py
│   ├── test_geographical_distance.py
│   ├── test_radius_units.py
│   └── test_select_candidates.py
├── osrm_api/
│   ├── test_resolve_base_url.py
│   ├── test_resolve_path_profile.py
│   ├── test_resolve_profile.py
│   ├── test_route.py
│   ├── test_table.py
│   ├── test_table_between_chunked.py
│   └── test_table_chunked.py
├── runner/
│   └── test_runner.py
├── services/
│   └── geospatial_proximity/
│       └── test_service.py            # FastAPI endpoints and JSON output
└── README.md
```

The test directory is named `test`, while the API directory is named
`geospatial-proximity` with a hyphen. The service test package uses an
underscore because it is a Python package name.

## Run the full suite

From the repository root with the virtual environment active:

```powershell
pytest
```

The repository-level `pytest.ini` enables coverage for
`libraries.algoritm` and `libraries.classes`. To run only one area, use for
example:

```powershell
pytest src/test/proximity
pytest src/test/osrm_api
pytest src/test/services/geospatial_proximity
```

Start the local OSRM services only when adding or running a test that is
explicitly intended to make live routing requests. The regular suite does not
need the generated OSRM data.
