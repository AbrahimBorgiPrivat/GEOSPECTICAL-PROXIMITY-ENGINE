"""Simple orchestration for the generic proximity algorithm."""

from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from libraries.classes.osrm_api import OSRMClient
from libraries.algoritm.proximity import (
    _validate_locations,
    _validate_radius,
    DistanceUnit,
    aggregate_results,
    calculate_osrm_distances,
    filter_by_route_distance,
    normalize_distance_unit,
    select_candidates,
)

Location = Mapping[str, float]
DEFAULT_PROFILE = "foot"
DISTANCE_UNIT = "metres"


def run_proximity(
    sources: Sequence[Location],
    targets: Sequence[Location],
    radius: float,
    osrm_client: Optional[OSRMClient] = None,
    profile: Optional[str] = None,
    include_candidate_distances: bool = False,
    distance_unit: DistanceUnit = DISTANCE_UNIT,
    speed_mps: Optional[float] = None,
    radius_unit: Optional[DistanceUnit] = None,
) -> Tuple[np.ndarray, List[Dict[str, float]], Dict[str, int | float]]:
    """Run proximity using routed distance or duration as the radius metric.

    ``distance_unit='metres'`` preserves the original behaviour. With
    ``distance_unit='duration'``, OSRM durations are compared with ``radius`` and
    the geographic candidate screen uses ``speed_mps`` or the default speed
    associated with ``profile``.

    ``radius_unit`` is retained as a backwards-compatible alias for
    ``distance_unit``. The alias value ``'seconds'`` is normalized to
    ``'duration'``.
    """
    _validate_radius(radius)
    _validate_locations(sources, targets)
    if radius_unit is not None:
        if distance_unit != DISTANCE_UNIT and distance_unit != radius_unit:
            raise ValueError(
                "Use either distance_unit or radius_unit, not conflicting values."
            )
        distance_unit = radius_unit
    distance_unit = normalize_distance_unit(distance_unit)
    effective_profile = profile or DEFAULT_PROFILE
    client = osrm_client or OSRMClient(profile=effective_profile)

    candidates = select_candidates(
        sources,
        targets,
        radius,
        radius_unit=distance_unit,
        profile=effective_profile,
        speed_mps=speed_mps,
    )
    osrm_distances = calculate_osrm_distances(
        sources,
        targets,
        candidates,
        client,
        profile=effective_profile,
        radius_unit=distance_unit,
    )
    matches = filter_by_route_distance(
        candidates, osrm_distances, radius, radius_unit=distance_unit
    )

    distance_matrix = np.full((len(sources), len(targets)), np.nan)
    relations: List[Dict[str, float]] = []
    for match in matches:
        source_index = int(match["source_index"])
        target_index = int(match["target_index"])
        source = sources[source_index]
        target = targets[target_index]
        distance = float(match["dist"])
        distance_matrix[source_index, target_index] = distance
        relations.append(
            {
                "source_index": source_index,
                "target_index": target_index,
                "source_lon": float(source["lon"]),
                "source_lat": float(source["lat"]),
                "target_lon": float(target["lon"]),
                "target_lat": float(target["lat"]),
                "weight": float(target["weight"]),
                "geodist": float(match["geodist"]),
                "dist": distance,
            }
        )

    result = distance_matrix, relations, aggregate_results(sources, targets, matches)
    if include_candidate_distances:
        return result + (candidates, osrm_distances)
    return result


proximity_algorithm = run_proximity
