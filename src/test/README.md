# Tests

The test suite verifies the mathematical pipeline and the OSRM integration
boundary without requiring every test to call a live routing service.

## Coverage areas

- `algoritm/` — orchestration and the public `run_proximity` result;
- `proximity/` — geographic distance, candidate selection, routed filtering
  and relation/weight aggregation;
- `osrm_api/` — profile and URL resolution, routes, tables and chunking;
- `conftest.py` — shared test configuration and fixtures.

## Run the suite

From the repository root with the virtual environment active:

```powershell
pytest
```

The project configuration enables coverage for `libraries.algoritm` and
`libraries.classes`. Most tests use mocked or controlled OSRM responses, so
they can run without starting Docker. Start the local OSRM services when adding
an end-to-end routing test.
