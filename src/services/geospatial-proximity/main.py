"""Expose the proximity algorithm as a small JSON HTTP API."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Mapping, Optional

import numpy as np
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from libraries.algoritm.algoritm import run_proximity
from libraries.classes.osrm_api import OSRMClient


class Location(BaseModel):
    """A geographic location accepted by the API."""

    lon: float = Field(ge=-180, le=180)
    lat: float = Field(ge=-90, le=90)


class Target(Location):
    """A location with the weight used in the aggregate result."""

    weight: float = Field(ge=0)


class ProximityRequest(BaseModel):
    """Input contract for one proximity calculation."""

    sources: List[Location]
    targets: List[Target]
    radius: float = Field(ge=0)
    profile: str = "foot"
    distance_unit: Literal["metres", "duration", "seconds"] = "metres"
    radius_unit: Optional[Literal["metres", "duration", "seconds"]] = None
    speed_mps: Optional[float] = Field(default=None, gt=0)
    include_candidate_distances: bool = False
    osrm_url: Optional[str] = None


app = FastAPI(
    title="Geospatial Proximity Engine",
    version="1.0.0",
    description="Runs the proximity algorithm through an HTTP API.",
)


def _json_safe(value: Any) -> Any:
    """Convert NumPy values and non-finite floats to JSON-compatible values."""
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Support both Pydantic 1 and Pydantic 2 model APIs."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _serialize_result(result: tuple[Any, ...]) -> Dict[str, Any]:
    """Serialize the tuple returned by ``run_proximity``."""
    distance_matrix, relations, summary, *optional = result
    response: Dict[str, Any] = {
        "distance_matrix": _json_safe(distance_matrix),
        "relations": _json_safe(relations),
        "summary": _json_safe(summary),
    }

    if optional:
        candidates, osrm_distances = optional
        response["candidates"] = [
            {
                "source_index": int(source_index),
                "target_index": int(target_index),
                "geodist": float(geodist),
            }
            for source_index, target_index, geodist in candidates
        ]
        response["osrm_distances"] = [
            {
                "source_index": int(source_index),
                "target_index": int(target_index),
                "distance": float(distance),
            }
            for (source_index, target_index), distance in osrm_distances.items()
        ]
    return response


@app.get("/health")
def health() -> Dict[str, str]:
    """Return a simple liveness response."""
    return {"status": "ok"}


@app.post("/proximity")
def proximity(request: ProximityRequest) -> Dict[str, Any]:
    """Run the proximity algorithm and return its JSON result."""
    try:
        client = OSRMClient(
            base_url=request.osrm_url or "local",
            profile=request.profile,
        )
        result = run_proximity(
            sources=[_model_to_dict(location) for location in request.sources],
            targets=[_model_to_dict(location) for location in request.targets],
            radius=request.radius,
            osrm_client=client,
            profile=request.profile,
            include_candidate_distances=request.include_candidate_distances,
            distance_unit=request.distance_unit,
            radius_unit=request.radius_unit,
            speed_mps=request.speed_mps,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except requests.RequestException as error:
        raise HTTPException(status_code=502, detail="OSRM request failed.") from error

    return _serialize_result(result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
