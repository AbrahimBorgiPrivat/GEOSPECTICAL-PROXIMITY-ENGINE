import numpy as np
import requests

from libraries.classes.osrm_api import OSRMClient


LOCATIONS = [
    {"lon": 12.5683, "lat": 55.6761},
    {"lon": 12.5800, "lat": 55.6800},
]


class DummyResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"distances": [[0.0, 10.0], [11.0, 0.0]]}


class NegativeDistanceResponse(DummyResponse):
    def json(self):
        return {"distances": [[0.0, -10.0]]}


def test_table_builds_source_target_request_and_returns_matrix(monkeypatch):
    calls = []

    def fake_get(url, params=None):
        calls.append((url, params))
        return DummyResponse()

    monkeypatch.setattr(requests, "get", fake_get)
    client = OSRMClient(base_url="http://osrm.example/", profile="foot")

    result = client.table(LOCATIONS, sources=[0], destinations=[1])

    assert np.array_equal(result["distances"], [[0.0, 10.0], [11.0, 0.0]])
    assert calls[0][0].startswith("http://osrm.example/table/v1/foot/")
    assert calls[0][1]["sources"] == "0"
    assert calls[0][1]["destinations"] == "1"


def test_table_clips_negative_distances(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda *args, **kwargs: NegativeDistanceResponse(),
    )
    client = OSRMClient(base_url="http://osrm.example", profile="foot")

    result = client.table(LOCATIONS)

    assert result["distances"] == [[0.0, 0.0]]
