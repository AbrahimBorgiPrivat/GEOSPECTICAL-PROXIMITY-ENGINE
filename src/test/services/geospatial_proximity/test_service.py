import importlib

import numpy as np
from fastapi.testclient import TestClient


service = importlib.import_module("services.geospatial-proximity.main")
client = TestClient(service.app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_proximity_endpoint_serializes_algorithm_result(monkeypatch):
    captured = {}

    def fake_run_proximity(**kwargs):
        captured.update(kwargs)
        return (
            np.array([[75.0, np.nan]]),
            [{"source_index": 0, "target_index": 0, "dist": 75.0}],
            {"number_of_sources": 1, "number_of_targets": 1},
        )

    monkeypatch.setattr(service, "run_proximity", fake_run_proximity)

    response = client.post(
        "/proximity",
        json={
            "sources": [{"lon": 12.0, "lat": 55.0}],
            "targets": [{"lon": 12.001, "lat": 55.0, "weight": 6}],
            "radius": 500,
            "profile": "foot",
            "osrm_url": "http://osrm.test",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "distance_matrix": [[75.0, None]],
        "relations": [{"source_index": 0, "target_index": 0, "dist": 75.0}],
        "summary": {"number_of_sources": 1, "number_of_targets": 1},
    }
    assert captured["radius"] == 500
    assert captured["profile"] == "foot"
    assert captured["sources"] == [{"lon": 12.0, "lat": 55.0}]


def test_proximity_endpoint_rejects_invalid_coordinates(monkeypatch):
    called = False

    def fake_run_proximity(**kwargs):
        nonlocal called
        called = True
        return (), (), ()

    monkeypatch.setattr(service, "run_proximity", fake_run_proximity)

    response = client.post(
        "/proximity",
        json={
            "sources": [{"lon": 181, "lat": 55}],
            "targets": [{"lon": 12, "lat": 55, "weight": 1}],
            "radius": 500,
        },
    )

    assert response.status_code == 422
    assert called is False


def test_proximity_endpoint_can_include_candidate_distances(monkeypatch):
    def fake_run_proximity(**kwargs):
        assert kwargs["include_candidate_distances"] is True
        return (
            np.array([[42.0]]),
            [],
            {},
            [(0, 0, 30.0)],
            {(0, 0): 42.0},
        )

    monkeypatch.setattr(service, "run_proximity", fake_run_proximity)

    response = client.post(
        "/proximity",
        json={
            "sources": [{"lon": 12, "lat": 55}],
            "targets": [{"lon": 12, "lat": 55, "weight": 1}],
            "radius": 100,
            "include_candidate_distances": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["candidates"] == [
        {"source_index": 0, "target_index": 0, "geodist": 30.0}
    ]
    assert response.json()["osrm_distances"] == [
        {"source_index": 0, "target_index": 0, "distance": 42.0}
    ]
