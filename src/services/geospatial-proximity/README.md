# Geospatial proximity service

Start OSRM first from `src/services/osrm`, then run the API from the project
root:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
uvicorn --app-dir src/services/geospatial-proximity main:app --port 8000
```

Send `POST http://localhost:8000/proximity` with `sources`, `targets` (each
with `weight`) and `radius`. The response contains `distance_matrix`,
`relations` and `summary`. `GET /health` checks that the service is running.

The OpenAPI documentation is available at `/docs`.
