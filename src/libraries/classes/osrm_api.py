import os
import requests
import math
import numpy as np
from tqdm import tqdm
from typing import List, Dict, Optional, Literal, Sequence

class OSRMClient:
    LOCAL_PROFILE_PORTS = {
        "foot": "http://localhost:5000",
        "car": "http://localhost:5001",
        "bicycle": "http://localhost:5002",
    }
    PROFILE_ENV_VARS = {
        "foot": "OSRM_FOOT_URL",
        "car": "OSRM_CAR_URL",
        "bicycle": "OSRM_BICYCLE_URL",
    }
    def __init__(
        self,
        base_url: str = "local",
        profile: str = "foot",
    ):
        profile = profile.lower()
        self.profile = profile
        self._local_mode = base_url == "local"
        if base_url == "local":
            self.base_url = self._resolve_base_url(profile)
        else:
            # Remote / external OSRM → do not interfere
            self.base_url = base_url.rstrip("/")
    
    def _resolve_profile(self, profile: Optional[str]) -> str:
        if profile is None:
            return self.profile
        return profile.lower()

    def _resolve_path_profile(self, profile: Optional[str]) -> str:
        return self._resolve_profile(profile)

    def _resolve_base_url(self, profile: Optional[str]) -> str:
        if not self._local_mode:
            return self.base_url

        resolved = self._resolve_profile(profile)
        if resolved not in self.LOCAL_PROFILE_PORTS:
            raise ValueError(
                f"Unsupported local profile '{resolved}'. "
                f"Supported: {list(self.LOCAL_PROFILE_PORTS)}"
            )

        env_var = self.PROFILE_ENV_VARS.get(resolved)
        return os.getenv(
            env_var,
            self.LOCAL_PROFILE_PORTS[resolved],
        ).rstrip("/")

    @staticmethod
    def _format_coordinates(locations: List[Dict[str, float]]):
        """
        Converts list of dicts with lon/lat into OSRM coordinate string.
        Input:[{'lon': 14.7, 'lat': 55.1}, ...]
        Returns: "lon1,lat1;lon2,lat2;lon3,lat3"
        """
        parts = []
        for loc in locations:
            lon = float(loc["lon"])
            lat = float(loc["lat"])
            parts.append(f"{lon},{lat}")
        return ";".join(parts)
    
    def table(
            self,
            locations: List[Dict[str, float]],
            annotations: Literal["distance", "duration"] = "distance",
            sources: Optional[List[int]] = None,
            destinations: Optional[List[int]] = None,
            fallback_coordinate: Literal["input", "snapped"] = "input",
            profile: Optional[str] = None,
            clip_negative: bool = True,
        ) -> Dict:
        """
        Calls OSRM /table/v1/<profile>/
        Docs: https://project-osrm.org/docs/v5.24.0/api/#table-service
        """
        base_url = self._resolve_base_url(profile)
        profile = self._resolve_path_profile(profile)
        coord_string = self._format_coordinates(locations)
        url = f"{base_url}/table/v1/{profile}/{coord_string}"
        params = {
            "annotations": annotations,
            "fallback_coordinate": fallback_coordinate,
        }
        if sources is not None:
            params["sources"] = ";".join(map(str, sources))
        if destinations is not None:
            params["destinations"] = ";".join(map(str, destinations))
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if clip_negative:
            key = "distances" if annotations == "distance" else "durations"
            matrix = data.get(key)
            if matrix is not None:
                for i, row in enumerate(matrix):
                    for j, val in enumerate(row):
                        if val is not None and val < 0:
                            matrix[i][j] = 0.0
        return data

    def table_chunked(
        self,
        locations: List[Dict[str, float]],
        chunk_size: int = 75,
        profile: Optional[str] = None,
        annotations: Literal["distance", "duration"] = "distance",
        clip_negative: bool = True,
        ) -> np.ndarray:
        n = len(locations)
        chunks = math.ceil(n / chunk_size)
        M = np.zeros((n, n))
        ranges = []
        for c in range(chunks):
            start = c * chunk_size
            end = min((c + 1) * chunk_size, n)
            ranges.append((start, end))
        key = "distances" if annotations == "distance" else "durations"
        for _, (s_i, e_i) in tqdm(
            enumerate(ranges),
            desc="OSRM Table Chunks",
            total=len(ranges),
            leave=False,
        ):
            loc_i = locations[s_i:e_i]
            for _, (s_j, e_j) in tqdm(
                enumerate(ranges),
                desc="  Inner chunks",
                total=len(ranges),
                leave=False,
            ):
                loc_j = locations[s_j:e_j]
                coords = loc_i + loc_j
                n_i = len(loc_i)
                n_j = len(loc_j)
                sources = list(range(n_i))
                destinations = list(range(n_i, n_i + n_j))
                result = self.table(
                    coords,
                    profile=profile,
                    annotations=annotations,
                    sources=sources,
                    destinations=destinations,
                    clip_negative=clip_negative,
                )
                block = np.array(result[key])
                M[s_i:e_i, s_j:e_j] = block
        return M

    def table_between_chunked(
        self,
        sources: Sequence[Dict[str, float]],
        targets: Sequence[Dict[str, float]],
        chunk_size: int = 75,
        profile: Optional[str] = None,
        annotations: Literal["distance", "duration"] = "distance",
        clip_negative: bool = True,
        max_coordinates_per_request: int = 100,
    ) -> np.ndarray:
        """Return a chunked source-by-target OSRM table."""
        if chunk_size < 1:
            raise ValueError("chunk_size must be a positive integer.")
        if max_coordinates_per_request < 2:
            raise ValueError("max_coordinates_per_request must be at least 2.")

        effective_chunk_size = min(chunk_size, max_coordinates_per_request // 2)
        result_matrix = np.full((len(sources), len(targets)), np.nan)
        key = "distances" if annotations == "distance" else "durations"

        for source_start in range(0, len(sources), effective_chunk_size):
            source_end = min(source_start + effective_chunk_size, len(sources))
            source_chunk = list(sources[source_start:source_end])
            for target_start in range(0, len(targets), effective_chunk_size):
                target_end = min(target_start + effective_chunk_size, len(targets))
                target_chunk = list(targets[target_start:target_end])
                locations = source_chunk + target_chunk
                source_indices = list(range(len(source_chunk)))
                destination_indices = list(
                    range(len(source_chunk), len(locations))
                )
                response = self.table(
                    locations,
                    profile=profile,
                    annotations=annotations,
                    sources=source_indices,
                    destinations=destination_indices,
                    clip_negative=clip_negative,
                )
                block = np.asarray(response[key], dtype=float)
                result_matrix[source_start:source_end, target_start:target_end] = block

        return result_matrix

    def route(
            self,
            locations: List[Dict[str, float]],
            overview: Literal["false", "simplified", "full"] = "simplified",
            steps: bool = False,
            annotations: Optional[Literal["distance", "duration", "nodes", "weight", "datasources"]] = None,
            geometries: Literal["polyline", "polyline6", "geojson"] = "polyline",
            alternatives: bool = False,
            continue_straight: Optional[bool] = None,
            profile: Optional[str] = None,
        ):
        """
        Calls OSRM /route/v1/<profile>/
        Docs: https://project-osrm.org/docs/v5.24.0/api/#route-service
        """
        base_url = self._resolve_base_url(profile)
        profile = self._resolve_path_profile(profile)
        coord_string = self._format_coordinates(locations)
        url = f"{base_url}/route/v1/{profile}/{coord_string}"
        params = {
            "overview": overview,
            "steps": "true" if steps else "false",
            "alternatives": "true" if alternatives else "false",
            "geometries": geometries,
            "annotations": annotations if annotations else "false",
            "continue_straight": "true" if continue_straight else "false"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    


