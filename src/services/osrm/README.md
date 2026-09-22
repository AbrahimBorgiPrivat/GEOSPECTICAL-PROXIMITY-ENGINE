# OSRM Service

This directory contains the local OSRM routing setup used by the Geospatial Proximity Engine. It builds and runs Denmark routing data for three profiles:

- foot — walking routes on http://localhost:5000
- car — driving routes on http://localhost:5001
- bicycle — bicycle routes on http://localhost:5002

The service provides directed distance or duration matrices for proximity calculations and route geometries for map visualization.

## 1. Directory structure

~~~text
src/services/osrm/
│
├── data/
│   ├── maps/
│   │   └── denmark.osm.pbf       # Downloaded OpenStreetMap data
│   └── osrm/
│       ├── foot/                 # Generated foot routing data
│       ├── car/                  # Generated car routing data
│       └── bicycle/              # Generated bicycle routing data
│
├── build_data.sh                 # Extract, partition and customize data
├── docker-compose.yml            # Three local OSRM services
└── README.md
~~~

The generated map data is large and is excluded from Git. It must be built locally before the containers are started.

## 2. Requirements

- Docker Desktop with Docker Compose
- Git Bash on Windows (required for build_data.sh)
- Internet access to download the Denmark OSM extract
- Sufficient disk space for the downloaded map and generated profiles

## 3. Download the Denmark map

From the repository root, download the Denmark extract into src/services/osrm/data/maps/:

~~~bash
cd src/services/osrm/data/maps
curl -L -o denmark.osm.pbf https://download.geofabrik.de/europe/denmark-latest.osm.pbf
~~~

The expected file is:

~~~text
src/services/osrm/data/maps/denmark.osm.pbf
~~~

## 4. Build the OSRM data

Run the build script from this directory in Git Bash:

~~~bash
cd src/services/osrm
chmod +x build_data.sh
./build_data.sh
~~~

The script builds all three profiles. For each profile it runs:

1. osrm-extract using the profile Lua file;
2. osrm-partition using the MLD algorithm; and
3. osrm-customize using the generated .osrm file.

Generated files are written to:

~~~text
src/services/osrm/data/osrm/foot/
src/services/osrm/data/osrm/car/
src/services/osrm/data/osrm/bicycle/
~~~

On Windows, run the script from Git Bash so its path conversion and Docker volume handling work correctly.

## 5. Start the OSRM services

Make sure Docker Desktop is running, then execute:

~~~bash
cd src/services/osrm
docker compose up
~~~

To run the containers in the background:

~~~bash
docker compose up -d
~~~

The local endpoints are:

| Profile | Base URL | Docker container |
|---|---|---|
| foot | http://localhost:5000 | osrm_foot |
| car | http://localhost:5001 | osrm_car |
| bicycle | http://localhost:5002 | osrm_bicycle |

Each container runs osrm-routed --algorithm mld against its profile-specific Denmark dataset.

Useful commands:

~~~bash
docker compose ps
docker compose logs -f osrm_car
docker compose down
~~~

## 6. OSRM API endpoints

The routing services expose the standard OSRM API. The profile is part of the request path, for example:

~~~text
http://localhost:5001/table/v1/car/{lon1},{lat1};{lon2},{lat2}
http://localhost:5001/route/v1/car/{lon1},{lat1};{lon2},{lat2}
~~~

| Endpoint | Purpose |
|---|---|
| /table | Directed distance or duration matrix |
| /route | Route geometry, distance, duration and optional steps |
| /nearest | Nearest routable street location |
| /match | Map matching of recorded coordinates |

See the [OSRM API documentation](https://project-osrm.org/docs/v5.24.0/api/) for the complete endpoint and parameter reference.

## 7. Python integration

The Python client is implemented in src/libraries/classes/osrm_api.py. It resolves local profile URLs automatically and supports the foot, car and bicycle profiles.

### 7.1 Distance and duration matrices

~~~python
from libraries.classes.osrm_api import OSRMClient

locations = [
    {"lon": 12.5683, "lat": 55.6761},
    {"lon": 12.5900, "lat": 55.6700},
]

client = OSRMClient(profile="car")
distances = client.table_chunked(locations, annotations="distance")
durations = client.table_chunked(locations, annotations="duration")
~~~

For source and target collections, use table_between_chunked():

~~~python
matrix = client.table_between_chunked(
    sources=source_locations,
    targets=target_locations,
    annotations="distance",
)
~~~

The proximity algorithm uses these directed values when calculating geographic proximity. Distances are returned in metres and durations in seconds.

### 7.2 Routes and geometry

~~~python
client = OSRMClient(profile="car")
response = client.route(
    locations,
    overview="full",
    steps=True,
    geometries="geojson",
)

route = response["routes"][0]
geometry = route["geometry"]
~~~

Use geometries="polyline" or geometries="polyline6" when an encoded polyline is preferred. Route responses are consumed by the visualization code in src/visulation/, which renders OSRM routes in Folium maps.

### 7.3 Custom or containerized URLs

Local mode selects the profile-specific port automatically:

~~~python
client = OSRMClient(profile="bicycle")  # http://localhost:5002
~~~

To use another OSRM host, pass an explicit base_url:

~~~python
client = OSRMClient(
    base_url="http://osrm.example.com",
    profile="car",
)
~~~

The local URL can also be overridden with environment variables:

~~~text
OSRM_FOOT_URL
OSRM_CAR_URL
OSRM_BICYCLE_URL
~~~

## 8. Typical workflow

1. Download denmark.osm.pbf.
2. Build the foot, car and bicycle datasets.
3. Start the OSRM containers.
4. Start the proximity API or run the Python pipeline.
5. Generate proximity results and Folium route maps.

## 9. Troubleshooting

### Map file not found

Confirm that the map exists at:

~~~text
src/services/osrm/data/maps/denmark.osm.pbf
~~~

Run build_data.sh from src/services/osrm, not from the repository root.

### Generated OSRM data is missing

Confirm that each profile contains a generated dataset:

~~~text
src/services/osrm/data/osrm/foot/denmark.osrm
src/services/osrm/data/osrm/car/denmark.osrm
src/services/osrm/data/osrm/bicycle/denmark.osrm
~~~

If any profile is missing, rebuild the data before starting Docker Compose.

### A profile is unavailable

Check the container and its logs:

~~~bash
docker compose ps
docker compose logs osrm_foot
docker compose logs osrm_car
docker compose logs osrm_bicycle
~~~

Also verify that ports 5000, 5001 and 5002 are not already in use.

### Requests fail from the API container

When the proximity API runs in Docker, use the configured host.docker.internal URLs rather than localhost. The API Compose setup maps the local profiles to ports 5000, 5001 and 5002 respectively.

## 10. Licensing

OSRM is open-source software, and the routing data is derived from OpenStreetMap. OpenStreetMap data is available under the [ODbL license](https://www.openstreetmap.org/copyright). Review the applicable OSRM and OpenStreetMap attribution requirements before distributing results.

## 11. Maintainer

This OSRM integration is part of the Geospatial Proximity Engine project.

Maintainer: **Abrahim Borgi**
