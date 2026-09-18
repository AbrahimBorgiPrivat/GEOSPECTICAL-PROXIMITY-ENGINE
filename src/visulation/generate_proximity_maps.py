"""Generate one combined Folium proximity map for all leads."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import folium

from libraries.algoritm.algoritm import DISTANCE_UNIT, run_proximity
from libraries.algoritm.proximity import normalize_distance_unit, radius_to_meters
from libraries.classes.osrm_api import OSRMClient


DEFAULT_DATA_DIR = Path(__file__).parent / "data"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "output"
DEFAULT_RADIUS_METERS = 100.0
DEFAULT_RADIUS_UNIT = DISTANCE_UNIT


def load_json(path: Path) -> list[dict[str, Any]]:
    """Load a JSON list containing lead records."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}.")
    return data


def group_lead_locations(
    records: Sequence[Mapping[str, Any]], location_key: str
) -> dict[str, list[dict[str, float]]]:
    """Convert prepared JSON records into ``lead_id -> locations``."""
    grouped: dict[str, list[dict[str, float]]] = {}
    for record in records:
        if "lead_id" not in record:
            raise ValueError("Each record must contain 'lead_id'.")
        locations = record.get(location_key, [])
        if not isinstance(locations, list):
            raise ValueError(f"'{location_key}' must be a list.")
        grouped[str(record["lead_id"])] = [
            {
                "lead_id": str(record["lead_id"]),
                "lon": float(location["lon"]),
                "lat": float(location["lat"]),
                **(
                    {"weight": float(location["weight"])}
                    if "weight" in location
                    else {}
                ),
            }
            for location in locations
        ]
    return grouped


def _map_center(
    sources: Sequence[Mapping[str, float]],
    targets: Sequence[Mapping[str, float]],
) -> list[float]:
    points = list(sources) + list(targets)
    if not points:
        return [55.6761, 12.5683]
    return [
        sum(float(point["lat"]) for point in points) / len(points),
        sum(float(point["lon"]) for point in points) / len(points),
    ]


def _fit_map_to_points(
    proximity_map: folium.Map,
    sources: Sequence[Mapping[str, float]],
    targets: Sequence[Mapping[str, float]],
) -> None:
    points = list(sources) + list(targets)
    if not points:
        return
    bounds = [
        [
            min(float(point["lat"]) for point in points),
            min(float(point["lon"]) for point in points),
        ],
        [
            max(float(point["lat"]) for point in points),
            max(float(point["lon"]) for point in points),
        ],
    ]
    proximity_map.fit_bounds(bounds, padding=(30, 30))


def _add_osrm_routes(
    proximity_map: folium.Map,
    relations: Sequence[Mapping[str, float]],
    sources: Sequence[Mapping[str, float]],
    targets: Sequence[Mapping[str, float]],
    osrm_client: OSRMClient,
    profile: str,
    radius_unit: str,
) -> None:
    """Draw OSRM routes for every source-to-target pair."""
    red_routes_layer = folium.FeatureGroup(
        name="OSRM routes - outside radius", show=True
    )
    green_routes_layer = folium.FeatureGroup(
        name="OSRM routes - within radius", show=True
    )
    # Add red routes first and green routes last, so green wins where geometries overlap.
    red_routes_layer.add_to(proximity_map)
    green_routes_layer.add_to(proximity_map)

    matched_pairs = {
        (int(relation["source_index"]), int(relation["target_index"]))
        for relation in relations
    }
    matched_target_indices = {target_index for _, target_index in matched_pairs}
    metric_key = "duration" if radius_unit == "duration" else "distance"
    metric_label = "s" if radius_unit == "duration" else "m"

    for source_index, source in enumerate(sources):
        for target_index, target in enumerate(targets):
            # Do not clutter a matched target with red routes from other sources.
            if (
                target_index in matched_target_indices
                and (source_index, target_index) not in matched_pairs
            ):
                continue
            response = osrm_client.route(
                [
                    {"lon": float(source["lon"]), "lat": float(source["lat"])},
                    {"lon": float(target["lon"]), "lat": float(target["lat"])},
                ],
                overview="full",
                geometries="geojson",
                profile=profile,
            )
            routes = response.get("routes", [])
            if not routes:
                continue

            route = routes[0]
            coordinates = route.get("geometry", {}).get("coordinates", [])
            if len(coordinates) < 2:
                continue

            # GeoJSON uses [longitude, latitude], while Folium expects [latitude, longitude].
            route_line = folium.PolyLine(
                locations=[
                    (latitude, longitude) for longitude, latitude in coordinates
                ],
                color=(
                    "#16a34a"
                    if (source_index, target_index) in matched_pairs
                    else "#dc2626"
                ),
                weight=2,
                opacity=0.75,
                tooltip=(
                    f"Source {source_index} -> Target {target_index}: "
                    f"{float(route.get(metric_key, 0.0)):.1f} {metric_label}"
                ),
            )
            if (source_index, target_index) in matched_pairs:
                route_line.add_to(green_routes_layer)
            else:
                route_line.add_to(red_routes_layer)


def build_lead_map(
    lead_id: str,
    sources: Sequence[Mapping[str, float]],
    targets: Sequence[Mapping[str, float]],
    radius: float = DEFAULT_RADIUS_METERS,
    osrm_client: OSRMClient | None = None,
    profile: str = "foot",
    radius_unit: str = DEFAULT_RADIUS_UNIT,
    speed_mps: float | None = None,
    proximity_map: folium.Map | None = None,
) -> tuple[folium.Map, dict[str, Any]]:
    """Run proximity for one lead and render its source/target map."""
    radius_unit = normalize_distance_unit(radius_unit)
    client = osrm_client or OSRMClient(profile=profile)
    distance_matrix, relations, summary, candidates, candidate_distances = run_proximity(
        sources=sources,
        targets=targets,
        radius=radius,
        osrm_client=client,
        profile=profile,
        include_candidate_distances=True,
        distance_unit=radius_unit,
        speed_mps=speed_mps,
    )

    matched_source_indices = {
        int(relation["source_index"]) for relation in relations
    }
    target_matches: dict[int, list[dict[str, float]]] = defaultdict(list)
    target_candidate_distances: dict[int, list[dict[str, float]]] = defaultdict(list)
    for source_index, target_index, geodist in candidates:
        route_distance = candidate_distances.get((source_index, target_index))
        target_candidate_distances[target_index].append(
            {
                "source_index": source_index,
                "geodist": geodist,
                "dist": route_distance,
            }
        )
    for relation in relations:
        target_matches[int(relation["target_index"])].append(relation)

    if proximity_map is None:
        proximity_map = folium.Map(
            location=_map_center(sources, targets),
            zoom_start=15,
            control_scale=True,
            tiles=None,
        )
        folium.Element(
            "<style>"
            ".leaflet-container { background: #ffffff; }"
            ".leaflet-tile { filter: grayscale(1) brightness(1.18) contrast(.86); }"
            "</style>"
        ).add_to(proximity_map.get_root().html)
        folium.TileLayer(
            tiles="https://tile.openstreetmap.de/{z}/{x}/{y}.png",
            attr="© OpenStreetMap contributors",
            name="OpenStreetMap Light",
            overlay=False,
            control=True,
        ).add_to(proximity_map)

    _add_osrm_routes(
        proximity_map,
        relations,
        sources,
        targets,
        client,
        profile,
        radius_unit,
    )
    _fit_map_to_points(proximity_map, sources, targets)

    circle_radius_meters = radius_to_meters(
        radius,
        radius_unit,
        profile=profile,
        speed_mps=speed_mps,
    )
    radius_label = "s" if radius_unit == "duration" else "m"
    metric_label = "s" if radius_unit == "duration" else "m"

    for source_index, source in enumerate(sources):
        is_match = source_index in matched_source_indices
        color = "blue"
        status = "has target within radius" if is_match else "no target within radius"
        folium.Circle(
            location=[source["lat"], source["lon"]],
            radius=circle_radius_meters,
            color=color,
            fill=False,
            tooltip=f"Source {source_index}: {status}; radius={radius:.0f} {radius_label}",
        ).add_to(proximity_map)
        folium.CircleMarker(
            location=[source["lat"], source["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            popup=(
                f"Lead: {source.get('lead_id', lead_id)}<br>"
                f"Source index: {source_index}"
            ),
        ).add_to(proximity_map)

    for target_index, target in enumerate(targets):
        matches = target_matches.get(target_index, [])
        is_match = bool(matches)
        target_color = "green" if is_match else "red"
        route_text = "<br>".join(
            f"Source {int(match['source_index'])}: "
            f"{match['dist']:.1f} {metric_label}"
            for match in matches
        )
        if not route_text:
            route_text = "<br>".join(
                f"Source {int(candidate['source_index'])}: "
                f"{candidate['dist']:.1f} {metric_label}"
                for candidate in target_candidate_distances.get(target_index, [])
                if candidate["dist"] is not None
            ) or "No OSRM route: outside geographic candidate radius"
        target_popup = (
            "<div style='font-size: 11px; line-height: 1.25;'>"
            f"Lead: {target.get('lead_id', lead_id)}<br>"
            f"Status: {'within radius' if is_match else 'outside radius'}<br>"
            f"Weight: {target['weight']}<br>"
            f"{route_text}</div>"
        )
        folium.CircleMarker(
            location=[target["lat"], target["lon"]],
            radius=5,
            color=target_color,
            fill=True,
            fill_color=target_color,
            fill_opacity=0.8,
            popup=target_popup,
        ).add_to(proximity_map)

    return proximity_map, {
        "lead_id": lead_id,
        "radius": radius,
        "radius_unit": radius_unit,
        "speed_mps": speed_mps,
        "summary": summary,
        "distance_matrix": distance_matrix.tolist(),
        "relations": relations,
        "candidate_distances": {
            f"{source_index}:{target_index}": distance
            for (source_index, target_index), distance in candidate_distances.items()
        },
    }


def generate_maps(
    source_path: Path,
    target_path: Path,
    output_dir: Path,
    radius: float = DEFAULT_RADIUS_METERS,
    profile: str = "foot",
    radius_unit: str = DEFAULT_RADIUS_UNIT,
    speed_mps: float | None = None,
) -> list[Path]:
    """Generate one combined HTML map containing all leads and locations."""
    source_records = load_json(source_path)
    target_records = load_json(target_path)
    sources_by_lead = group_lead_locations(source_records, "source")
    targets_by_lead = group_lead_locations(target_records, "target")
    lead_ids = sorted(set(sources_by_lead) | set(targets_by_lead))

    output_dir.mkdir(parents=True, exist_ok=True)
    combined_map: folium.Map | None = None
    results: list[dict[str, Any]] = []
    all_sources = []
    all_targets = []
    for lead_id in lead_ids:
        lead_map, result = build_lead_map(
            lead_id,
            sources_by_lead.get(lead_id, []),
            targets_by_lead.get(lead_id, []),
            radius=radius,
            profile=profile,
            radius_unit=radius_unit,
            speed_mps=speed_mps,
            proximity_map=combined_map,
        )
        combined_map = lead_map
        results.append(result)
        all_sources.extend(sources_by_lead.get(lead_id, []))
        all_targets.extend(targets_by_lead.get(lead_id, []))

    if combined_map is None:
        combined_map = folium.Map(location=[55.6761, 12.5683], tiles=None)
    _fit_map_to_points(combined_map, all_sources, all_targets)
    output_path = output_dir / "proximity_map.html"
    combined_map.save(output_path)
    with (output_dir / "proximity_map_distances.json").open(
        "w", encoding="utf-8"
    ) as file:
        json.dump({"leads": results}, file, ensure_ascii=False, indent=2, default=str)
    return [output_path]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources",
        type=Path,
        default=DEFAULT_DATA_DIR / "proximity_sources_100m_residential.json",
    )
    parser.add_argument(
        "--targets",
        type=Path,
        default=DEFAULT_DATA_DIR / "proximity_targets_100m_residential.json",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--radius", type=float, default=DEFAULT_RADIUS_METERS)
    parser.add_argument(
        "--distance-unit",
        "--radius-unit",
        dest="radius_unit",
        default=DEFAULT_RADIUS_UNIT,
        choices=["metres", "duration", "seconds"],
        help="Interpret --radius as metres or a duration in seconds.",
    )
    parser.add_argument(
        "--speed-mps",
        type=float,
        default=None,
        help="Movement speed in metres per second for duration candidate screening.",
    )
    parser.add_argument(
        "--profile", default="foot", choices=["foot", "car", "bicycle"]
    )
    args = parser.parse_args()

    for path in generate_maps(
        args.sources,
        args.targets,
        args.output_dir,
        radius=args.radius,
        profile=args.profile,
        radius_unit=args.radius_unit,
        speed_mps=args.speed_mps,
    ):
        print(f"Created {path}")


if __name__ == "__main__":
    main()
