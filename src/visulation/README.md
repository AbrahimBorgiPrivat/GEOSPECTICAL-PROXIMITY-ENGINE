# Visualisation

This directory turns prepared source and target records into a combined Folium
map. It is a presentation layer over the reusable proximity algorithm and does
not redefine the distance logic.

## Inputs

The default files are:

- `data/proximity_sources_100m_residential.json`;
- `data/proximity_targets_100m_residential.json`.

Records are grouped by `lead_id`. Each source or target location contains
`lon` and `lat`; targets also contain a non-negative `weight`.

## Generate a map

Start the local OSRM services first, then run from the repository root:

```powershell
$env:PYTHONPATH = (Resolve-Path src).Path
python -m src.visulation.generate_proximity_maps --radius 100 --profile foot
```

`--radius` is interpreted as metres by default. To use travel time, provide
`--distance-unit duration`; `--speed-mps` optionally overrides the profile-specific
speed used to convert that time into the geographic screening radius:

```powershell
python -m src.visulation.generate_proximity_maps --radius 900 --distance-unit duration --profile foot --speed-mps 1.6
```

The command produces:

- `output/proximity_map.html` — one combined Folium map for all leads;
- `output/proximity_map_distances.json` — calculation results and candidate
  distances used by the map.

## Map semantics

- blue markers and circles represent sources and their radius; time radii are
  converted to metres for Folium's geographic circle;
- green markers and routes represent accepted source-target relations;
- red markers and routes represent targets or routes outside the radius;
- green route layers are added after red layers so green geometry is visible
  where routes overlap.

OSRM route geometry is requested separately from the table-distance calculation,
which keeps the numerical result and the visual audit trail distinct.
