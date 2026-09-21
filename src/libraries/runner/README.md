# Runner

Start the geospatial proximity service, configure `PYTHONPATH`, and run from
the project root:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -m libraries.runner.runner
```

The runner posts `proximity_request.json` to
`http://localhost:8000/proximity` and prints the JSON response.
