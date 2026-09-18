"""Generic source-to-target proximity pipeline."""

import math
from typing import Dict, List, Literal, Mapping, Optional, Sequence, Tuple

import numpy as np

from libraries.classes.osrm_api import OSRMClient


Location = Mapping[str, float]
Candidate = Tuple[int, int, float]
DistanceUnit = Literal["metres", "duration", "seconds"]
# Backwards-compatible type alias for callers that used the earlier name.
RadiusUnit = DistanceUnit

DEFAULT_SPEED_MPS_BY_PROFILE = {
    "foot": 1.4,
    "bicycle": 5.6,
    "car": 13.9,
}


def geographical_distance(source: Location, target: Location) -> float:
    """Return the great-circle distance between two locations in metres."""
    source_lon, source_lat = _coordinates(source, "source")
    target_lon, target_lat = _coordinates(target, "target")

    earth_radius_m = 6_371_000.0
    lat_1 = math.radians(source_lat)
    lat_2 = math.radians(target_lat)
    delta_lat = math.radians(target_lat - source_lat)
    delta_lon = math.radians(target_lon - source_lon)
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_1) * math.cos(lat_2) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * earth_radius_m * math.asin(math.sqrt(haversine))


def select_candidates(
    sources: Sequence[Location],
    targets: Sequence[Location],
    radius: float,
    radius_unit: DistanceUnit = "metres",
    profile: Optional[str] = None,
    speed_mps: Optional[float] = None,
) -> List[Candidate]:
    """Return candidate pairs within the geographic lower-bound radius.

    A time radius is converted to metres before candidate selection. The speed
    is a screening/conversion assumption; OSRM remains responsible for the
    final routed distance or duration decision.
    """
    _validate_radius(radius)
    radius_meters = radius_to_meters(
        radius, radius_unit, profile=profile, speed_mps=speed_mps
    )
    candidates: List[Candidate] = []
    for source_index, source in enumerate(sources):
        _coordinates(source, "source")
        for target_index, target in enumerate(targets):
            geodist = geographical_distance(source, target)
            if geodist <= radius_meters:
                candidates.append((source_index, target_index, geodist))
    return candidates


def calculate_osrm_distances(
    sources: Sequence[Location],
    targets: Sequence[Location],
    candidates: Sequence[Candidate],
    osrm_client: OSRMClient,
    profile: Optional[str] = None,
    radius_unit: DistanceUnit = "metres",
) -> Dict[Tuple[int, int], float]:
    """Calculate OSRM distance or duration values for candidate pairs."""
    normalized_unit = normalize_distance_unit(radius_unit)
    distances: Dict[Tuple[int, int], float] = {}
    candidates_by_source: Dict[int, List[int]] = {}
    for source_index, target_index, _ in candidates:
        candidates_by_source.setdefault(source_index, []).append(target_index)

    for source_index, target_indices in candidates_by_source.items():
        target_locations = [targets[target_index] for target_index in target_indices]
        matrix = osrm_client.table_between_chunked(
            [sources[source_index]],
            target_locations,
            profile=profile,
            annotations=("duration" if normalized_unit == "duration" else "distance"),
        )
        for matrix_target_index, target_index in enumerate(target_indices):
            distance = matrix[0, matrix_target_index]
            if not np.isnan(distance) and math.isfinite(float(distance)):
                distances[(source_index, target_index)] = float(distance)
    return distances


def filter_by_route_distance(
    candidates: Sequence[Candidate],
    osrm_distances: Mapping[Tuple[int, int], float],
    radius: float,
    radius_unit: DistanceUnit = "metres",
) -> List[Dict[str, float]]:
    """Keep candidates whose active OSRM metric is within ``radius``."""
    _validate_radius(radius)
    _validate_radius_unit(radius_unit)
    return [
        {
            "source_index": source_index,
            "target_index": target_index,
            "geodist": geodist,
            "dist": osrm_distances[(source_index, target_index)],
        }
        for source_index, target_index, geodist in candidates
        if (source_index, target_index) in osrm_distances
        and osrm_distances[(source_index, target_index)] <= radius
    ]


def aggregate_results(
    sources: Sequence[Location],
    targets: Sequence[Location],
    matches: Sequence[Mapping[str, float]],
) -> Dict[str, int | float]:
    """Build the requested relation counts and weight summaries."""
    unique_target_weights: Dict[Tuple[float, float], float] = {}
    for match in matches:
        target = targets[int(match["target_index"])]
        coordinate = _coordinates(target, "target")
        unique_target_weights.setdefault(coordinate, float(target["weight"]))

    return {
        "number_of_sources": len(sources),
        "number_of_targets": len(matches),
        "number_of_unique_targets": len(unique_target_weights),
        "sum_of_weight": sum(float(targets[int(m["target_index"])] ["weight"]) for m in matches),
        "unique_sum_of_weight": sum(unique_target_weights.values()),
    }


def find_proximity(
    sources: Sequence[Location],
    targets: Sequence[Location],
    radius: float,
    osrm_client: Optional[OSRMClient] = None,
    profile: Optional[str] = None,
    radius_unit: DistanceUnit = "metres",
    speed_mps: Optional[float] = None,
) -> Tuple[np.ndarray, List[Dict[str, float]], Dict[str, int | float]]:
    """Backward-compatible wrapper around :func:`run_proximity`."""
    from libraries.algoritm.algoritm import run_proximity

    return run_proximity(
        sources,
        targets,
        radius,
        osrm_client=osrm_client,
        profile=profile,
        radius_unit=radius_unit,
        speed_mps=speed_mps,
    )


def radius_to_meters(
    radius: float,
    radius_unit: DistanceUnit = "metres",
    profile: Optional[str] = None,
    speed_mps: Optional[float] = None,
) -> float:
    """Convert the configured radius to metres for candidate screening."""
    _validate_radius(radius)
    normalized_unit = normalize_distance_unit(radius_unit)
    if normalized_unit == "metres":
        return float(radius)
    return float(radius) * resolve_speed_mps(profile, speed_mps)


def resolve_speed_mps(
    profile: Optional[str] = None,
    speed_mps: Optional[float] = None,
) -> float:
    """Return an explicit or profile-specific movement speed in m/s."""
    if speed_mps is not None:
        try:
            value = float(speed_mps)
        except (TypeError, ValueError) as error:
            raise ValueError("speed_mps must be a positive number.") from error
        if not math.isfinite(value) or value <= 0:
            raise ValueError("speed_mps must be a positive number.")
        return value

    resolved_profile = (profile or "foot").lower()
    try:
        return DEFAULT_SPEED_MPS_BY_PROFILE[resolved_profile]
    except KeyError as error:
        raise ValueError(
            f"No default speed is configured for profile '{resolved_profile}'. "
            f"Provide speed_mps explicitly or use one of "
            f"{list(DEFAULT_SPEED_MPS_BY_PROFILE)}."
        ) from error


def _coordinates(location: Location, label: str) -> Tuple[float, float]:
    try:
        lon = float(location["lon"])
        lat = float(location["lat"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{label} must contain numeric 'lon' and 'lat'.") from error
    if not math.isfinite(lon) or not math.isfinite(lat):
        raise ValueError(f"{label} coordinates must be finite.")
    if not -180 <= lon <= 180 or not -90 <= lat <= 90:
        raise ValueError(f"{label} coordinates are outside valid ranges.")
    return lon, lat


def _validate_locations(
    sources: Sequence[Location], targets: Sequence[Location]
) -> None:
    for source in sources:
        _coordinates(source, "source")
    for target in targets:
        _coordinates(target, "target")
        try:
            weight = float(target["weight"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("target must contain numeric 'weight'.") from error
        if not math.isfinite(weight) or weight < 0:
            raise ValueError("target weight must be finite and non-negative.")


def _validate_radius(radius: float) -> None:
    try:
        value = float(radius)
    except (TypeError, ValueError) as error:
        raise ValueError("radius must be a non-negative number.") from error
    if not math.isfinite(value) or value < 0:
        raise ValueError("radius must be a non-negative number.")


def normalize_distance_unit(distance_unit: str) -> Literal["metres", "duration"]:
    """Normalize public metric names to ``metres`` or OSRM ``duration``."""
    if distance_unit == "seconds":
        return "duration"
    if distance_unit in {"metres", "duration"}:
        return distance_unit
    raise ValueError("distance_unit must be either 'metres' or 'duration'.")


def _validate_radius_unit(radius_unit: str) -> None:
    normalize_distance_unit(radius_unit)
